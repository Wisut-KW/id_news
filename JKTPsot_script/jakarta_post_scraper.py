#!/usr/bin/env python3
"""
Jakarta Post News Scraper

Scrapes news articles from The Jakarta Post business companies section.
Default date range: last 2 days (configurable)
Appends new articles to JSON file, avoiding duplicates.
"""

import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

# Configuration
BASE_URL = "https://www.thejakartapost.com/business/companies/latest"
OUTPUT_FILE = "news_data.json"
DEFAULT_DAYS = 2
REQUEST_TIMEOUT = 30
MAX_PAGES = 50

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scraper.log')
    ]
)
logger = logging.getLogger(__name__)


class JakartaPostScraper:
    """Scraper for The Jakarta Post news articles."""
    
    def __init__(self, days_back=DEFAULT_DAYS, output_file=OUTPUT_FILE):
        self.days_back = days_back
        self.output_file = output_file
        self.cutoff_date = datetime.now() - timedelta(days=days_back)
        self.existing_urls = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self._load_existing_data()
    
    def _load_existing_data(self):
        """Load existing URLs from output file to avoid duplicates."""
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if 'url' in item:
                                self.existing_urls.add(item['url'])
                logger.info(f"Loaded {len(self.existing_urls)} existing URLs from {self.output_file}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load existing data: {e}")
    
    def _save_data(self, articles):
        """Append new articles to JSON file."""
        if not articles:
            logger.info("No new articles to save")
            return
        
        existing_data = []
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        existing_data = []
            except (json.JSONDecodeError, IOError):
                existing_data = []
        
        existing_data.extend(articles)
        
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(articles)} new articles to {self.output_file}")
        except IOError as e:
            logger.error(f"Failed to save data: {e}")
    
    def _extract_date_from_url(self, url):
        """Extract date from URL pattern like /2026/02/18/article-name.html"""
        try:
            pattern = r'/(\d{4})/(\d{2})/(\d{2})/'
            match = re.search(pattern, url)
            if match:
                year, month, day = match.groups()
                return datetime(int(year), int(month), int(day))
        except (ValueError, AttributeError):
            pass
        return None
    
    def _is_valid_article(self, title, url):
        """Check if this is a valid article (not navigation, login, etc.)"""
        if not title or not url:
            return False
        
        # Skip common non-article URLs
        skip_patterns = [
            '/user/account/login',
            '/multimedia',
            '/epost',
            'windows.microsoft.com',
            '/skin/',
            '.png',
            '.jpg',
            '.gif',
            'page=',
        ]
        
        url_lower = url.lower()
        for pattern in skip_patterns:
            if pattern in url_lower:
                return False
        
        # Check if URL contains date pattern (Jakarta Post articles have dates in URL)
        if not re.search(r'/\d{4}/\d{2}/\d{2}/', url):
            return False
        
        # Must have a substantial title (more than 5 chars)
        if len(title.strip()) < 5:
            return False
        
        return True
    
    def _is_in_most_viewed_section(self, element):
        """Check if element is in the 'most viewed' sidebar section"""
        parent = element
        max_depth = 5
        depth = 0
        
        while parent and depth < max_depth:
            class_attr = parent.get('class')
            if class_attr:
                class_str = ' '.join(class_attr).lower()
                # Skip if in most viewed, popular, or similar sidebars
                if any(x in class_str for x in ['mostviewed', 'most-viewed', 'popular', 'jpmvcontainer', 'listarticlegrid']):
                    return True
            parent = parent.find_parent()
            depth += 1
        
        return False
    
    def _fetch_page(self, page_num):
        """Fetch and parse a single page."""
        if page_num == 1:
            url = f"{BASE_URL}?utm_source=(direct)&utm_medium=channel_companies"
        else:
            url = f"{BASE_URL}?page={page_num}&utm_source=(direct)&utm_medium=channel_companies"
        
        try:
            logger.info(f"Fetching page {page_num}: {url}")
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = []
            processed_urls = set()
            
            # Find all links with href containing a date pattern
            all_links = soup.find_all('a', href=re.compile(r'/\d{4}/\d{2}/\d{2}/'))
            
            for link in all_links:
                href = link.get('href')
                if not href:
                    continue
                
                # Skip if in most viewed section
                if self._is_in_most_viewed_section(link):
                    continue
                
                # Make absolute URL
                if href.startswith('//'):
                    url = 'https:' + href
                elif href.startswith('/'):
                    url = 'https://www.thejakartapost.com' + href
                elif href.startswith('http'):
                    url = href
                else:
                    continue
                
                # Clean URL - remove utm parameters for deduplication
                clean_url = url.split('?')[0]
                
                # Skip if already exists or already processed
                if clean_url in self.existing_urls or clean_url in processed_urls:
                    continue
                
                # Get title
                title = link.get_text(strip=True)
                
                # Check if valid article
                if not self._is_valid_article(title, url):
                    continue
                
                # Mark as processed
                processed_urls.add(clean_url)
                
                # Extract date from URL
                article_date = self._extract_date_from_url(url)
                
                # Check date cutoff
                if article_date and article_date < self.cutoff_date:
                    continue
                
                # Find parent for summary and image
                parent = link.find_parent(['div', 'article', 'li'])
                summary = ''
                image_url = ''
                
                if parent:
                    # Look for summary paragraph
                    p_elem = parent.find('p')
                    if p_elem:
                        summary = p_elem.get_text(strip=True)
                    
                    # Look for image
                    img = parent.find('img')
                    if img:
                        image_url = img.get('src') or img.get('data-src') or ''
                        if image_url.startswith('//'):
                            image_url = 'https:' + image_url
                        elif image_url.startswith('/'):
                            image_url = 'https://www.thejakartapost.com' + image_url
                
                # Format date string
                date_str = article_date.strftime('%Y-%m-%d') if article_date else ''
                
                article_data = {
                    'title': title,
                    'url': clean_url,
                    'date': date_str,
                    'date_obj': article_date.isoformat() if article_date else None,
                    'summary': summary,
                    'image_url': image_url,
                    'scraped_at': datetime.now().isoformat()
                }
                
                articles.append(article_data)
            
            logger.info(f"Found {len(articles)} valid articles on page {page_num}")
            return articles
            
        except requests.RequestException as e:
            logger.error(f"Request error on page {page_num}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error on page {page_num}: {e}")
            return []
    
    def scrape(self):
        """Main scraping method with pagination."""
        logger.info(f"Starting scraper with {self.days_back} days back (cutoff: {self.cutoff_date.date()})")
        
        all_articles = []
        page_num = 1
        consecutive_empty = 0
        old_articles_count = 0
        
        while page_num <= MAX_PAGES and consecutive_empty < 3 and old_articles_count < 10:
            articles = self._fetch_page(page_num)
            
            if not articles:
                consecutive_empty += 1
                logger.info(f"No articles on page {page_num}, consecutive empty: {consecutive_empty}")
                if consecutive_empty >= 3:
                    logger.info("3 consecutive empty pages, stopping")
                    break
            else:
                consecutive_empty = 0
                
                # Count old articles on this page
                page_old_count = 0
                for article in articles:
                    if article.get('date_obj'):
                        article_date = datetime.fromisoformat(article['date_obj'])
                        if article_date < self.cutoff_date:
                            page_old_count += 1
                
                # Filter out old articles
                new_articles = []
                for article in articles:
                    if article.get('date_obj'):
                        article_date = datetime.fromisoformat(article['date_obj'])
                        if article_date >= self.cutoff_date:
                            new_articles.append(article)
                    else:
                        new_articles.append(article)
                
                old_articles_count += page_old_count
                all_articles.extend(new_articles)
                
                # Stop if we've seen too many old articles
                if old_articles_count >= 10:
                    logger.info(f"Found {old_articles_count} old articles, stopping pagination")
                    break
            
            page_num += 1
        
        # Remove duplicates (shouldn't happen with processed_urls, but just in case)
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_articles.append(article)
        
        logger.info(f"Total new unique articles found: {len(unique_articles)}")
        
        # Save to file
        self._save_data(unique_articles)
        
        return unique_articles


def main():
    """Main entry point with CLI argument support."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Scrape news articles from The Jakarta Post'
    )
    parser.add_argument(
        '--days', '-d',
        type=int,
        default=DEFAULT_DAYS,
        help=f'Number of days back to scrape (default: {DEFAULT_DAYS})'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=OUTPUT_FILE,
        help=f'Output JSON file (default: {OUTPUT_FILE})'
    )
    
    args = parser.parse_args()
    
    scraper = JakartaPostScraper(days_back=args.days, output_file=args.output)
    articles = scraper.scrape()
    
    print(f"\n{'='*60}")
    print(f"Scraping completed!")
    print(f"Articles found: {len(articles)}")
    print(f"Output file: {args.output}")
    print(f"{'='*60}\n")
    
    return 0 if articles else 1


if __name__ == '__main__':
    sys.exit(main())
