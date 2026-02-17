# Indonesia Local News Negative Event Detection System
"""
Complete pipeline to:
1. Fetch RSS feed from Antara News
2. Scrape full article content
3. Detect negative news using keywords and sentiment analysis
4. Store enriched structured data
"""

# Cell 1: Import Libraries
import requests
import feedparser
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
from datetime import datetime, date
from dateutil import parser as date_parser
import time
import re
import unicodedata
from typing import List, Dict, Optional

# Cell 2: Configuration Variables
RSS_URL = "https://en.antaranews.com/rss/news"
DATA_DIR = "data"
LOGS_DIR = "logs"
REQUEST_DELAY = 2
MAX_RETRIES = 3
TODAY = date.today().isoformat()

NEGATIVE_KEYWORDS = {
    'natural_disaster': [
        'earthquake', 'flood', 'tsunami', 'volcano', 'eruption', 'landslide',
        'avalanche', 'drought', 'storm', 'hurricane', 'typhoon', 'tornado'
    ],
    'crime': [
        'arrested', 'arrest', 'murder', 'killed', 'death', 'dead', 'corruption',
        'bribery', 'fraud', 'theft', 'stolen', 'robbery', 'assault', 'violence',
        'kidnapping', 'drug', 'trafficking', 'smuggling'
    ],
    'accident': [
        'crash', 'collision', 'explosion', 'fire', 'burned', 'injured',
        'wounded', 'casualties', 'wreck', 'derail', 'sinking'
    ],
    'health': [
        'outbreak', 'epidemic', 'pandemic', 'virus', 'disease', 'infection',
        'contamination', 'poisoning', 'fatal', 'died'
    ],
    'conflict': [
        'protest', 'riot', 'clash', 'fighting', 'attack', 'bombing', 'terrorist',
        'hostage', 'siege', 'shooting', 'gunfire', 'unrest'
    ],
    'economic_distress': [
        'bankruptcy', 'bankrupt', 'inflation', 'recession', 'crisis', 'collapse',
        'unemployment', 'layoff', 'default', 'debt', 'losses', 'plunge'
    ]
}l

ALL_NEGATIVE_KEYWORDS = [
    keyword for category in NEGATIVE_KEYWORDS.values() for keyword in category
]

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

print(f"Configuration loaded. Today: {TODAY}")
print(f"Total negative keywords: {len(ALL_NEGATIVE_KEYWORDS)}")

# Cell 3: RSS Ingestion Agent
class RSSIngestionAgent:
    def __init__(self, rss_url: str):
        self.rss_url = rss_url
    
    def fetch_feed(self) -> List[Dict]:
        print(f"Fetching RSS feed from: {self.rss_url}")
        feed = feedparser.parse(self.rss_url)
        
        articles = []
        for entry in feed.entries:
            article = {
                'title': entry.get('title', ''),
                'url': entry.get('link', ''),
                'published_date': self._parse_date(entry.get('published', '')),
                'summary': entry.get('summary', '')
            }
            articles.append(article)
        
        print(f"Total articles fetched: {len(articles)}")
        return articles
    
    def _parse_date(self, date_str: str) -> str:
        try:
            parsed = date_parser.parse(date_str)
            return parsed.date().isoformat()
        except:
            return ''
    
    def filter_today_articles(self, articles: List[Dict]) -> List[Dict]:
        today_str = date.today().isoformat()
        filtered = [
            article for article in articles
            if article['published_date'] == today_str
        ]
        print(f"Articles from today ({today_str}): {len(filtered)}")
        return filtered

