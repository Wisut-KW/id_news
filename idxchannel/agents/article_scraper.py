"""
Article Scraper Agent
Scrapes full article content from news URLs
"""

import time
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict


class ArticleScraperAgent:
    """Agent to scrape full article content"""
    
    def __init__(self, delay: float = 2.0, max_retries: int = 3):
        self.delay = delay
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
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
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, "lxml")
                
                result = {
                    "content": self._extract_content(soup),
                    "author": self._extract_author(soup),
                    "published_date": self._extract_date(soup),
                }
                
                # Delay to be respectful
                time.sleep(self.delay)
                
                return result
                
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
            "article .content",
            ".article-content",
            ".post-content",
            ".entry-content",
            "[class*='article-body']",
            "[class*='content-body']",
            ".detail-text",
            ".read-content",
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                paragraphs = element.find_all("p")
                if paragraphs:
                    return "\n\n".join(p.get_text(strip=True) for p in paragraphs)
        
        # Fallback: extract all paragraphs from main content area
        main_content = soup.select_one("main") or soup.select_one("[role='main']") or soup.select_one(".content")
        if main_content:
            paragraphs = main_content.find_all("p")
            if paragraphs:
                return "\n\n".join(p.get_text(strip=True) for p in paragraphs)
        
        # Final fallback: all paragraphs
        paragraphs = soup.find_all("p")
        return "\n\n".join(p.get_text(strip=True) for p in paragraphs)
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """
        Extract author information
        
        Args:
            soup: Parsed HTML
            
        Returns:
            Author name or empty string
        """
        selectors = [
            ".author",
            "[class*='author']",
            "[rel='author']",
            ".byline",
            "[class*='byline']",
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return ""
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """
        Extract published date from article page
        
        Args:
            soup: Parsed HTML
            
        Returns:
            Date string or empty string
        """
        # Look for time element
        time_elem = soup.find("time")
        if time_elem:
            datetime_attr = time_elem.get("datetime", "")
            if datetime_attr:
                if isinstance(datetime_attr, list):
                    datetime_attr = datetime_attr[0] if datetime_attr else ""
                return str(datetime_attr)[:10]  # YYYY-MM-DD
            return time_elem.get_text(strip=True)
        
        # Look for date elements
        selectors = [
            ".date",
            ".published",
            "[class*='date']",
            "[class*='published']",
            "[class*='time']",
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return ""
