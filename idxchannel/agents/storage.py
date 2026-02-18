"""
Storage Agent
Saves processed articles to JSON with append/merge support
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Set


class StorageAgent:
    """Agent to store processed articles with merge support"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def save(self, articles: List[Dict]) -> str:
        """
        Save articles to JSON file, merging with existing data
        
        Args:
            articles: List of processed article dicts
            
        Returns:
            Path to saved file
        """
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"{today}_idxchannel.json"
        filepath = os.path.join(self.data_dir, filename)
        
        # Add processing timestamp to new articles
        for article in articles:
            if "processed_at" not in article:
                article["processed_at"] = datetime.now().isoformat()
        
        # Load existing data if file exists
        existing_articles = []
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    existing_articles = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load existing file: {e}")
        
        # Merge articles, avoiding duplicates by URL
        merged_articles = self._merge_articles(existing_articles, articles)
        
        # Save merged data
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(merged_articles, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def _merge_articles(self, existing: List[Dict], new: List[Dict]) -> List[Dict]:
        """
        Merge existing and new articles, avoiding duplicates
        
        Args:
            existing: List of existing articles
            new: List of new articles
            
        Returns:
            Merged list with no duplicates
        """
        # Create a set of existing URLs for quick lookup
        existing_urls: Set[str] = set()
        for article in existing:
            url = article.get("url", "")
            if url:
                existing_urls.add(url)
        
        # Start with existing articles
        merged = existing.copy()
        
        # Add new articles that don't already exist
        added_count = 0
        for article in new:
            url = article.get("url", "")
            if url and url not in existing_urls:
                merged.append(article)
                existing_urls.add(url)
                added_count += 1
            elif not url:
                # Article without URL, add it anyway
                merged.append(article)
                added_count += 1
        
        print(f"  Merged: {len(existing)} existing + {len(new)} new = {len(merged)} total ({added_count} new added)")
        
        return merged
    
    def load(self, filename: str) -> List[Dict]:
        """
        Load articles from JSON file
        
        Args:
            filename: Name of file to load
            
        Returns:
            List of article dicts
        """
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def get_stats(self, filename: str) -> Dict:
        """
        Get statistics about stored articles
        
        Args:
            filename: Name of file to check
            
        Returns:
            Dict with statistics
        """
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            return {
                "exists": False,
                "total_articles": 0,
                "negative_articles": 0
            }
        
        articles = self.load(filename)
        negative_count = sum(1 for a in articles if a.get("is_negative", False))
        
        return {
            "exists": True,
            "total_articles": len(articles),
            "negative_articles": negative_count,
            "file_size_kb": os.path.getsize(filepath) / 1024
        }
