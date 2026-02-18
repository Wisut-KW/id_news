"""
Article Scraper Agent
Scrapes full article content from news URLs
"""

import re
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
                # Try regular URL first
                response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, "lxml")
                
                content = self._extract_content(soup)
                
                # If no content found, try AMP version
                if not content or len(content) < 100:
                    amp_url = url + ("?" if "?" not in url else "&") + "outputType=amp"
                    amp_response = self.session.get(amp_url, timeout=Config.REQUEST_TIMEOUT)
                    amp_response.raise_for_status()
                    amp_soup = BeautifulSoup(amp_response.content, "lxml")
                    content = self._extract_amp_content(amp_soup)
                
                result = {
                    "content": content,
                    "summary": self._extract_summary_from_content(content),
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
        return self._extract_summary_from_content(content)

    def _extract_summary_from_content(self, content: str) -> str:
        """Extract article summary from content string"""
        paragraphs = content.split("\n\n")

        # Return first 2-3 paragraphs as summary
        summary_paragraphs = paragraphs[:3]
        return "\n\n".join(summary_paragraphs)

    def _extract_amp_content(self, soup: BeautifulSoup) -> str:
        """Extract content from AMP version of the page"""
        # Get all text from the page
        text = soup.get_text(separator='\n', strip=True)

        # Clean up the text by removing navigation elements
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        # Filter out navigation/menu items (short lines that look like menu items)
        content_lines = []
        skip_patterns = [
            'Your browser is out of date', 'Please Update your browser',
            'A list of the most popular web browsers', 'Just click on the icons',
            'press enter to search', 'LOG IN', 'REGISTER', 'Subscribe',
            'Search', 'Close', 'Home', 'News', 'Business', 'World', 'Opinion',
            'Politics', 'Jakarta', 'Society', 'Archipelago', 'Economy',
            'Tech', 'Companies', 'Regulations', 'Markets', 'LOGIN',
            'Multimedia', 'Index', 'Video', 'Photo', 'Travel', 'Sports',
            'Newsletter', 'Mobile Apps', 'The Jakarta Post Group',
            "Can't find what you're looking for", 'View all search results',
            'Popular Reads', 'Top Results', 'No results found',
            'Share this article', 'Related', 'Read also', 'More in'
        ]

        for line in lines:
            # Skip short lines that are likely navigation
            if len(line) < 30 and not line.endswith('.'):
                continue
            # Skip lines containing skip patterns
            if any(pattern in line for pattern in skip_patterns):
                continue
            # Skip common navigation/menu text (exact match)
            if line in ['Home', 'News', 'Business', 'World', 'Opinion', 'Culture',
                       'Politics', 'Jakarta', 'Society', 'Archipelago', 'Economy',
                       'Tech', 'Companies', 'Regulations', 'Markets', 'LOGIN',
                       'Subscribe', 'Search', 'Close', 'Multimedia', 'Index',
                       'Video', 'Photo', 'Travel', 'Sports', 'Newsletter']:
                continue
            content_lines.append(line)

        # Join lines and look for article content pattern
        full_text = '\n'.join(content_lines)

        # Try to extract article content - usually starts after the title
        # and continues until "Related" or "Read also"
        article_patterns = [
            r'([A-Z][^.]{20,500}?[.].{100,})(?:Related|Read also|Share this|©|All rights reserved|More in)',
            r'([A-Z][^.]{50,}?[.].{200,})(?:\n\n[A-Z]|Related|Read also)',
        ]

        for pattern in article_patterns:
            match = re.search(pattern, full_text, re.DOTALL)
            if match:
                content = match.group(1).strip()
                if len(content) > 200:
                    return content

        # Fallback: return all substantial content lines
        substantial_lines = [l for l in content_lines if len(l) > 50]
        return '\n\n'.join(substantial_lines[:20])
    
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