# Cell 4: Article Scraper Agent
class ArticleScraperAgent:
    def __init__(self, delay: int = 2, max_retries: int = 3):
        self.delay = delay
        self.max_retries = max_retries
        self.failed_urls = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_article(self, url: str) -> Optional[str]:
        for attempt in range(self.max_retries):
            try:
                time.sleep(self.delay)
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                content = self._extract_content(soup)
                
                if content:
                    return content
                else:
                    print(f"  Warning: No content found for {url}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                print(f"  Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == self.max_retries - 1:
                    self.failed_urls.append((url, str(e)))
                    return None
                time.sleep(self.delay * 2)
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        selectors = [
            'article', '.post-content', '.entry-content', '.article-content',
            '.content', '[itemprop="articleBody"]', '.post', '.news-content'
        ]
        
        for selector in selectors:
            content_div = soup.select_one(selector)
            if content_div:
                paragraphs = content_div.find_all('p')
                if paragraphs:
                    text = ' '.join([p.get_text(strip=True) for p in paragraphs])
                    if len(text) > 100:
                        return text
        
        body = soup.find('body')
        if body:
            paragraphs = body.find_all('p')
            text = ' '.join([p.get_text(strip=True) for p in paragraphs])
            return text
        
        return ''
    
    def scrape_articles(self, articles: List[Dict]) -> List[Dict]:
        print(f"Scraping {len(articles)} articles...")
        enriched_articles = []
        
        for i, article in enumerate(articles, 1):
            print(f"[{i}/{len(articles)}] Scraping: {article['title'][:60]}...")
            content = self.scrape_article(article['url'])
            
            if content:
                article['content'] = content
                enriched_articles.append(article)
        
        print(f"Successfully scraped: {len(enriched_articles)}/{len(articles)}")
        return enriched_articles

# Cell 5: Text Cleaning Agent
class TextCleaningAgent:
    def clean_text(self, text: str) -> str:
        if not text:
            return ''
        
        text = re.sub(r'^ANTARA\s*-\s*', '', text, flags=re.IGNORECASE)
        text = unicodedata.normalize('NFKD', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?;:()-]', '', text)
        text = text.strip()
        
        return text
    
    def clean_articles(self, articles: List[Dict]) -> List[Dict]:
        print(f"Cleaning {len(articles)} articles...")
        
        for article in articles:
            if 'content' in article:
                article['content'] = self.clean_text(article['content'])
            article['title'] = self.clean_text(article['title'])
            article['summary'] = self.clean_text(article['summary'])
        
        print("Text cleaning completed!")
        return articles

# Cell 6: Negative News Detection Agent
class NegativeNewsDetectionAgent:
    def __init__(self, keywords: List[str]):
        self.keywords = [kw.lower() for kw in keywords]
        self.keyword_scores = {}
    
    def detect_negative_keywords(self, text: str) -> tuple:
        text_lower = text.lower()
        matched_keywords = []
        
        for keyword in self.keywords:
            count = text_lower.count(keyword)
            if count > 0:
                matched_keywords.extend([keyword] * count)
        
        keyword_score = len(matched_keywords)
        return keyword_score, matched_keywords
    
    def is_negative(self, keyword_score: int) -> bool:
        return keyword_score >= 2
    
    def analyze_article(self, article: Dict) -> Dict:
        full_text = ' '.join([
            article.get('title', ''),
            article.get('summary', ''),
            article.get('content', '')
        ])
        
        keyword_score, matched_keywords = self.detect_negative_keywords(full_text)
        is_neg = self.is_negative(keyword_score)
        
        article['negative_score'] = keyword_score
        article['is_negative'] = is_neg
        article['matched_keywords'] = matched_keywords
        article['processed_at'] = datetime.now().isoformat()
        
        return article
    
    def analyze_articles(self, articles: List[Dict]) -> List[Dict]:
        print(f"Analyzing {len(articles)} articles for negative content...")
        
        analyzed_articles = []
        negative_count = 0
        
        for article in articles:
            analyzed = self.analyze_article(article)
            analyzed_articles.append(analyzed)
            if analyzed['is_negative']:
                negative_count += 1
        
        print(f"Analysis complete: {negative_count}/{len(articles)} articles marked as negative")
        return analyzed_articles

# Cell 7: Storage & Logging Agents
class StorageAgent:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def save_articles(self, articles: List[Dict], filename: str = None) -> str:
        if filename is None:
            filename = f"{TODAY}_antaranews.json"
        
        filepath = os.path.join(self.data_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(articles)} articles to: {filepath}")
        return filepath


class LoggingAgent:
    def __init__(self, logs_dir: str):
        self.logs_dir = logs_dir
        os.makedirs(logs_dir, exist_ok=True)
        self.log_file = os.path.join(logs_dir, f"{TODAY}_errors.log")
    
    def log_error(self, url: str, error_message: str):
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} | {url} | {error_message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def log_failed_urls(self, failed_urls: List[tuple]):
        if not failed_urls:
            print("No errors to log.")
            return
        
        for url, error in failed_urls:
            self.log_error(url, error)
        
        print(f"Logged {len(failed_urls)} errors to: {self.log_file}")

# Cell 8: Run Complete Pipeline
def run_pipeline():
    print("=" * 60)
    print("INDONESIA LOCAL NEWS NEGATIVE EVENT DETECTION SYSTEM")
    print("=" * 60)
    print(f"Pipeline started at: {datetime.now().isoformat()}\n")
    
    # Step 1: RSS Ingestion
    print("STEP 1: RSS Ingestion")
    print("-" * 40)
    rss_agent = RSSIngestionAgent(RSS_URL)
    all_articles = rss_agent.fetch_feed()
    today_articles = rss_agent.filter_today_articles(all_articles)
    
    if not today_articles:
        print("No articles from today found. Exiting.")
        return
    
    # Step 2: Article Scraping
    print("\nSTEP 2: Article Scraping")
    print("-" * 40)
    scraper_agent = ArticleScraperAgent(delay=REQUEST_DELAY, max_retries=MAX_RETRIES)
    enriched_articles = scraper_agent.scrape_articles(today_articles)
    
    if not enriched_articles:
        print("No articles could be scraped. Exiting.")
        return
    
    # Step 3: Text Cleaning
    print("\nSTEP 3: Text Cleaning")
    print("-" * 40)
    cleaning_agent = TextCleaningAgent()
    cleaned_articles = cleaning_agent.clean_articles(enriched_articles)
    
    # Step 4: Negative News Detection
    print("\nSTEP 4: Negative News Detection")
    print("-" * 40)
    detection_agent = NegativeNewsDetectionAgent(ALL_NEGATIVE_KEYWORDS)
    analyzed_articles = detection_agent.analyze_articles(cleaned_articles)
    
    # Step 5: Storage
    print("\nSTEP 5: Storage")
    print("-" * 40)
    storage_agent = StorageAgent(DATA_DIR)
    output_file = storage_agent.save_articles(analyzed_articles)
    
    # Step 6: Logging
    print("\nSTEP 6: Error Logging")
    print("-" * 40)
    logging_agent = LoggingAgent(LOGS_DIR)
    logging_agent.log_failed_urls(scraper_agent.failed_urls)
    
    # Summary
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED")
    print("=" * 60)
    print(f"Total articles processed: {len(analyzed_articles)}")
    negative_count = sum(1 for a in analyzed_articles if a['is_negative'])
    print(f"Negative articles detected: {negative_count}")
    print(f"Output file: {output_file}")
    print(f"Completed at: {datetime.now().isoformat()}")
    
    return analyzed_articles

if __name__ == "__main__":
    results = run_pipeline()
    
    # Display summary
    if results:
        print("\n" + "=" * 60)
        print("ARTICLE SUMMARY")
        print("=" * 60)
        
        negative_articles = [a for a in results if a['is_negative']]
        if negative_articles:
            print(f"\nNEGATIVE ARTICLES ({len(negative_articles)}):\n")
            for article in negative_articles:
                print(f"Title: {article['title'][:70]}...")
                print(f"  Score: {article['negative_score']} | URL: {article['url'][:60]}...")
                print()
        else:
            print("\nNo negative articles detected today.")
        
        print("\nSTATISTICS")
        print("-" * 40)
        print(f"Total Articles: {len(results)}")
        print(f"Negative Articles: {len(negative_articles)}")
        if results:
            print(f"Negative Percentage: {len(negative_articles)/len(results)*100:.1f}%")
            avg_score = sum(a['negative_score'] for a in results) / len(results)
            print(f"Avg Negative Score: {avg_score:.2f}")