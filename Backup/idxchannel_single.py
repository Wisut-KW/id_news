#!/usr/bin/env python3
"""
Indonesia Local News Negative Event Detection System
Combined single-file implementation

This module provides a complete pipeline for:
1. Fetching RSS feeds from Antara News
2. Scraping full article content
3. Cleaning and normalizing text
4. Detecting negative news events
5. Storing results in JSON format
6. Logging errors
"""

import os
import sys
import re
import json
import time
import unicodedata
from datetime import datetime
from typing import List, Dict, Optional

# External dependencies
try:
    import feedparser
    import requests
    from bs4 import BeautifulSoup
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please install: pip install feedparser requests beautifulsoup4 lxml vaderSentiment")
    sys.exit(1)


# =============================================================================
# CONFIGURATION
# =============================================================================

class Config:
    """Configuration settings for the pipeline"""
    RSS_URL = "https://en.antaranews.com/rss/news"
    DATA_DIR = "data"
    LOGS_DIR = "logs"
    DELAY_SECONDS = 2.0
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 30
    SENTIMENT_THRESHOLD = -0.3
    KEYWORD_THRESHOLD = 2
    MIN_CONTENT_LENGTH = 100


# =============================================================================
# AGENT 1: RSS INGESTION
# =============================================================================

class RSSIngestionAgent:
    """Agent to fetch and parse RSS feeds"""
    
    def __init__(self, rss_url: str = Config.RSS_URL):
        self.rss_url = rss_url
    
    def fetch_feed(self) -> List[Dict]:
        """
        Fetch and parse RSS feed, return list of article metadata
        
        Returns:
            List of dicts with: title, url, published_date, summary
        """
        feed = feedparser.parse(self.rss_url)
        articles = []
        
        for entry in feed.entries:
            article = {
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "published_date": self._parse_date(entry.get("published", "")),
                "summary": entry.get("summary", ""),
            }
            articles.append(article)
        
        return articles
    
    def filter_today_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Filter articles to only include those published today
        
        Args:
            articles: List of article metadata
            
        Returns:
            Filtered list of today's articles
        """
        today = datetime.now().strftime("%Y-%m-%d")
        return [article for article in articles if article["published_date"] == today]
    
    def _parse_date(self, date_str) -> str:
        """
        Parse RSS date string to YYYY-MM-DD format
        
        Args:
            date_str: Date string from RSS feed
            
        Returns:
            Date in YYYY-MM-DD format
        """
        if not date_str:
            return ""
        
        # Handle list case from feedparser
        if isinstance(date_str, list):
            date_str = date_str[0] if date_str else ""
        
        try:
            # Common RSS date formats
            for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z"]:
                try:
                    parsed = datetime.strptime(date_str, fmt)
                    return parsed.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            
            # Try with UTC offset variations
            cleaned = date_str.replace("GMT", "+0000").replace("UTC", "+0000")
            for fmt in ["%a, %d %b %Y %H:%M:%S %z"]:
                try:
                    parsed = datetime.strptime(cleaned, fmt)
                    return parsed.strftime("%Y-%m-%d")
                except ValueError:
                    continue
        except Exception:
            pass
        
        return ""


# =============================================================================
# AGENT 2: ARTICLE SCRAPER
# =============================================================================

class ArticleScraperAgent:
    """Agent to scrape full article content"""
    
    def __init__(self, delay: float = Config.DELAY_SECONDS, 
                 max_retries: int = Config.MAX_RETRIES):
        self.delay = delay
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def scrape_article(self, url: str) -> Optional[str]:
        """
        Scrape full article content from URL
        
        Args:
            url: Article URL to scrape
            
        Returns:
            Full article text or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, "lxml")
                content = self._extract_content(soup)
                
                # Delay to be respectful
                time.sleep(self.delay)
                
                return content
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(self.delay * (attempt + 1))
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """
        Extract article content from BeautifulSoup object
        
        Args:
            soup: Parsed HTML
            
        Returns:
            Extracted text content
        """
        # Try to find article content in common containers
        selectors = [
            "article",
            ".article-content",
            ".post-content",
            ".entry-content",
            "[class*='content']",
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                paragraphs = element.find_all("p")
                if paragraphs:
                    return "\n\n".join(p.get_text(strip=True) for p in paragraphs)
        
        # Fallback: extract all paragraphs
        paragraphs = soup.find_all("p")
        return "\n\n".join(p.get_text(strip=True) for p in paragraphs)


# =============================================================================
# AGENT 3: TEXT CLEANING
# =============================================================================

class TextCleaningAgent:
    """Agent to clean and normalize text content"""
    
    def clean(self, text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Normalize unicode
        text = unicodedata.normalize("NFKD", text)
        
        # Remove "ANTARA -" prefix
        text = re.sub(r'^ANTARA\s*[-–—]\s*', '', text, flags=re.IGNORECASE)
        
        # Remove HTML artifacts
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove scripts and style content
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def clean_article(self, article: dict) -> dict:
        """
        Clean all text fields in an article
        
        Args:
            article: Article dict with text fields
            
        Returns:
            Article with cleaned text fields
        """
        cleaned = article.copy()
        
        if "title" in cleaned:
            cleaned["title"] = self.clean(cleaned["title"])
        
        if "summary" in cleaned:
            cleaned["summary"] = self.clean(cleaned["summary"])
        
        if "content" in cleaned:
            cleaned["content"] = self.clean(cleaned["content"])
        
        return cleaned


# =============================================================================
# AGENT 4: NEGATIVE NEWS DETECTION
# =============================================================================

class NegativeNewsDetectionAgent:
    """Agent to detect negative news events"""
    
    # Negative keyword categories
    KEYWORDS = {
        "natural_disasters": [
            "earthquake", "flood", "tsunami", "volcanic eruption", "landslide",
            "cyclone", "hurricane", "typhoon", "tornado", "drought", "wildfire"
        ],
        "crime": [
            "arrested", "murder", "corruption", "theft", "robbery", "assault",
            "fraud", "bribery", "kidnapping", "drug trafficking", "smuggling"
        ],
        "accident": [
            "crash", "explosion", "fire", "collision", "derailment", "sinking",
            "capsize", "wreck", "pile-up", "accident"
        ],
        "health": [
            "outbreak", "virus", "epidemic", "pandemic", "disease", "infection",
            "contamination", "poisoning", "fatal", "death toll"
        ],
        "conflict": [
            "protest", "violence", "riot", "clash", "demonstration", "unrest",
            "conflict", "attack", "bombing", "shooting", "hostage"
        ],
        "economic_distress": [
            "bankruptcy", "inflation", "recession", "crisis", "collapse",
            "unemployment", "layoffs", "shutdown", "default"
        ]
    }
    
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
    
    def analyze(self, text: str) -> Dict:
        """
        Analyze text for negative content
        
        Args:
            text: Article text to analyze
            
        Returns:
            Dict with negative_score, sentiment_score, is_negative
        """
        keyword_score = self._calculate_keyword_score(text)
        sentiment_score = self._calculate_sentiment_score(text)
        is_negative = self._determine_negative(keyword_score, sentiment_score)
        
        return {
            "negative_score": keyword_score,
            "sentiment_score": sentiment_score,
            "is_negative": is_negative
        }
    
    def _calculate_keyword_score(self, text: str) -> int:
        """
        Count negative keyword occurrences
        
        Args:
            text: Text to analyze
            
        Returns:
            Total keyword count
        """
        text_lower = text.lower()
        score = 0
        
        for category, keywords in self.KEYWORDS.items():
            for keyword in keywords:
                # Use word boundaries for better matching
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                matches = re.findall(pattern, text_lower)
                score += len(matches)
        
        return score
    
    def _calculate_sentiment_score(self, text: str) -> float:
        """
        Calculate sentiment score using VADER
        
        Args:
            text: Text to analyze
            
        Returns:
            Compound sentiment score (-1 to 1)
        """
        scores = self.analyzer.polarity_scores(text)
        return scores["compound"]
    
    def _determine_negative(self, keyword_score: int, sentiment_score: float) -> bool:
        """
        Determine if article is negative based on scores
        
        Args:
            keyword_score: Count of negative keywords
            sentiment_score: VADER compound sentiment score
            
        Returns:
            True if article is negative
        """
        return keyword_score >= Config.KEYWORD_THRESHOLD or sentiment_score < Config.SENTIMENT_THRESHOLD


# =============================================================================
# AGENT 5: STORAGE
# =============================================================================

class StorageAgent:
    """Agent to store processed articles"""
    
    def __init__(self, data_dir: str = Config.DATA_DIR):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def save(self, articles: List[Dict]) -> str:
        """
        Save articles to JSON file
        
        Args:
            articles: List of processed article dicts
            
        Returns:
            Path to saved file
        """
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"{today}_antaranews.json"
        filepath = os.path.join(self.data_dir, filename)
        
        # Add processing timestamp
        for article in articles:
            article["processed_at"] = datetime.now().isoformat()
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def load(self, filename: str) -> List[Dict]:
        """
        Load articles from JSON file
        
        Args:
            filename: Name of file to load
            
        Returns:
            List of article dicts
        """
        filepath = os.path.join(self.data_dir, filename)
        
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)


# =============================================================================
# AGENT 6: LOGGING
# =============================================================================

class LoggingAgent:
    """Agent to log errors and events"""
    
    def __init__(self, logs_dir: str = Config.LOGS_DIR):
        self.logs_dir = logs_dir
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create log file for today
        today = datetime.now().strftime("%Y-%m-%d")
        self.log_file = os.path.join(logs_dir, f"{today}_errors.log")
    
    def log_error(self, url: str, error_message: str) -> None:
        """
        Log an error with URL
        
        Args:
            url: URL that caused the error
            error_message: Error description
        """
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} | {url} | {error_message}\n"
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    
    def log_info(self, message: str) -> None:
        """
        Log an info message
        
        Args:
            message: Info message to log
        """
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} | INFO | {message}\n"
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def run_pipeline():
    """
    Run the complete news processing pipeline
    
    Flow:
    1. Fetch RSS feed
    2. Filter today's articles
    3. Scrape full content
    4. Clean text
    5. Detect negative news
    6. Save results
    7. Log errors
    """
    # Initialize agents
    rss_agent = RSSIngestionAgent()
    scraper_agent = ArticleScraperAgent()
    cleaning_agent = TextCleaningAgent()
    detection_agent = NegativeNewsDetectionAgent()
    storage_agent = StorageAgent()
    logger = LoggingAgent()
    
    logger.log_info("Starting news pipeline")
    
    try:
        # Step 1: Fetch RSS feed
        logger.log_info("Fetching RSS feed")
        articles = rss_agent.fetch_feed()
        logger.log_info(f"Fetched {len(articles)} articles from RSS")
        
        # Step 2: Filter today's articles
        today_articles = rss_agent.filter_today_articles(articles)
        logger.log_info(f"Found {len(today_articles)} articles from today")
        
        if not today_articles:
            logger.log_info("No articles to process today")
            print("No articles found for today")
            return
        
        # Step 3-5: Process each article
        processed_articles = []
        
        for i, article in enumerate(today_articles):
            url = article.get("url", "")
            title = article.get("title", "Unknown")
            
            logger.log_info(f"Processing article {i+1}/{len(today_articles)}: {title[:50]}...")
            print(f"[{i+1}/{len(today_articles)}] Processing: {title[:60]}...")
            
            # Scrape full content
            content = scraper_agent.scrape_article(url)
            
            if content is None:
                logger.log_error(url, "Failed to scrape article content")
                print(f"  ✗ Failed to scrape")
                continue
            
            # Add content to article
            article["content"] = content
            
            # Clean text
            article = cleaning_agent.clean_article(article)
            
            # Skip empty content
            if not article["content"] or len(article["content"]) < Config.MIN_CONTENT_LENGTH:
                logger.log_error(url, "Article content too short or empty")
                print(f"  ✗ Content too short")
                continue
            
            # Detect negative news
            analysis = detection_agent.analyze(article["content"])
            article.update(analysis)
            
            processed_articles.append(article)
            status = "⚠ NEGATIVE" if analysis["is_negative"] else "✓ OK"
            print(f"  {status} (score: {analysis['negative_score']}, sentiment: {analysis['sentiment_score']:.2f})")
            logger.log_info(f"Processed: {title[:50]}... (Negative: {analysis['is_negative']})")
        
        # Step 6: Save results
        if processed_articles:
            output_path = storage_agent.save(processed_articles)
            logger.log_info(f"Saved {len(processed_articles)} articles to {output_path}")
            
            # Print summary
            negative_count = sum(1 for a in processed_articles if a["is_negative"])
            print(f"\n{'='*60}")
            print(f"PIPELINE COMPLETE")
            print(f"{'='*60}")
            print(f"Total articles processed: {len(processed_articles)}")
            print(f"Negative articles detected: {negative_count}")
            print(f"Output saved to: {output_path}")
            print(f"{'='*60}\n")
        else:
            logger.log_info("No articles were successfully processed")
            print("\nNo articles were successfully processed")
        
    except Exception as e:
        logger.log_error("pipeline", str(e))
        print(f"\nERROR: {e}")
        raise


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    run_pipeline()
