"""
IDX Channel Listing Scraper Agent
Scrapes news from IDX Channel index page with date filtering
"""

import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict
from urllib.parse import urljoin


class IDXChannelListingAgent:
    """Agent to scrape news listings from IDX Channel"""
    
    BASE_URL = "https://www.idxchannel.com"
    INDEX_URL = "https://www.idxchannel.com/indeks"
    
    def __init__(self, delay: float = 2.0, max_retries: int = 3):
        self.delay = delay
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def fetch_listings_by_date(self, date_str: str) -> List[Dict]:
        """
        Fetch article listings for a specific date using index page
        
        Args:
            date_str: Date in YYYY-MM-DD format
            
        Returns:
            List of article metadata
        """
        # Convert YYYY-MM-DD to DD/MM/YYYY format for the URL
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d/%m/%Y")
        
        url = f"{self.INDEX_URL}?date={formatted_date}&idkanal="
        print(f"    Fetching index page: {url}")
        
        articles = []
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, "lxml")
                articles = self._parse_index_page(soup, date_str)
                
                print(f"    Found {len(articles)} articles for {date_str}")
                time.sleep(self.delay)
                return articles
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(f"    ✗ Failed to fetch index page: {e}")
                    return []
                time.sleep(self.delay * (attempt + 1))
        
        return articles
    
    def fetch_listings_by_date_range(self, days: int = 3) -> List[Dict]:
        """
        Fetch article listings for the last N days using index pages
        
        Args:
            days: Number of days to look back (default: 3)
            
        Returns:
            List of article metadata with accurate dates
        """
        all_articles = []
        today = datetime.now()
        
        print(f"\n[Fetching index pages for last {days} days...]")
        
        for i in range(days):
            date_obj = today - timedelta(days=i)
            date_str = date_obj.strftime("%Y-%m-%d")
            
            print(f"\n  [{i+1}/{days}] Fetching articles for {date_str}...")
            articles = self.fetch_listings_by_date(date_str)
            
            # Ensure all articles have the correct date
            for article in articles:
                article["published_date"] = date_str
            
            all_articles.extend(articles)
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article["url"] and article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                unique_articles.append(article)
        
        print(f"\n  Total unique articles: {len(unique_articles)}")
        return unique_articles
    
    def _parse_index_page(self, soup: BeautifulSoup, date_str: str) -> List[Dict]:
        """
        Parse article listings from index page
        
        Args:
            soup: Parsed HTML
            date_str: Date string to assign to articles
            
        Returns:
            List of article metadata
        """
        articles = []
        
        # Try different selectors for article items on index page
        article_selectors = [
            ".indeks-list article",
            ".article-list article",
            ".news-list article",
            ".list-article article",
            ".content-list article",
            ".box-list article",
            "article",
        ]
        
        article_elements = []
        for selector in article_selectors:
            elements = soup.select(selector)
            if elements:
                article_elements = elements
                break
        
        # If no article containers found, look for links with article structure
        if not article_elements:
            links = soup.find_all("a", href=True)
            for link in links:
                href = link.get("href")
                if href and isinstance(href, str):
                    if "/read/" in href or "/news/" in href or "/article/" in href:
                        article_elements.append(link)
        
        for element in article_elements:
            article = self._extract_article_info(element)
            if article["url"]:
                article["published_date"] = date_str  # Ensure correct date
                articles.append(article)
        
        return articles
    
    def _extract_article_info(self, element) -> Dict:
        """
        Extract article info from a listing element
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            Article metadata dict
        """
        article = {
            "title": "",
            "url": "",
            "published_date": "",
            "summary": "",
            "category": "",
        }
        
        # Extract URL
        link = element.find("a", href=True)
        if link:
            href = link.get("href", "")
            article["url"] = urljoin(self.BASE_URL, href)
        elif element.name == "a" and element.get("href"):
            article["url"] = urljoin(self.BASE_URL, element.get("href"))
        
        # Extract title
        title_selectors = ["h1", "h2", "h3", ".title", "[class*='title']", ".judul"]
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                article["title"] = title_elem.get_text(strip=True)
                break
        
        # If no title found, use link text
        if not article["title"] and link:
            article["title"] = link.get_text(strip=True)
        
        # Extract summary
        summary_selectors = [
            ".summary", ".excerpt", ".description", 
            "[class*='summary']", "[class*='desc']",
            ".short-content", ".lead"
        ]
        for selector in summary_selectors:
            summary_elem = element.select_one(selector)
            if summary_elem:
                article["summary"] = summary_elem.get_text(strip=True)
                break
        
        # Extract category
        category_elem = element.select_one("[class*='category']") or element.select_one("[class*='tag']") or element.select_one("[class*='kanal']")
        if category_elem:
            article["category"] = category_elem.get_text(strip=True)
        
        return article
    
    def _parse_date(self, date_str: str) -> str:
        """
        Parse date string to YYYY-MM-DD format
        
        Args:
            date_str: Date string from webpage
            
        Returns:
            Date in YYYY-MM-DD format or empty string
        """
        if not date_str:
            return ""
        
        # Common date formats for Indonesian sites
        formats = [
            "%d %B %Y",           # 17 February 2026
            "%d %b %Y",           # 17 Feb 2026
            "%Y-%m-%d",           # 2026-02-17
            "%d/%m/%Y",           # 17/02/2026
            "%B %d, %Y",          # February 17, 2026
            "%b %d, %Y",          # Feb 17, 2026
        ]
        
        # Indonesian month names
        month_map = {
            "januari": "January", "februari": "February", "maret": "March",
            "april": "April", "mei": "May", "juni": "June",
            "juli": "July", "agustus": "August", "september": "September",
            "oktober": "October", "november": "November", "desember": "December"
        }
        
        # Normalize Indonesian months
        date_lower = date_str.lower()
        for id_month, en_month in month_map.items():
            if id_month in date_lower:
                date_str = date_lower.replace(id_month, en_month)
                break
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str.strip(), fmt)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        return ""
    
    def filter_today_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Filter articles to only include those from today
        
        Args:
            articles: List of article metadata
            
        Returns:
            Filtered list of today's articles
        """
        today = datetime.now().strftime("%Y-%m-%d")
        return [a for a in articles if a.get("published_date") == today]
    
    def filter_recent_articles(self, articles: List[Dict], days: int = 3) -> List[Dict]:
        """
        Filter articles to include those from the last N days
        
        Args:
            articles: List of article metadata
            days: Number of days to look back (default: 3)
            
        Returns:
            Filtered list of recent articles
        """
        today = datetime.now()
        cutoff_date = today - timedelta(days=days-1)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")
        
        recent_articles = []
        for article in articles:
            article_date = article.get("published_date", "")
            if article_date and article_date >= cutoff_str:
                recent_articles.append(article)
        
        return recent_articles
