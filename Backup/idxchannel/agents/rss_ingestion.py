"""
RSS Ingestion Agent
Fetches and parses RSS feed from Antara News
"""

import feedparser
from datetime import datetime
from typing import List, Dict


class RSSIngestionAgent:
    """Agent to fetch and parse RSS feeds"""
    
    def __init__(self, rss_url: str = "https://en.antaranews.com/rss/news"):
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
