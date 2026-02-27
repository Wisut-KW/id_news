#!/usr/bin/env python3
"""
Jakarta Globe News Scraper

A comprehensive Python-based news scraper that:
- Scrapes articles from Jakarta Globe (Indonesian news portal)
- Supports configurable date ranges (defaults to last 2 days)
- Automatically paginates through article listings
- Prevents duplicate entries by tracking URLs
- Extracts full article content from individual pages
- Translates articles from Indonesian to English and/or Thai
- Logs all operations and errors
- Appends new data to existing JSON files
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timedelta
from typing import Optional

import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator


# Configuration
DEFAULT_DAYS_BACK = 2
DEFAULT_OUTPUT_FILE = "news_data.json"
BASE_URL = "https://jakartaglobe.id/search/business/1"
MAX_PAGES = 100
REQUEST_DELAY = 0.5

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class JakartaGlobeScraper:
    """Main scraper class for Jakarta Globe news articles."""
    
    def __init__(
        self,
        days_back: int = DEFAULT_DAYS_BACK,
        output_file: str = DEFAULT_OUTPUT_FILE,
        url: str = BASE_URL,
        fetch_content: bool = False,
        translate: bool = False,
        translate_thai: bool = False,
        translated_output: Optional[str] = None,
        translated_thai_output: Optional[str] = None
    ):
        self.days_back = days_back
        self.output_file = output_file
        self.base_url = url
        self.fetch_content = fetch_content
        self.translate = translate
        self.translate_thai = translate_thai
        self.translated_output = translated_output or "news_data_translated_en.json"
        self.translated_thai_output = translated_thai_output or "news_data_translated_th.json"
        
        self.existing_urls = set()
        self.articles = []
        self.cutoff_date = datetime.now() - timedelta(days=self.days_back)
        
        # Initialize translators
        self.translator_en = None
        self.translator_th = None
        if self.translate:
            self.translator_en = GoogleTranslator(source='id', target='en')
        if self.translate_thai:
            self.translator_th = GoogleTranslator(source='id', target='th')
        
        logger.info(f"Initialized scraper with {days_back} days back")
        logger.info(f"Base URL: {url}")
        logger.info(f"Cutoff date: {self.cutoff_date}")
    
    def load_existing_data(self) -> None:
        """Load existing URLs from output file to prevent duplicates."""
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    for article in existing_data:
                        if 'url' in article:
                            self.existing_urls.add(article['url'])
                    logger.info(f"Loaded {len(self.existing_urls)} existing URLs")
            except Exception as e:
                logger.warning(f"Could not load existing data: {e}")
    
    def get_page_url(self, page: int) -> str:
        """Generate URL for specific page."""
        if page == 1:
            return self.base_url
        # Pagination pattern: /search/business/{page}
        return f"https://jakartaglobe.id/search/business/{page}"
    
    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def parse_listing_page(self, html: str) -> list:
        """Parse article listing page and extract article info."""
        articles = []
        soup = BeautifulSoup(html, 'lxml')
        
        # Find article elements - try multiple selectors
        article_elements = (
            soup.select('div.article-item') or
            soup.select('div.news-item') or
            soup.select('div.article-card') or
            soup.select('article') or
            soup.select('div.latest-news article') or
            soup.select('div.search-result article') or
            soup.select('div.news-list article') or
            []
        )
        
        if not article_elements:
            # Try finding links that look like articles
            article_elements = soup.select('a[href*="/read/"]')
        
        for elem in article_elements:
            try:
                article_data = self._extract_article_from_element(elem, soup)
                if article_data:
                    articles.append(article_data)
            except Exception as e:
                logger.warning(f"Error parsing article element: {e}")
                continue
        
        logger.info(f"Found {len(articles)} articles on page")
        return articles
    
    def _extract_article_from_element(self, elem, soup) -> Optional[dict]:
        """Extract article data from HTML element."""
        article_data = {}
        
        # Try to find title and URL
        if elem.name == 'a':
            # Element is a link
            article_data['url'] = elem.get('href', '')
            title_elem = elem.select_one('h2, h3, h4, .title, .article-title')
            if title_elem:
                article_data['title'] = title_elem.get_text(strip=True)
            else:
                article_data['title'] = elem.get_text(strip=True)
        else:
            # Element is a container - find link inside
            link_elem = elem.select_one('a[href*="/read/"]')
            if not link_elem:
                return None
            
            article_data['url'] = link_elem.get('href', '')
            
            # Extract title
            title_elem = (
                elem.select_one('h2, h3, h4, .title, .article-title, .news-title') or
                link_elem.select_one('h2, h3, h4, .title')
            )
            if title_elem:
                article_data['title'] = title_elem.get_text(strip=True)
            else:
                article_data['title'] = link_elem.get_text(strip=True)
        
        # Validate URL
        if not article_data.get('url') or '/read/' not in article_data['url']:
            return None
        
        # Make URL absolute
        if not article_data['url'].startswith('http'):
            article_data['url'] = 'https://jakartaglobe.id' + article_data['url']
        
        # Extract date from URL
        date_match = re.search(r'/read/(\d{4})(\d{2})(\d{2})/', article_data['url'])
        if date_match:
            year, month, day = date_match.groups()
            article_data['date'] = f"{year}-{month}-{day}T00:00:00"
            article_data['date_parsed'] = datetime(int(year), int(month), int(day))
        else:
            article_data['date'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            article_data['date_parsed'] = datetime.now()
        
        # Extract category
        category_elem = elem.select_one('.category, .category-tag, span.category')
        if category_elem:
            article_data['category'] = category_elem.get_text(strip=True)
        else:
            article_data['category'] = 'Business'
        
        # Check if URL already exists
        if article_data['url'] in self.existing_urls:
            article_data['is_existing'] = True
        else:
            article_data['is_existing'] = False
            self.existing_urls.add(article_data['url'])
        
        article_data['scraped_at'] = datetime.now().isoformat()
        
        return article_data
    
    def should_stop_pagination(self, articles: list) -> bool:
        """Check if we should stop pagination based on article dates."""
        if not articles:
            return True
        
        # Check if all articles are older than cutoff
        for article in articles:
            if 'date_parsed' in article and isinstance(article['date_parsed'], datetime):
                if article['date_parsed'] >= self.cutoff_date:
                    return False
        
        return True
    
    def fetch_article_content(self, url: str) -> dict:
        """Fetch full article content from individual article page."""
        content_data = {
            'content': '',
            'content_html': '',
            'author': '',
            'author_role': '',
            'published_time': '',
            'modified_time': '',
            'summary': '',
            'word_count': 0,
            'categories': [],
            'subcategory': '',
            'tags': [],
            'images': []
        }
        
        html = self.fetch_page(url)
        if not html:
            return content_data
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract content
        content_elem = (
            soup.select_one('div.article-content') or
            soup.select_one('div.content') or
            soup.select_one('div.article-body') or
            soup.select_one('div.post-content') or
            soup.select_one('article div.content') or
            soup.select_one('div.entry-content')
        )
        
        if content_elem:
            content_data['content_html'] = str(content_elem)
            # Get text from all paragraphs
            paragraphs = content_elem.select('p')
            content_data['content'] = '\n\n'.join(
                p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
            )
            # Summary is first paragraph
            if paragraphs and paragraphs[0].get_text(strip=True):
                content_data['summary'] = paragraphs[0].get_text(strip=True)
            # Word count
            content_data['word_count'] = len(content_data['content'].split())
        
        # Extract author
        author_elem = (
            soup.select_one('meta[name="author"]') or
            soup.select_one('.author-name') or
            soup.select_one('.author') or
            soup.select_one('[rel="author"]')
        )
        if author_elem:
            content_data['author'] = author_elem.get('content', '') or author_elem.get_text(strip=True)
        
        # Extract author role
        role_elem = soup.select_one('.author-role, .author-title, .author-position')
        if role_elem:
            content_data['author_role'] = role_elem.get_text(strip=True)
        
        # Extract published time
        published_elem = soup.select_one('meta[property="article:published_time"]')
        if published_elem:
            content_data['published_time'] = published_elem.get('content', '')
        
        # Extract modified time
        modified_elem = soup.select_one('meta[property="article:modified_time"]')
        if modified_elem:
            content_data['modified_time'] = modified_elem.get('content', '')
        
        # Extract categories from breadcrumb
        breadcrumb = soup.select('nav.breadcrumb a, ol.breadcrumb a, .breadcrumb a')
        categories = []
        for crumb in breadcrumb:
            cat_text = crumb.get_text(strip=True)
            if cat_text and cat_text not in ['Home', 'Beranda', 'Jakarta Globe']:
                categories.append(cat_text)
        if categories:
            content_data['categories'] = categories
            content_data['subcategory'] = categories[-1] if categories else ''
        
        # Extract tags
        tags_elem = soup.select_one('meta[name="keywords"]')
        if tags_elem:
            tags_content = tags_elem.get('content', '')
            content_data['tags'] = [t.strip() for t in tags_content.split(',') if t.strip()]
        
        # Extract images
        # Hero image
        hero_img = soup.select_one('meta[property="og:image"]')
        if hero_img:
            hero_url = hero_img.get('content', '')
            if hero_url:
                content_data['images'].append({
                    'url': hero_url,
                    'alt': soup.select_one('meta[property="og:image:alt"]', '').get('content', '') if soup.select_one('meta[property="og:image:alt"]') else '',
                    'is_hero': True
                })
        
        # Content images
        if content_elem:
            for img in content_elem.select('img'):
                img_url = img.get('src', '') or img.get('data-src', '')
                if img_url and not img_url.startswith('data:'):
                    content_data['images'].append({
                        'url': img_url,
                        'alt': img.get('alt', ''),
                        'is_hero': False
                    })
        
        return content_data
    
    def translate_article(self, article: dict, target: str = 'en') -> dict:
        """Translate article to target language."""
        translator = self.translator_en if target == 'en' else self.translator_th
        if not translator:
            return article
        
        translated = article.copy()
        target_lang = 'en' if target == 'en' else 'th'
        
        # Store original values
        translated['title_original'] = article.get('title', '')
        if article.get('content'):
            translated['content_original'] = article.get('content', '')
        if article.get('category'):
            translated['category_original'] = article.get('category', '')
        if article.get('author'):
            translated['author_original'] = article.get('author', '')
        
        try:
            # Translate title
            if article.get('title'):
                translated['title'] = translator.translate(article['title'])
            
            # Translate content
            if article.get('content'):
                content = article['content']
                # Chunk long content
                if len(content) > 4000:
                    chunks = [content[i:i+4000] for i in range(0, len(content), 4000)]
                    translated_content = ' '.join(translator.translate(chunk) for chunk in chunks)
                else:
                    translated_content = translator.translate(content)
                translated['content'] = translated_content
            
            # Translate category
            if article.get('category'):
                translated['category'] = translator.translate(article['category'])
            
            # Translate author
            if article.get('author'):
                translated['author'] = translator.translate(article['author'])
            
            # Add metadata
            translated['translated_at'] = datetime.now().isoformat()
            translated['translation_source'] = 'id'
            translated['translation_target'] = target_lang
            
            logger.info(f"Translated article to {target_lang}: {translated.get('title', '')[:50]}...")
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            # Return original if translation fails
        
        return translated
    
    def save_articles(self) -> None:
        """Save articles to JSON file."""
        try:
            # Load existing data
            existing_data = []
            if os.path.exists(self.output_file):
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # Add new articles
            existing_urls = {a.get('url') for a in existing_data}
            for article in self.articles:
                if article.get('url') not in existing_urls:
                    existing_data.append(article)
            
            # Save
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(self.articles)} new articles to {self.output_file}")
            
        except Exception as e:
            logger.error(f"Error saving articles: {e}")
    
    def save_translated_articles(self, articles: list, filename: str) -> None:
        """Save translated articles to JSON file."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(articles)} translated articles to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving translated articles: {e}")
    
    def scrape(self) -> None:
        """Main scraping method."""
        logger.info("Starting Jakarta Globe scraper...")
        
        # Load existing data
        self.load_existing_data()
        
        # Scrape listing pages
        page = 1
        total_new = 0
        
        while page <= MAX_PAGES:
            url = self.get_page_url(page)
            logger.info(f"Scraping page {page}: {url}")
            
            html = self.fetch_page(url)
            if not html:
                logger.warning(f"Failed to fetch page {page}, stopping")
                break
            
            articles = self.parse_listing_page(html)
            
            if not articles:
                logger.info("No articles found, stopping pagination")
                break
            
            # Check if should stop
            if self.should_stop_pagination(articles):
                logger.info("All articles are older than cutoff date, stopping pagination")
                # Still add articles within range
                for article in articles:
                    if article.get('date_parsed') and article['date_parsed'] >= self.cutoff_date:
                        if not article.get('is_existing'):
                            self.articles.append(article)
                            total_new += 1
                break
            
            # Add articles
            for article in articles:
                if not article.get('is_existing'):
                    self.articles.append(article)
                    total_new += 1
            
            logger.info(f"Page {page}: {len(articles)} articles, {sum(1 for a in articles if not a.get('is_existing'))} new")
            
            page += 1
            time.sleep(REQUEST_DELAY)
        
        logger.info(f"Found {total_new} new articles from {page - 1} pages")
        
        # Fetch content if requested
        if self.fetch_content and self.articles:
            logger.info("Fetching article content...")
            for i, article in enumerate(self.articles):
                logger.info(f"Fetching content {i+1}/{len(self.articles)}: {article.get('title', '')[:50]}")
                content_data = self.fetch_article_content(article['url'])
                article.update(content_data)
                time.sleep(REQUEST_DELAY)
        
        # Save main data
        if self.articles:
            self.save_articles()
        
        # Translate articles
        if self.translate and self.articles:
            logger.info("Translating articles to English...")
            translated_en = []
            for article in self.articles:
                translated = self.translate_article(article, 'en')
                translated_en.append(translated)
                time.sleep(0.5)  # Rate limiting
            self.save_translated_articles(translated_en, self.translated_output)
        
        if self.translate_thai and self.articles:
            logger.info("Translating articles to Thai...")
            translated_th = []
            for article in self.articles:
                translated = self.translate_article(article, 'th')
                translated_th.append(translated)
                time.sleep(0.5)  # Rate limiting
            self.save_translated_articles(translated_th, self.translated_thai_output)
        
        logger.info("Scraping completed!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Jakarta Globe News Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--days', '-d',
        type=int,
        default=DEFAULT_DAYS_BACK,
        help=f'Number of days back to scrape (default: {DEFAULT_DAYS_BACK})'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=DEFAULT_OUTPUT_FILE,
        help=f'Main output file (default: {DEFAULT_OUTPUT_FILE})'
    )
    
    parser.add_argument(
        '--url',
        type=str,
        default=BASE_URL,
        help='Base URL to scrape'
    )
    
    parser.add_argument(
        '--fetch-content', '-c',
        action='store_true',
        help='Fetch full article content'
    )
    
    parser.add_argument(
        '--translate', '-t',
        action='store_true',
        help='Translate to English'
    )
    
    parser.add_argument(
        '--translate-thai',
        action='store_true',
        help='Translate to Thai'
    )
    
    parser.add_argument(
        '--translated-output',
        type=str,
        help='English translation output file'
    )
    
    parser.add_argument(
        '--translated-thai-output',
        type=str,
        help='Thai translation output file'
    )
    
    args = parser.parse_args()
    
    scraper = JakartaGlobeScraper(
        days_back=args.days,
        output_file=args.output,
        url=args.url,
        fetch_content=args.fetch_content,
        translate=args.translate,
        translate_thai=args.translate_thai,
        translated_output=args.translated_output,
        translated_thai_output=args.translated_thai_output
    )
    
    scraper.scrape()


if __name__ == '__main__':
    main()
