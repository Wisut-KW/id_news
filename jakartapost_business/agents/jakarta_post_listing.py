"""
Jakarta Post Business Listing Scraper Agent
Scrapes news listings from Jakarta Post business categories with pagination
"""

import time
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Tuple
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

from .config import Config


class JakartaPostListingAgent:
    """Agent to scrape news listings from Jakarta Post business categories"""
    
    def __init__(self, delay_min: int = None, delay_max: int = None, max_retries: int = None):
        self.delay_min = delay_min or Config.REQUEST_DELAY_MIN
        self.delay_max = delay_max or Config.REQUEST_DELAY_MAX
        self.max_retries = max_retries or Config.MAX_RETRIES
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
    
    def fetch_all_categories(self, start_date: datetime, end_date: datetime, max_pages: int = None) -> List[Dict]:
        """
        Fetch articles from all business categories with pagination
        
        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            max_pages: Maximum pages per category (default: Config.MAX_PAGES)
            
        Returns:
            List of article metadata
        """
        if max_pages is None:
            max_pages = Config.MAX_PAGES
            
        all_articles = []
        
        for category_name, category_url in Config.CATEGORIES.items():
            print(f"\n  Scraping category: {category_name.upper()}")
            articles = self._fetch_category_with_pagination(
                category_name, category_url, start_date, end_date, max_pages
            )
            all_articles.extend(articles)
        
        # Remove duplicates
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                unique_articles.append(article)
        
        return unique_articles
    
    def _fetch_category_with_pagination(self, category_name: str, base_url: str, 
                                       start_date: datetime, end_date: datetime, 
                                       max_pages: int) -> List[Dict]:
        """
        Fetch articles from a single category with pagination
        
        Args:
            category_name: Name of the category
            base_url: Base URL for the category
            start_date: Start date for filtering
            end_date: End date for filtering
            max_pages: Maximum number of pages to fetch
            
        Returns:
            List of article metadata
        """
        all_articles = []
        page = 1
        
        while page <= max_pages:
            print(f"    Page {page}...", end=" ")
            
            # Build page URL
            page_url = self._build_page_url(base_url, page)
            
            # Fetch page
            articles = self._fetch_page(page_url, category_name)
            
            if not articles:
                print("No articles found")
                break
            
            # Check if we should stop (oldest article < start_date)
            stop_pagination = True
            valid_articles = []
            
            for article in articles:
                article_date = article.get("published_date", "")
                
                if article_date:
                    try:
                        article_date_obj = datetime.strptime(article_date, "%Y-%m-%d")
                        
                        # Check if article is within date range
                        if start_date <= article_date_obj <= end_date:
                            valid_articles.append(article)
                        
                        # If article is >= start_date, continue pagination
                        if article_date_obj >= start_date:
                            stop_pagination = False
                    except ValueError:
                        # If date parsing fails, include article
                        valid_articles.append(article)
                        stop_pagination = False
                else:
                    # No date, include and continue
                    valid_articles.append(article)
                    stop_pagination = False
            
            all_articles.extend(valid_articles)
            print(f"{len(valid_articles)} articles")
            
            # Check if we should stop pagination
            if stop_pagination:
                print(f"    → Oldest article outside date range, stopping")
                break
            
            # Delay between requests
            time.sleep(random.uniform(self.delay_min, self.delay_max))
            page += 1
        
        return all_articles
    
    def _build_page_url(self, base_url: str, page: int) -> str:
        """Build URL for a specific page"""
        if page == 1:
            return base_url
        
        # Parse URL and add page parameter
        parsed = urlparse(base_url)
        query_params = parse_qs(parsed.query)
        query_params['page'] = [str(page)]
        new_query = urlencode(query_params, doseq=True)
        
        return urlunparse(parsed._replace(query=new_query))
    
    def _fetch_page(self, url: str, category: str) -> List[Dict]:
        """Fetch and parse a single page"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, "lxml")
                articles = self._parse_listing(soup, category)
                
                return articles
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return []
                time.sleep(random.uniform(self.delay_min, self.delay_max) * (attempt + 1))
        
        return []
    
    def _parse_listing(self, soup: BeautifulSoup, category: str) -> List[Dict]:
        """Parse article listings from page"""
        articles = []
        
        # Jakarta Post article selectors
        article_selectors = [
            ".article-list article",
            ".news-list article",
            ".post-list article",
            ".content article",
            "article.post",
            "article.news",
            ".category article",
        ]
        
        article_elements = []
        for selector in article_selectors:
            elements = soup.select(selector)
            if elements:
                article_elements = elements
                break
        
        # Fallback: look for article links
        if not article_elements:
            links = soup.find_all("a", href=True)
            for link in links:
                href = link.get("href", "")
                if "/business/" in href and ("/" in href or "/" in href):
                    article_elements.append(link)
        
        for element in article_elements:
            article = self._extract_article_info(element, category)
            if article["url"]:
                articles.append(article)
        
        return articles
    
    def _extract_article_info(self, element, category: str) -> Dict:
        """Extract article info from listing element"""
        article = {
            "title": "",
            "url": "",
            "published_date": "",
            "summary": "",
            "category": category,
            "author": "",
        }
        
        # Extract URL
        link = element.find("a", href=True)
        if link:
            href = link.get("href", "")
            article["url"] = self._clean_url(urljoin(Config.BASE_URL, href))
        elif element.name == "a" and element.get("href"):
            article["url"] = self._clean_url(urljoin(Config.BASE_URL, element.get("href")))
        
        # Extract title
        title_selectors = ["h1", "h2", "h3", ".title", "[class*='title']", ".headline"]
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                article["title"] = title_elem.get_text(strip=True)
                break
        
        if not article["title"] and link:
            article["title"] = link.get_text(strip=True)
        
        # Extract date
        date_elem = element.find("time") or element.select_one("[class*='date']") or element.select_one("[class*='time']")
        if date_elem:
            date_text = date_elem.get_text(strip=True)
            article["published_date"] = self._parse_date(date_text)
        
        # Extract author if available
        author_elem = element.select_one("[class*='author']") or element.select_one("[rel='author']")
        if author_elem:
            article["author"] = author_elem.get_text(strip=True)
        
        return article
    
    def _clean_url(self, url: str) -> str:
        """Remove tracking parameters from URL"""
        parsed = urlparse(url)
        # Remove common tracking parameters
        query_params = parse_qs(parsed.query)
        tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']
        for param in tracking_params:
            query_params.pop(param, None)
        
        new_query = urlencode(query_params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))
    
    def _parse_date(self, date_str: str) -> str:
        """Parse date string to YYYY-MM-DD format"""
        if not date_str:
            return ""
        
        # Common formats
        formats = [
            "%B %d, %Y",      # February 17, 2026
            "%b %d, %Y",      # Feb 17, 2026
            "%Y-%m-%d",       # 2026-02-17
            "%d %B %Y",       # 17 February 2026
            "%d %b %Y",       # 17 Feb 2026
            "%d/%m/%Y",       # 17/02/2026
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str.strip(), fmt)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        return ""
