"""
Article Scraper Agent
Scrapes full article content from news URLs
"""

import time
import random
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict

from .config import Config


class ArticleScraperAgent:
    """Agent to scrape full article content"""
    
    def __init__(self, delay_min: int = None, delay_max: int = None, max_retries: int = None):
        self.delay_min = delay_min or Config.REQUEST_DELAY_MIN
        self.delay_max = delay_max or Config.REQUEST_DELAY_MAX
        self.max_retries = max_retries or Config.MAX_RETRIES
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
    
    def scrape_article(self, url: str) -> Optional[Dict]:
        """
        Scrape full article content from URL
        
        Args:
            url: Article URL to scrape
            
        Returns:
            Dict with content and metadata or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, "lxml")
                
                result = {
                    "content": self._extract_content(soup),
                    "summary": self._extract_summary(soup),
                    "author": self._extract_author(soup),
                }
                
                # Delay to be respectful
                time.sleep(random.uniform(self.delay_min, self.delay_max))
                
                return result
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(random.uniform(self.delay_min, self.delay_max) * (attempt + 1))
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract full article content"""
        # Try content selectors
        content_selectors = [
            ".article-content",
            ".post-content",
            ".entry-content",
            ".content-body",
            "article .content",
            ".article-body",
            ".detail-text",
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                # Remove script and style tags
                for script in element.find_all(["script", "style"]):
                    script.decompose()
                
                # Get all paragraphs
                paragraphs = element.find_all("p")
                if paragraphs:
                    return "\n\n".join(p.get_text(strip=True) for p in paragraphs)
        
        # Fallback
        main_content = soup.select_one("main") or soup.select_one("article")
        if main_content:
            paragraphs = main_content.find_all("p")
            return "\n\n".join(p.get_text(strip=True) for p in paragraphs)
        
        return ""
    
    def _extract_summary(self, soup: BeautifulSoup) -> str:
        """Extract article summary (first 2-3 paragraphs)"""
        content = self._extract_content(soup)
        paragraphs = content.split("\n\n")
        
        # Return first 2-3 paragraphs as summary
        summary_paragraphs = paragraphs[:3]
        return "\n\n".join(summary_paragraphs)
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract author information"""
        selectors = [
            ".author",
            "[class*='author']",
            "[rel='author']",
            ".byline",
            ".writer",
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return ""
