#!/usr/bin/env python3
"""
Test script for bisnis_scraper.ipynb functionality
Saves results to test_results/ folder
"""

import json
import logging
import os
import re
import ssl
import gzip
import urllib.request
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Set
from urllib.parse import urljoin

from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create SSL context
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


class BisnisScraperTest:
    """Test scraper for notebook validation."""
    
    def __init__(self, days_back=1, base_url=None, output_dir='test_results'):
        self.days_back = days_back
        self.base_url = base_url or 'https://www.bisnis.com/index?categoryId=43'
        self.output_dir = output_dir
        self.cutoff_date = datetime.now() - timedelta(days=days_back)
        self.existing_urls = set()
        self.article_url_pattern = re.compile(r'/read/(\d{8})/(\d+)/(\d+)/')
        self.scraped_data = []
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
    def fetch_url(self, url: str, timeout: int = 30) -> Optional[str]:
        """Fetch URL content using urllib."""
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
                if 'charset=' in content_type:
                    charset = content_type.split('charset=')[-1].split(';')[0].strip()
                else:
                    charset = 'utf-8'
                
                try:
                    return content.decode(charset)
                except:
                    for enc in ['utf-8', 'iso-8859-1', 'windows-1252']:
                        try:
                            return content.decode(enc, errors='ignore')
                        except:
                            continue
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
        """Fetch a page and return BeautifulSoup object."""
        if '?' in self.base_url:
            url = f"{self.base_url}&page={page_num}"
        else:
            url = f"{self.base_url}?page={page_num}"
        
        try:
            logger.info(f"Fetching page {page_num}: {url}")
            html_content = self.fetch_url(url)
            if html_content is None:
                return None
            return BeautifulSoup(html_content, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching page {page_num}: {e}")
            return None
    
    def extract_article_data(self, article_elem) -> Optional[Dict]:
        """Extract article data from element."""
        try:
            link_elem = article_elem.find('a', href=True, class_='artLink')
            if not link_elem:
                link_elem = article_elem.find('a', href=True)
            
            if not link_elem:
                return None
            
            url = link_elem['href']
            if not url.startswith('http'):
                url = urljoin("https://www.bisnis.com", url)
            
            if not self.article_url_pattern.search(url):
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
            logger.error(f"Error extracting article: {e}")
            return None
    
    def fetch_article_content(self, url: str) -> Dict:
        """Fetch comprehensive article content."""
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
            'word_count': 0
        }
        
        try:
            logger.info(f"Fetching content: {url[:80]}...")
            html_content = self.fetch_url(url)
            if html_content is None:
                return content_data
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract meta data
            author_meta = soup.find('meta', attrs={'name': 'author'})
            if author_meta:
                content_data['author'] = str(author_meta.get('content', '')).strip()
            
            published_meta = soup.find('meta', attrs={'property': 'article:published_time'})
            if published_meta:
                content_data['published_time'] = str(published_meta.get('content', '')).strip()
            
            # Extract author section
            author_section = soup.find('div', class_='author') or soup.find('div', class_='detail__author')
            if author_section:
                author_name = author_section.find(['h5', 'h4', 'span', 'a'])
                if author_name and not content_data['author']:
                    content_data['author'] = author_name.get_text(strip=True)
                author_role = author_section.find(['span', 'div'], class_=re.compile('role', re.I))
                if author_role:
                    content_data['author_role'] = author_role.get_text(strip=True)
            
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
            
            # Extract tags
            keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
            if keywords_meta:
                keywords = str(keywords_meta.get('content', ''))
                if keywords:
                    content_data['tags'] = [tag.strip() for tag in keywords.split(',') if tag.strip()]
            
            # Extract content
            content_selectors = ['div.description', 'div.detail__content', 'div.article-content', 'article']
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
                
                # Extract images
                for img in content_elem.find_all('img'):
                    img_src = img.get('src', '')
                    img_alt = img.get('alt', '')
                    if isinstance(img_src, list):
                        img_src = img_src[0] if img_src else ''
                    if img_src and not str(img_src).startswith('data:'):
                        content_data['images'].append({
                            'url': str(img_src),
                            'alt': str(img_alt)
                        })
            
            # Hero image
            hero_img = soup.find('meta', attrs={'property': 'og:image'})
            if hero_img:
                hero_url = str(hero_img.get('content', ''))
                if hero_url and not any(img['url'] == hero_url for img in content_data['images']):
                    content_data['images'].insert(0, {'url': hero_url, 'alt': 'Hero Image', 'is_hero': True})
            
        except Exception as e:
            logger.error(f"Error fetching content: {e}")
        
        return content_data
    
    def scrape(self, fetch_content=True):
        """Main scraping method."""
        logger.info(f"Starting test scrape with {self.days_back} days back")
        logger.info(f"Output directory: {self.output_dir}")
        
        articles = []
        page_num = 1
        max_pages = 2  # Limit for testing
        
        while page_num <= max_pages:
            logger.info(f"Fetching page {page_num}...")
            soup = self.fetch_page(page_num)
            if not soup:
                logger.warning(f"Failed to fetch page {page_num}")
                break
            
            art_items = soup.find_all('div', class_='artItem')
            logger.info(f"Found {len(art_items)} article containers on page {page_num}")
            
            if not art_items:
                logger.info("No articles found on this page")
                break
            
            page_articles = []
            for elem in art_items:
                article = self.extract_article_data(elem)
                if article and article['url'] not in self.existing_urls:
                    page_articles.append(article)
            
            logger.info(f"Extracted {len(page_articles)} articles from page {page_num}")
            
            if not page_articles:
                break
            
            # Check date threshold
            all_old = all(
                a.get('date_parsed') and a['date_parsed'] < self.cutoff_date
                for a in page_articles if a.get('date_parsed')
            )
            if all_old:
                logger.info("All articles on this page are older than cutoff")
                break
            
            articles.extend(page_articles)
            page_num += 1
        
        logger.info(f"Total articles found: {len(articles)}")
        
        # Fetch content if requested
        if fetch_content and articles:
            logger.info(f"Fetching content for {len(articles)} articles...")
            for i, article in enumerate(articles):
                logger.info(f"Content [{i+1}/{len(articles)}]: {article['title'][:60]}...")
                content_data = self.fetch_article_content(article['url'])
                article.update(content_data)
        
        self.scraped_data = articles
        return articles
    
    def translate_articles(self, articles, target_lang='en'):
        """Translate articles to target language."""
        try:
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(source='id', target=target_lang)
            logger.info(f"Translator initialized for {target_lang}")
        except ImportError:
            logger.error("deep-translator not installed")
            return []
        
        translated = []
        logger.info(f"Translating {len(articles)} articles to {target_lang}...")
        
        for i, article in enumerate(articles):
            logger.info(f"Translating [{i+1}/{len(articles)}]: {article['title'][:50]}...")
            
            try:
                trans_article = article.copy()
                
                # Translate fields
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
                
                if article.get('author'):
                    trans_article['author'] = translator.translate(article['author'])
                    trans_article['author_original'] = article['author']
                
                trans_article['translated_at'] = datetime.now().isoformat()
                trans_article['translation_source'] = 'id'
                trans_article['translation_target'] = target_lang
                
                translated.append(trans_article)
                
                import time
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Translation error: {e}")
                translated.append(article)
        
        return translated
    
    def save_data(self, data, filename):
        """Save data to JSON file in output directory."""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Saved {len(data)} articles to {filepath}")
        return filepath
    
    def generate_report(self, articles, articles_en=None, articles_th=None):
        """Generate a summary report."""
        report = []
        report.append("=" * 60)
        report.append("BISNIS.COM SCRAPER TEST REPORT")
        report.append("=" * 60)
        report.append(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Days Back: {self.days_back}")
        report.append(f"Base URL: {self.base_url}")
        report.append(f"Output Directory: {self.output_dir}")
        report.append("")
        report.append("RESULTS:")
        report.append(f"  - Articles scraped: {len(articles)}")
        
        if articles:
            # Calculate statistics
            channels = {}
            word_counts = []
            for art in articles:
                ch = art.get('channel', 'Unknown')
                channels[ch] = channels.get(ch, 0) + 1
                if art.get('word_count'):
                    word_counts.append(art['word_count'])
            
            report.append(f"  - Unique channels: {len(channels)}")
            report.append("  - Top channels:")
            for ch, count in sorted(channels.items(), key=lambda x: x[1], reverse=True)[:5]:
                report.append(f"      {ch}: {count}")
            
            if word_counts:
                report.append(f"  - Total words: {sum(word_counts):,}")
                report.append(f"  - Average words/article: {sum(word_counts)/len(word_counts):.0f}")
        
        if articles_en:
            report.append(f"  - English translations: {len(articles_en)}")
        
        if articles_th:
            report.append(f"  - Thai translations: {len(articles_th)}")
        
        report.append("")
        report.append("OUTPUT FILES:")
        for f in os.listdir(self.output_dir):
            filepath = os.path.join(self.output_dir, f)
            size = os.path.getsize(filepath)
            report.append(f"  - {f} ({size:,} bytes)")
        
        report.append("")
        report.append("SAMPLE ARTICLES:")
        for i, art in enumerate(articles[:3]):
            report.append(f"\n{i+1}. {art['title']}")
            report.append(f"   Channel: {art.get('channel', 'N/A')}")
            report.append(f"   Date: {art.get('date', 'N/A')}")
            report.append(f"   Word count: {art.get('word_count', 0)}")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)


def main():
    """Main test function."""
    print("\n" + "=" * 60)
    print("BISNIS.COM SCRAPER - TEST RUN")
    print("=" * 60 + "\n")
    
    # Initialize scraper
    scraper = BisnisScraperTest(
        days_back=1,
        output_dir='test_results'
    )
    
    # Run scraping with content
    articles = scraper.scrape(fetch_content=True)
    
    if not articles:
        print("ERROR: No articles found!")
        return
    
    # Save original data
    scraper.save_data(articles, 'news_data.json')
    
    # Translate to English
    articles_en = scraper.translate_articles(articles, target_lang='en')
    scraper.save_data(articles_en, 'news_data_translated_en.json')
    
    # Translate to Thai
    articles_th = scraper.translate_articles(articles, target_lang='th')
    scraper.save_data(articles_th, 'news_data_translated_th.json')
    
    # Generate report
    report = scraper.generate_report(articles, articles_en, articles_th)
    
    # Save report
    report_path = os.path.join(scraper.output_dir, 'test_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Print report
    print("\n" + report)
    
    print(f"\n✓ Test completed successfully!")
    print(f"✓ Results saved to: {scraper.output_dir}/")


if __name__ == '__main__':
    main()
