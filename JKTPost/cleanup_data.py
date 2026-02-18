#!/usr/bin/env python3
"""
Clean existing JSON data by:
1. Removing duplicate URLs (keeping only the first occurrence)
2. Filtering out category/listing pages (URLs that end with /business/* paths without article dates)
3. Normalizing all URLs to https:// format
"""

import json
import os
from urllib.parse import urlparse

def is_article_url(url: str) -> bool:
    """
    Check if URL is an actual article (not a category page)
    Article URLs should have date patterns like /YYYY/MM/DD/ in the path
    """
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    # Category pages to exclude
    category_patterns = [
        '/business/economy',
        '/business/companies',
        '/business/tech',
        '/business/regulations',
        '/business/markets',
        '/index.php/business/economy',
        '/index.php/business/companies',
        '/index.php/business/tech',
        '/index.php/business/regulations',
        '/index.php/business/markets',
    ]
    
    # Check if it's a category page (ends with category path or has no date in path)
    for pattern in category_patterns:
        if path.rstrip('/').endswith(pattern.rstrip('/')):
            return False
    
    # Check if URL contains date pattern (YYYY/MM/DD)
    import re
    date_pattern = r'/\d{4}/\d{2}/\d{2}/'
    if re.search(date_pattern, path):
        return True
    
    # If no date pattern, it's likely a category or non-article page
    return False

def normalize_url(url: str) -> str:
    """
    Normalize URL by:
    - Converting http to https
    - Handling www subdomain consistently
    - Removing trailing slashes
    """
    parsed = urlparse(url)
    
    # Convert to https
    scheme = 'https'
    
    # Handle www - always use www for consistency
    netloc = parsed.netloc.lower()
    if netloc == 'thejakartapost.com':
        netloc = 'www.thejakartapost.com'
    
    # Remove trailing slashes from path
    path = parsed.path.rstrip('/') if parsed.path else '/'
    
    # Rebuild URL without query params for comparison (but keep original for storage)
    from urllib.parse import urlunparse
    normalized = urlunparse((scheme, netloc, path, '', '', ''))
    
    return normalized

def clean_data(filepath: str):
    """Clean the JSON data file"""
    print(f"Cleaning data file: {filepath}")
    
    # Load existing data
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    print(f"Total articles before cleaning: {len(articles)}")
    
    # Track unique URLs
    seen_urls = set()
    unique_articles = []
    skipped_categories = 0
    skipped_duplicates = 0
    
    for article in articles:
        url = article.get('url', '')
        if not url:
            continue
        
        # Check if it's an article URL (not category page)
        if not is_article_url(url):
            skipped_categories += 1
            continue
        
        # Normalize URL for deduplication
        normalized_url = normalize_url(url)
        
        # Skip if we've seen this URL before
        if normalized_url in seen_urls:
            skipped_duplicates += 1
            continue
        
        # Update article URL to normalized version
        article['url'] = normalized_url
        seen_urls.add(normalized_url)
        unique_articles.append(article)
    
    print(f"Skipped category pages: {skipped_categories}")
    print(f"Skipped duplicate URLs: {skipped_duplicates}")
    print(f"Total unique articles after cleaning: {len(unique_articles)}")
    
    # Save cleaned data
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(unique_articles, f, indent=2, ensure_ascii=False)
    
    print(f"Cleaned data saved to: {filepath}")
    return len(unique_articles)

if __name__ == "__main__":
    data_file = os.path.join('data', 'jakartapost_business.json')
    clean_data(data_file)
