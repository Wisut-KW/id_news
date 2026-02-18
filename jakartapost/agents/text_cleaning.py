"""
Text Cleaning Agent
Cleans and normalizes article text
"""

import re
import unicodedata


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
        
        # Remove HTML artifacts
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
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
        
        if "author" in cleaned:
            cleaned["author"] = self.clean(cleaned["author"])
        
        return cleaned
