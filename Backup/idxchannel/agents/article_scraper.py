"""
Article Scraper Agent
Scrapes full article content from news URLs
"""

import time
import requests
from bs4 import BeautifulSoup
from typing import Optional


class ArticleScraperAgent:
    """Agent to scrape full article content"""
    
    def __init__(self, delay: float = 2.0, max_retries: int = 3):
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
                response = self.session.get(url, timeout=30)
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
