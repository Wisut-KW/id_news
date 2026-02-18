#!/usr/bin/env python3
"""
Jakarta Post Business News Scraper
Scrapes news articles from The Jakarta Post business section.
"""

import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scraper.log')
    ]
)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.thejakartapost.com/business/latest"
OUTPUT_FILE = "news_data.json"


class JakartaPostScraper:
    def __init__(
        self,
        days_back: int = 2,
        output_file: str = OUTPUT_FILE,
        base_url: str = BASE_URL
    ):
        self.days_back = days_back
        self.output_file = output_file
        self.base_url = base_url
        self.cutoff_date = datetime.now() - timedelta(days=days_back)
        self.existing_urls = self._load_existing_urls()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
        })
        # Pattern to match article URLs with dates like /business/2026/02/18/slug.html
        self.article_url_pattern = re.compile(r'/business/\d{4}/\d{2}/\d{2}/')

    def _load_existing_urls(self) -> set:
        if not os.path.exists(self.output_file):
            return set()
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {item['url'] for item in data if 'url' in item}
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Error loading existing data: {e}")
            return set()

    def _load_existing_data(self) -> list:
        if not os.path.exists(self.output_file):
            return []
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Could not parse existing JSON, starting fresh")
            return []

    def _save_data(self, data: list):
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Saved {len(data)} articles to {self.output_file}")

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        date_formats = [
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%d %H:%M:%S',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y',
            '%Y-%m-%d',
        ]
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        logger.debug(f"Could not parse date: {date_str}")
        return None

    def _extract_date_from_url(self, url: str) -> Optional[datetime]:
        """Extract date from URL like /business/2026/02/18/article.html"""
        match = re.search(r'/business/(\d{4})/(\d{2})/(\d{2})/', url)
        if match:
            year, month, day = match.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except ValueError:
                return None
        return None

    def _fetch_page(self, page_num: int) -> Optional[BeautifulSoup]:
        url = f"{self.base_url}?page={page_num}"
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            # Debug: Check if we got article containers
            list_news_count = len(soup.find_all('div', class_='listNews'))
            logger.debug(f"Page {page_num}: Found {list_news_count} listNews containers, {len(response.text)} bytes")
            return soup
        except requests.RequestException as e:
            logger.error(f"Error fetching page {page_num}: {e}")
            return None

    def _extract_article_data(self, article_elem, skip_existing: bool = True) -> Optional[dict]:
        """Extract article data from element.
        
        Args:
            article_elem: BeautifulSoup element containing article
            skip_existing: If True, return None for existing URLs. If False, still extract.
        """
        try:
            # Find the link to the article
            link_elem = article_elem.find('a', href=True)
            if not link_elem:
                return None
            
            url = urljoin("https://www.thejakartapost.com", link_elem['href'])
            
            # Only process actual article URLs with date pattern
            if not self.article_url_pattern.search(url):
                return None
            
            # Check if already exists
            is_existing = url in self.existing_urls
            if is_existing and skip_existing:
                logger.debug(f"Skipping existing URL: {url}")
                return None
            
            # Extract title - look for h2.titleNews first (specific to Jakarta Post)
            title_elem = article_elem.find('h2', class_='titleNews')
            if not title_elem:
                # Fallback: look for h2 or h3 with link text
                title_elem = article_elem.find(['h2', 'h3', 'h1'])
            if not title_elem:
                title_elem = link_elem
            
            title = title_elem.get_text(strip=True) if title_elem else "No title"
            
            # Extract date - try to get from URL first (most reliable)
            article_date = self._extract_date_from_url(url)
            date_str = None
            
            # Also try to get date from element
            date_elem = article_elem.find('span', class_='date')
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                parsed_date = self._parse_date(date_text)
                if parsed_date:
                    article_date = parsed_date
                    date_str = date_text
            
            # Extract summary
            summary_elem = article_elem.find('p')
            summary = summary_elem.get_text(strip=True) if summary_elem else ""
            
            return {
                'title': title,
                'url': url,
                'date': article_date.isoformat() if article_date else date_str,
                'date_parsed': article_date,
                'summary': summary,
                'is_existing': is_existing,
                'scraped_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error extracting article data: {e}")
            return None

    def _should_stop_pagination(self, all_articles: list, page_num: int) -> bool:
        """Check if pagination should stop based on article dates.
        
        Args:
            all_articles: List of all articles found (including duplicates)
            page_num: Current page number
        """
        if not all_articles:
            logger.info(f"No articles found on page {page_num}, stopping")
            return True
        
        # Check if all articles are older than cutoff
        dated_articles = [a for a in all_articles if a.get('date_parsed')]
        
        if dated_articles and all(a['date_parsed'] < self.cutoff_date for a in dated_articles):
            logger.info(f"All articles on page {page_num} are older than cutoff, stopping pagination")
            return True
        
        return False

    def _find_articles_on_page(self, soup: BeautifulSoup) -> tuple:
        """Find article elements using Jakarta Post specific selectors.
        
        Returns:
            tuple: (all_articles, new_articles) where all_articles includes duplicates
        """
        all_articles = []
        new_articles = []
        processed_urls = set()
        
        # Method 1: Look for .listNews containers (main article containers on Jakarta Post)
        list_news = soup.find_all('div', class_='listNews')
        logger.debug(f"Found {len(list_news)} .listNews elements")
        
        for elem in list_news:
            # First extract without skipping to get date info for pagination
            article_data = self._extract_article_data(elem, skip_existing=False)
            if article_data and article_data['url'] not in processed_urls:
                all_articles.append(article_data)
                processed_urls.add(article_data['url'])
                # Only add to new_articles if not existing
                if not article_data['is_existing']:
                    new_articles.append(article_data)
        
        # Method 2: Look for all article links with date patterns
        if not all_articles:
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = str(link.get('href', ''))
                if self.article_url_pattern.search(href):
                    # Get the parent container
                    parent = link.find_parent(['div', 'article', 'li', 'section'])
                    if parent:
                        article_data = self._extract_article_data(parent, skip_existing=False)
                        if article_data and article_data['url'] not in processed_urls:
                            all_articles.append(article_data)
                            processed_urls.add(article_data['url'])
                            if not article_data['is_existing']:
                                new_articles.append(article_data)
        
        return all_articles, new_articles

    def scrape(self):
        logger.info(f"Starting scrape with {self.days_back} days back (cutoff: {self.cutoff_date.date()})")
        all_articles = self._load_existing_data()
        new_articles = []
        page_num = 1
        stop_pagination = False
        
        while not stop_pagination:
            logger.info(f"Fetching page {page_num}...")
            soup = self._fetch_page(page_num)
            if not soup:
                logger.error(f"Failed to fetch page {page_num}")
                break
            
            page_all_articles, page_new_articles = self._find_articles_on_page(soup)
            
            logger.info(f"Found {len(page_all_articles)} total articles ({len(page_new_articles)} new) on page {page_num}")
            
            for article in page_new_articles:
                new_articles.append(article)
                self.existing_urls.add(article['url'])
            
            if self._should_stop_pagination(page_all_articles, page_num):
                stop_pagination = True
            
            page_num += 1
            if page_num > 100:
                logger.warning("Reached maximum page limit (100), stopping")
                break
        
        if new_articles:
            all_articles.extend(new_articles)
            self._save_data(all_articles)
            logger.info(f"Added {len(new_articles)} new articles")
        else:
            logger.info("No new articles found")
        
        return new_articles


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Scrape The Jakarta Post business news'
    )
    parser.add_argument(
        '--days', '-d',
        type=int,
        default=2,
        help='Number of days back to scrape (default: 2)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=OUTPUT_FILE,
        help=f'Output JSON file (default: {OUTPUT_FILE})'
    )
    parser.add_argument(
        '--url',
        type=str,
        default=BASE_URL,
        help=f'Base URL to scrape (default: {BASE_URL})'
    )
    args = parser.parse_args()
    
    scraper = JakartaPostScraper(
        days_back=args.days,
        output_file=args.output,
        base_url=args.url
    )
    
    try:
        new_articles = scraper.scrape()
        print(f"\nScraping complete! Added {len(new_articles)} new articles.")
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
