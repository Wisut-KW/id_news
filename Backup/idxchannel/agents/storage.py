"""
Storage Agent
Saves processed articles to JSON
"""

import json
import os
from datetime import datetime
from typing import List, Dict


class StorageAgent:
    """Agent to store processed articles"""
    
    def __init__(self, data_dir: str = "data"):
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
