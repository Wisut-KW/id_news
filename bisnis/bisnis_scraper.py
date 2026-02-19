#!/usr/bin/env python3
"""
Bisnis.com News Scraper - Interactive Script
Run this instead of the notebook if you prefer
"""

import json
import logging
import os
import re
import ssl
import gzip
import urllib.request
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from urllib.parse import urljoin

from bs4 import BeautifulSoup

# Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


class BisnisScraperInteractive:
    """Interactive scraper with user prompts."""
    
    def __init__(self):
        self.days_back = 2
        self.base_url = 'https://www.bisnis.com/index?categoryId=43'
        self.output_dir = 'test_results'
        self.fetch_content = False
        self.translate_en = False
        self.translate_th = False
        
    def get_user_input(self):
        """Get configuration from user."""
        print("\n" + "="*60)
        print("BISNIS.COM NEWS SCRAPER")
        print("="*60 + "\n")
        
        # Days back
        days = input("How many days back to scrape? [default: 2]: ").strip()
        if days and days.isdigit():
            self.days_back = int(days)
        
        # Content fetching
        content = input("Fetch full article content? (y/n) [default: n]: ").strip().lower()
        self.fetch_content = content in ['y', 'yes']
        
        # Translation
        trans_en = input("Translate to English? (y/n) [default: n]: ").strip().lower()
        self.translate_en = trans_en in ['y', 'yes']
        
        trans_th = input("Translate to Thai? (y/n) [default: n]: ").strip().lower()
        self.translate_th = trans_th in ['y', 'yes']
        
        print(f"\nConfiguration:")
        print(f"  Days back: {self.days_back}")
        print(f"  Fetch content: {self.fetch_content}")
        print(f"  English translation: {self.translate_en}")
        print(f"  Thai translation: {self.translate_th}")
        
        confirm = input("\nStart scraping? (y/n): ").strip().lower()
        return confirm in ['y', 'yes']
    
    def fetch_url(self, url: str, timeout: int = 30) -> Optional[str]:
        """Fetch URL content."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ssl_context) as response:
                content = response.read()
                if response.info().get('Content-Encoding') == 'gzip':
                    content = gzip.decompress(content)
                
                content_type = response.headers.get('Content-Type', '')
                charset = 'utf-8'
                if 'charset=' in content_type:
                    charset = content_type.split('charset=')[-1].split(';')[0].strip()
                
                try:
                    return content.decode(charset)
                except:
                    return content.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_date_from_url(self, url: str) -> Optional[datetime]:
        """Extract date from URL."""
        match = re.search(r'/read/(\d{4})(\d{2})(\d{2})/(\d+)/(\d+)/', url)
        if match:
            year, month, day = match.groups()[:3]
            try:
                return datetime(int(year), int(month), int(day))
            except ValueError:
                return None
        return None
    
    def fetch_page(self, page_num: int) -> Optional[BeautifulSoup]:
        """Fetch a page."""
        if '?' in self.base_url:
            url = f"{self.base_url}&page={page_num}"
        else:
            url = f"{self.base_url}?page={page_num}"
        
        try:
            logger.info(f"Fetching page {page_num}...")
            html_content = self.fetch_url(url)
            if html_content is None:
                return None
            return BeautifulSoup(html_content, 'html.parser')
        except Exception as e:
            logger.error(f"Error: {e}")
            return None
    
    def extract_article_data(self, article_elem) -> Optional[Dict]:
        """Extract article data."""
        try:
            link_elem = article_elem.find('a', href=True, class_='artLink')
            if not link_elem:
                link_elem = article_elem.find('a', href=True)
            
            if not link_elem:
                return None
            
            url = link_elem['href']
            if not url.startswith('http'):
                url = urljoin("https://www.bisnis.com", url)
            
            pattern = re.compile(r'/read/(\d{8})/(\d+)/(\d+)/')
            if not pattern.search(url):
                return None
            
            title_elem = article_elem.find('h4', class_='artTitle')
            if not title_elem:
                title_elem = link_elem
            
            title = title_elem.get_text(strip=True) if title_elem else "No title"
            article_date = self.extract_date_from_url(url)
            
            channel_elem = article_elem.find('div', class_='artChannel')
            channel = channel_elem.get_text(strip=True) if channel_elem else ""
            
            return {
                'title': title,
                'url': url,
                'date': article_date.isoformat() if article_date else None,
                'date_parsed': article_date,
                'channel': channel,
                'scraped_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error extracting: {e}")
            return None
    
    def fetch_article_content(self, url: str) -> Dict:
        """Fetch full article content."""
        content_data = {
            'content': '', 'content_html': '', 'author': '', 'author_role': '',
            'published_time': '', 'modified_time': '', 'tags': [],
            'categories': [], 'subcategory': '', 'images': [],
            'summary': '', 'word_count': 0
        }
        
        try:
            html_content = self.fetch_url(url)
            if html_content is None:
                return content_data
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Meta data
            author_meta = soup.find('meta', attrs={'name': 'author'})
            if author_meta:
                content_data['author'] = str(author_meta.get('content', '')).strip()
            
            published_meta = soup.find('meta', attrs={'property': 'article:published_time'})
            if published_meta:
                content_data['published_time'] = str(published_meta.get('content', '')).strip()
            
            # Author section
            author_section = soup.find('div', class_='author') or soup.find('div', class_='detail__author')
            if author_section:
                author_name = author_section.find(['h5', 'h4', 'span', 'a'])
                if author_name and not content_data['author']:
                    content_data['author'] = author_name.get_text(strip=True)
            
            # Categories
            breadcrumb = soup.find('ul', class_='breadcrumb')
            if breadcrumb:
                categories = []
                for item in breadcrumb.find_all('li'):
                    link = item.find('a')
                    if link:
                        cat_text = link.get_text(strip=True)
                        if cat_text and cat_text.lower() not in ['home', 'bisnis.com']:
                            categories.append(cat_text)
                content_data['categories'] = categories
            
            # Tags
            keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
            if keywords_meta:
                keywords = str(keywords_meta.get('content', ''))
                if keywords:
                    content_data['tags'] = [tag.strip() for tag in keywords.split(',') if tag.strip()]
            
            # Content
            content_selectors = ['div.description', 'div.detail__content', 'article']
            content_elem = None
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    break
            
            if content_elem:
                content_data['content_html'] = str(content_elem)
                paragraphs = content_elem.find_all('p')
                if paragraphs:
                    if len(paragraphs) > 0:
                        first_p = paragraphs[0].get_text(strip=True)
                        if len(first_p) > 20:
                            content_data['summary'] = first_p
                    
                    content_text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    if len(content_text) > 50:
                        content_data['content'] = content_text
                        content_data['word_count'] = len(content_text.split())
            
        except Exception as e:
            logger.error(f"Error: {e}")
        
        return content_data
    
    def scrape(self):
        """Main scraping."""
        cutoff_date = datetime.now() - timedelta(days=self.days_back)
        logger.info(f"Scraping {self.days_back} days back...")
        
        articles = []
        page_num = 1
        max_pages = 5  # Limit for demo
        
        while page_num <= max_pages:
            soup = self.fetch_page(page_num)
            if not soup:
                break
            
            art_items = soup.find_all('div', class_='artItem')
            if not art_items:
                break
            
            page_articles = []
            for elem in art_items:
                article = self.extract_article_data(elem)
                if article:
                    page_articles.append(article)
            
            if not page_articles:
                break
            
            articles.extend(page_articles)
            logger.info(f"Page {page_num}: {len(page_articles)} articles")
            
            page_num += 1
        
        logger.info(f"Total: {len(articles)} articles")
        
        # Fetch content
        if self.fetch_content and articles:
            logger.info(f"Fetching content for {len(articles)} articles...")
            for i, article in enumerate(articles):
                logger.info(f"Content [{i+1}/{len(articles)}]")
                content_data = self.fetch_article_content(article['url'])
                article.update(content_data)
        
        return articles
    
    def translate(self, articles, target_lang):
        """Translate articles."""
        try:
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(source='id', target=target_lang)
        except ImportError:
            logger.error("deep-translator not installed")
            return []
        
        translated = []
        logger.info(f"Translating {len(articles)} to {target_lang}...")
        
        for i, article in enumerate(articles):
            try:
                trans_article = article.copy()
                
                if article.get('title'):
                    trans_article['title'] = translator.translate(article['title'][:4000])
                    trans_article['title_original'] = article['title']
                
                if article.get('content'):
                    content = article['content']
                    if len(content) > 4000:
                        chunks = [content[i:i+4000] for i in range(0, len(content), 4000)]
                        trans_content = ' '.join([translator.translate(chunk) for chunk in chunks])
                    else:
                        trans_content = translator.translate(content)
                    trans_article['content'] = trans_content
                    trans_article['content_original'] = article['content']
                
                if article.get('channel'):
                    trans_article['channel'] = translator.translate(article['channel'])
                    trans_article['channel_original'] = article['channel']
                
                trans_article['translated_at'] = datetime.now().isoformat()
                trans_article['translation_source'] = 'id'
                trans_article['translation_target'] = target_lang
                
                translated.append(trans_article)
                
                import time
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Translation error: {e}")
                translated.append(article)
        
        return translated
    
    def save(self, data, filename):
        """Save to file."""
        os.makedirs(self.output_dir, exist_ok=True)
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Saved: {filepath}")
        return filepath
    
    def run(self):
        """Main run method."""
        if not self.get_user_input():
            print("Cancelled.")
            return
        
        print("\n" + "="*60)
        print("STARTING SCRAPE")
        print("="*60 + "\n")
        
        # Scrape
        articles = self.scrape()
        
        if not articles:
            print("No articles found!")
            return
        
        # Save original
        self.save(articles, 'news_data.json')
        
        # Translate English
        if self.translate_en:
            articles_en = self.translate(articles, 'en')
            self.save(articles_en, 'news_data_translated_en.json')
        
        # Translate Thai
        if self.translate_th:
            articles_th = self.translate(articles, 'th')
            self.save(articles_th, 'news_data_translated_th.json')
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Articles scraped: {len(articles)}")
        print(f"Output directory: {self.output_dir}/")
        print(f"Files saved:")
        for f in os.listdir(self.output_dir):
            print(f"  - {f}")
        print("\n✓ Done!")


if __name__ == '__main__':
    scraper = BisnisScraperInteractive()
    scraper.run()
