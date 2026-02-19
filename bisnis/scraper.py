#!/usr/bin/env python3
"""
Bisnis.com News Scraper
Scrapes news articles from Bisnis.com website.
"""

import gzip
import json
import logging
import os
import re
import ssl
import sys
import urllib.request
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urljoin, urlparse

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

BASE_URL = "https://www.bisnis.com/index?categoryId=43"
OUTPUT_FILE = "news_data.json"

# Create SSL context that allows us to connect
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


class BisnisScraper:
    def __init__(
        self,
        days_back: int = 2,
        output_file: str = OUTPUT_FILE,
        base_url: str = BASE_URL,
        fetch_content: bool = False,
        translate: bool = False,
        translate_thai: bool = False,
        translated_output_file: str = None,
        translated_thai_output_file: str = None
    ):
        self.days_back = days_back
        self.output_file = output_file
        self.base_url = base_url
        self.fetch_content = fetch_content
        self.translate = translate
        self.translate_thai = translate_thai
        self.translated_output_file = translated_output_file or output_file.replace('.json', '_translated_en.json')
        self.translated_thai_output_file = translated_thai_output_file or output_file.replace('.json', '_translated_th.json')
        self.cutoff_date = datetime.now() - timedelta(days=days_back)
        self.existing_urls = self._load_existing_urls()
        
        # Pattern to match article URLs with dates like /read/20260219/9/1954004/slug
        self.article_url_pattern = re.compile(r'/read/(\d{8})/(\d+)/(\d+)/')
        
        # Initialize translators
        self.translator = None
        self.translator_thai = None
        
        if self.translate or self.translate_thai:
            try:
                from deep_translator import GoogleTranslator
                
                if self.translate:
                    self.translator = GoogleTranslator(source='id', target='en')
                    logger.info("Translation enabled: Indonesian -> English")
                
                if self.translate_thai:
                    self.translator_thai = GoogleTranslator(source='id', target='th')
                    logger.info("Translation enabled: Indonesian -> Thai")
                    
            except ImportError:
                logger.warning("deep-translator not installed. Translation disabled.")
                self.translate = False
                self.translate_thai = False
            except Exception as e:
                logger.warning(f"Could not initialize translator: {e}")
                self.translate = False
                self.translate_thai = False
    
    def _fetch_url(self, url: str, timeout: int = 30) -> Optional[str]:
        """Fetch URL content using urllib and return decoded string."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ssl_context) as response:
                content = response.read()
                # Handle gzip compression
                if response.info().get('Content-Encoding') == 'gzip':
                    content = gzip.decompress(content)
                
                # Try to detect encoding from response headers
                content_type = response.headers.get('Content-Type', '')
                if 'charset=' in content_type:
                    charset = content_type.split('charset=')[-1].split(';')[0].strip()
                else:
                    charset = 'utf-8'
                
                try:
                    return content.decode(charset)
                except (UnicodeDecodeError, LookupError):
                    # Fallback encodings
                    for enc in ['utf-8', 'iso-8859-1', 'windows-1252']:
                        try:
                            return content.decode(enc, errors='ignore')
                        except:
                            continue
                    return content.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

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
        """Parse various date formats."""
        date_formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%d %H:%M:%S',
            '%d %B %Y',
            '%d %b %Y',
            '%B %d, %Y',
            '%b %d, %Y',
        ]
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        logger.debug(f"Could not parse date: {date_str}")
        return None

    def _extract_date_from_url(self, url: str) -> Optional[datetime]:
        """Extract date from URL like /read/20260219/9/1954004/slug"""
        match = re.search(r'/read/(\d{4})(\d{2})(\d{2})/(\d+)/(\d+)/', url)
        if match:
            year, month, day = match.groups()[:3]
            try:
                return datetime(int(year), int(month), int(day))
            except ValueError:
                return None
        return None

    def _fetch_page(self, page_num: int) -> Optional[BeautifulSoup]:
        """Fetch a page and return BeautifulSoup object."""
        # Build URL with proper pagination
        if '?' in self.base_url:
            url = f"{self.base_url}&page={page_num}"
        else:
            url = f"{self.base_url}?page={page_num}"
        
        try:
            logger.info(f"Fetching: {url}")
            
            html_content = self._fetch_url(url)
            if html_content is None:
                return None
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Debug: Check if we got article containers
            art_items = len(soup.find_all('div', class_='artItem'))
            logger.debug(f"Page {page_num}: Found {art_items} artItem containers, {len(html_content)} chars")
            return soup
        except Exception as e:
            logger.error(f"Error fetching page {page_num}: {e}")
            return None

    def _fetch_article_content(self, url: str) -> dict:
        """Fetch and extract comprehensive article content from individual article page.
        
        Args:
            url: Article URL to fetch
            
        Returns:
            dict with content, author, and other article-specific fields
        """
        content_data = {
            'content': '',
            'content_html': '',
            'author': '',
            'author_role': '',
            'published_time': '',
            'modified_time': '',
            'tags': [],
            'categories': [],
            'subcategory': '',
            'images': [],
            'summary': '',
            'word_count': 0,
            'fetch_error': None
        }
        
        try:
            logger.debug(f"Fetching article content: {url}")
            html_content = self._fetch_url(url)
            if html_content is None:
                content_data['fetch_error'] = "Failed to fetch URL"
                return content_data
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract meta data
            # Author from meta tag
            author_meta = soup.find('meta', attrs={'name': 'author'})
            if author_meta:
                content_data['author'] = str(author_meta.get('content', '')).strip()
            
            # Published time from meta tag
            published_meta = soup.find('meta', attrs={'property': 'article:published_time'}) or \
                           soup.find('meta', attrs={'name': 'publish-date'})
            if published_meta:
                content_data['published_time'] = str(published_meta.get('content', '')).strip()
            
            # Modified time from meta tag
            modified_meta = soup.find('meta', attrs={'property': 'article:modified_time'})
            if modified_meta:
                content_data['modified_time'] = str(modified_meta.get('content', '')).strip()
            
            # Extract author with role from page structure
            author_section = soup.find('div', class_='author') or soup.find('div', class_='detail__author')
            if author_section:
                author_name = author_section.find(['h5', 'h4', 'span', 'a'])
                if author_name and not content_data['author']:
                    content_data['author'] = author_name.get_text(strip=True)
                
                author_role = author_section.find(['span', 'div'], class_=re.compile('role', re.I))
                if author_role:
                    content_data['author_role'] = author_role.get_text(strip=True)
            
            # If no author found yet, try more selectors
            if not content_data['author']:
                author_elem = soup.find(['span', 'div', 'a'], class_=re.compile('author', re.I))
                if author_elem:
                    content_data['author'] = author_elem.get_text(strip=True)
            
            # Extract categories from breadcrumbs
            breadcrumb = soup.find('ul', class_='breadcrumb') or soup.find('nav', class_='breadcrumb')
            if breadcrumb:
                categories = []
                for item in breadcrumb.find_all('li'):
                    link = item.find('a')
                    if link:
                        cat_text = link.get_text(strip=True)
                        if cat_text and cat_text.lower() not in ['home', 'bisnis.com']:
                            categories.append(cat_text)
                content_data['categories'] = categories
                if categories:
                    content_data['subcategory'] = categories[-1] if len(categories) > 1 else categories[0]
            
            # Extract tags/keywords
            keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
            if keywords_meta:
                keywords = str(keywords_meta.get('content', ''))
                if keywords:
                    content_data['tags'] = [tag.strip() for tag in keywords.split(',') if tag.strip()]
            
            # Also try to find tags in tag containers
            tag_container = soup.find('div', class_=re.compile('tag', re.I))
            if tag_container:
                tag_links = tag_container.find_all('a')
                for tag in tag_links:
                    tag_text = tag.get_text(strip=True)
                    if tag_text and tag_text not in content_data['tags']:
                        content_data['tags'].append(tag_text)
            
            # Extract main article content
            content_selectors = [
                'div.description',
                'div.detail__content', 
                'div.article-content',
                'div.entry-content',
                'article div.content',
                'div.main-content',
                'article',
            ]
            
            content_elem = None
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    break
            
            if content_elem:
                # Save HTML content
                content_data['content_html'] = str(content_elem)
                
                # Extract paragraphs
                paragraphs = content_elem.find_all('p')
                if paragraphs:
                    # First paragraph is usually the summary/lead
                    if len(paragraphs) > 0:
                        first_p = paragraphs[0].get_text(strip=True)
                        if len(first_p) > 20:
                            content_data['summary'] = first_p
                    
                    # All paragraphs as content
                    content_text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    if len(content_text) > 50:
                        content_data['content'] = content_text
                        content_data['word_count'] = len(content_text.split())
                
                # Extract images within content
                for img in content_elem.find_all('img'):
                    img_src = img.get('src', '')
                    img_alt = img.get('alt', '')
                    # Handle case where src might be a list
                    if isinstance(img_src, list):
                        img_src = img_src[0] if img_src else ''
                    if img_src and not str(img_src).startswith('data:'):
                        content_data['images'].append({
                            'url': str(img_src),
                            'alt': str(img_alt)
                        })
            
            # Fallback content extraction
            if not content_data['content']:
                article_area = soup.find('div', class_='detail') or soup.find('article') or soup.find('main')
                if article_area:
                    paragraphs = article_area.find_all('p')
                    content_text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    if len(content_text) > 50:
                        content_data['content'] = content_text
                        content_data['word_count'] = len(content_text.split())
            
            # Extract main image (hero image)
            hero_img = soup.find('meta', attrs={'property': 'og:image'})
            if hero_img:
                hero_url = str(hero_img.get('content', ''))
                if hero_url and not any(img['url'] == hero_url for img in content_data['images']):
                    content_data['images'].insert(0, {'url': hero_url, 'alt': 'Hero Image', 'is_hero': True})
            
            logger.debug(f"Successfully fetched content for {url}: {len(content_data['content'])} chars, "
                        f"author: {content_data['author']}, tags: {len(content_data['tags'])}, "
                        f"images: {len(content_data['images'])}, words: {content_data['word_count']}")
            
        except Exception as e:
            logger.error(f"Error fetching article {url}: {e}")
            content_data['fetch_error'] = str(e)
        
        return content_data

    def _extract_article_data(self, article_elem, skip_existing: bool = True) -> Optional[dict]:
        """Extract article data from element.
        
        Args:
            article_elem: BeautifulSoup element containing article (div.artItem)
            skip_existing: If True, return None for existing URLs. If False, still extract.
        """
        try:
            # Find the link to the article
            link_elem = article_elem.find('a', href=True, class_='artLink')
            if not link_elem:
                # Try finding any link with href
                link_elem = article_elem.find('a', href=True)
            
            if not link_elem:
                return None
            
            url = link_elem['href']
            if not url.startswith('http'):
                url = urljoin("https://www.bisnis.com", url)
            
            # Only process actual article URLs with date pattern
            if not self.article_url_pattern.search(url):
                return None
            
            # Check if already exists
            is_existing = url in self.existing_urls
            if is_existing and skip_existing:
                logger.debug(f"Skipping existing URL: {url}")
                return None
            
            # Extract title
            title_elem = article_elem.find('h4', class_='artTitle')
            if not title_elem:
                title_elem = link_elem  # Fallback to link text
            
            title = title_elem.get_text(strip=True) if title_elem else "No title"
            
            # Extract date from URL (most reliable)
            article_date = self._extract_date_from_url(url)
            date_str = None
            
            # Also try to get date from element
            date_elem = article_elem.find('div', class_='artDate')
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                # Note: date_text is likely relative like "5 menit yang lalu"
                # We keep it for reference but rely on URL date
                date_str = date_text
            
            # Extract channel/category
            channel_elem = article_elem.find('div', class_='artChannel')
            channel = ""
            if channel_elem:
                channel = channel_elem.get_text(strip=True)
            
            return {
                'title': title,
                'url': url,
                'date': article_date.isoformat() if article_date else date_str,
                'date_parsed': article_date,
                'channel': channel,
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
        """Find article elements using Bisnis.com specific selectors.
        
        Returns:
            tuple: (all_articles, new_articles) where all_articles includes duplicates
        """
        all_articles = []
        new_articles = []
        processed_urls = set()
        
        # Method 1: Look for .artItem containers (main article containers on Bisnis.com)
        art_items = soup.find_all('div', class_='artItem')
        logger.debug(f"Found {len(art_items)} .artItem elements")
        
        for elem in art_items:
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

    def _translate_text(self, text: str, max_retries: int = 3) -> str:
        """Translate text from Indonesian to English.
        
        Args:
            text: Text to translate
            max_retries: Maximum number of retries on failure
            
        Returns:
            Translated text or original text if translation fails
        """
        if not text or not self.translator:
            return text
        
        # Skip translation for very short texts
        if len(text.strip()) < 3:
            return text
        
        for attempt in range(max_retries):
            try:
                # deep_translator has a limit on text length, split if needed
                max_chunk_size = 4000
                if len(text) > max_chunk_size:
                    chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
                    translated_chunks = []
                    for chunk in chunks:
                        translated_chunk = self.translator.translate(chunk)
                        translated_chunks.append(translated_chunk)
                    return ' '.join(translated_chunks)
                else:
                    return self.translator.translate(text)
            except Exception as e:
                logger.warning(f"Translation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(1)  # Wait before retry
                else:
                    logger.error(f"Translation failed after {max_retries} attempts")
                    return text
        
        return text
    
    def _translate_article(self, article: dict, target_lang: str = 'en') -> dict:
        """Translate an article from Indonesian to target language.
        
        Args:
            article: Article dictionary with Indonesian content
            target_lang: Target language code ('en' or 'th')
            
        Returns:
            Article dictionary with translated content
        """
        translated = article.copy()
        
        # Select translator based on target language
        if target_lang == 'th':
            translator = self.translator_thai
        else:
            translator = self.translator
        
        # Temporarily set the translator for _translate_text to use
        original_translator = self.translator
        if target_lang == 'th':
            self.translator = translator
        
        try:
            # Translate title
            if article.get('title'):
                logger.debug(f"Translating title to {target_lang}: {article['title'][:60]}...")
                translated['title'] = self._translate_text(article['title'])
                translated['title_original'] = article['title']
            
            # Translate content if available
            if article.get('content'):
                logger.debug(f"Translating content to {target_lang} ({len(article['content'])} chars)...")
                translated['content'] = self._translate_text(article['content'])
                translated['content_original'] = article['content']
            
            # Translate channel
            if article.get('channel'):
                translated['channel'] = self._translate_text(article['channel'])
                translated['channel_original'] = article['channel']
            
            # Translate author if available
            if article.get('author'):
                translated['author'] = self._translate_text(article['author'])
                translated['author_original'] = article['author']
            
            translated['translated_at'] = datetime.now().isoformat()
            translated['translation_source'] = 'id'
            translated['translation_target'] = target_lang
            
        finally:
            # Restore original translator
            self.translator = original_translator
        
        return translated
    
    def _save_translated_data(self, articles: list, target_lang: str = 'en'):
        """Save translated articles to a separate JSON file."""
        if not articles:
            return
        
        output_file = self.translated_output_file if target_lang == 'en' else self.translated_thai_output_file
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Saved {len(articles)} translated articles ({target_lang}) to {output_file}")
        except Exception as e:
            logger.error(f"Error saving translated data: {e}")
    
    def _load_translated_data(self, target_lang: str = 'en') -> list:
        """Load existing translated data."""
        output_file = self.translated_output_file if target_lang == 'en' else self.translated_thai_output_file
        if not os.path.exists(output_file):
            return []
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Error loading translated data: {e}")
            return []

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
            # Fetch content for new articles if enabled
            if self.fetch_content:
                logger.info(f"Fetching content for {len(new_articles)} new articles...")
                for i, article in enumerate(new_articles, 1):
                    logger.info(f"Fetching content [{i}/{len(new_articles)}]: {article['title'][:60]}...")
                    content_data = self._fetch_article_content(article['url'])
                    article['content'] = content_data['content']
                    article['author'] = content_data['author']
                    if content_data['fetch_error']:
                        article['content_error'] = content_data['fetch_error']
            
            all_articles.extend(new_articles)
            self._save_data(all_articles)
            logger.info(f"Added {len(new_articles)} new articles")
            
            # Translate articles to English if enabled
            if self.translate and self.translator:
                logger.info(f"Translating {len(new_articles)} new articles to English...")
                translated_articles = []
                for i, article in enumerate(new_articles, 1):
                    logger.info(f"Translating to English [{i}/{len(new_articles)}]: {article['title'][:60]}...")
                    translated_article = self._translate_article(article, target_lang='en')
                    translated_articles.append(translated_article)
                    # Small delay to avoid rate limiting
                    import time
                    time.sleep(0.5)
                
                # Load existing translated data and append new translations
                existing_translated = self._load_translated_data(target_lang='en')
                # Filter out any existing translations for the same URLs
                existing_urls = {a['url'] for a in existing_translated}
                new_translated = [a for a in translated_articles if a['url'] not in existing_urls]
                existing_translated.extend(new_translated)
                self._save_translated_data(existing_translated, target_lang='en')
                logger.info(f"Added {len(new_translated)} English translated articles")
            
            # Translate articles to Thai if enabled
            if self.translate_thai and self.translator_thai:
                logger.info(f"Translating {len(new_articles)} new articles to Thai...")
                translated_articles_th = []
                for i, article in enumerate(new_articles, 1):
                    logger.info(f"Translating to Thai [{i}/{len(new_articles)}]: {article['title'][:60]}...")
                    translated_article = self._translate_article(article, target_lang='th')
                    translated_articles_th.append(translated_article)
                    # Small delay to avoid rate limiting
                    import time
                    time.sleep(0.5)
                
                # Load existing translated data and append new translations
                existing_translated_th = self._load_translated_data(target_lang='th')
                # Filter out any existing translations for the same URLs
                existing_urls_th = {a['url'] for a in existing_translated_th}
                new_translated_th = [a for a in translated_articles_th if a['url'] not in existing_urls_th]
                existing_translated_th.extend(new_translated_th)
                self._save_translated_data(existing_translated_th, target_lang='th')
                logger.info(f"Added {len(new_translated_th)} Thai translated articles")
        else:
            logger.info("No new articles found")
        
        return new_articles


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Scrape Bisnis.com news'
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
    parser.add_argument(
        '--fetch-content', '-c',
        action='store_true',
        help='Fetch full article content from each article page (slower but more complete)'
    )
    parser.add_argument(
        '--translate', '-t',
        action='store_true',
        help='Translate articles from Indonesian to English and save to separate file'
    )
    parser.add_argument(
        '--translate-thai',
        action='store_true',
        help='Translate articles from Indonesian to Thai and save to separate file'
    )
    parser.add_argument(
        '--translated-output',
        type=str,
        default=None,
        help='Output file for English translated articles (default: news_data_translated_en.json)'
    )
    parser.add_argument(
        '--translated-thai-output',
        type=str,
        default=None,
        help='Output file for Thai translated articles (default: news_data_translated_th.json)'
    )
    args = parser.parse_args()
    
    scraper = BisnisScraper(
        days_back=args.days,
        output_file=args.output,
        base_url=args.url,
        fetch_content=args.fetch_content,
        translate=args.translate,
        translate_thai=args.translate_thai,
        translated_output_file=args.translated_output,
        translated_thai_output_file=args.translated_thai_output
    )
    
    try:
        new_articles = scraper.scrape()
        print(f"\nScraping complete! Added {len(new_articles)} new articles.")
        if args.translate and scraper.translator:
            print(f"English translated articles saved to: {scraper.translated_output_file}")
        if args.translate_thai and scraper.translator_thai:
            print(f"Thai translated articles saved to: {scraper.translated_thai_output_file}")
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
