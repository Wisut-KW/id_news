#!/usr/bin/env python3
"""
Quick test script - Scrape 5 articles only for demo
"""

import json
import logging
import os
import re
import ssl
import gzip
import urllib.request
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def fetch_url(url, timeout=30):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_context) as response:
            content = response.read()
            if response.info().get('Content-Encoding') == 'gzip':
                content = gzip.decompress(content)
            return content.decode('utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"Error: {e}")
        return None

def main():
    print("\n" + "=" * 60)
    print("QUICK TEST - Bisnis.com Notebook Demo")
    print("=" * 60 + "\n")
    
    os.makedirs('test_results', exist_ok=True)
    
    # Scrape first page only
    url = "https://www.bisnis.com/index?categoryId=43&page=1"
    print(f"Fetching: {url}")
    
    html = fetch_url(url)
    if not html:
        print("Failed to fetch")
        return
    
    soup = BeautifulSoup(html, 'html.parser')
    art_items = soup.find_all('div', class_='artItem')
    print(f"Found {len(art_items)} articles\n")
    
    # Extract first 5 articles
    articles = []
    pattern = re.compile(r'/read/(\d{8})/(\d+)/(\d+)/')
    
    for elem in art_items[:5]:
        link = elem.find('a', href=True, class_='artLink') or elem.find('a', href=True)
        if not link:
            continue
        
        art_url = link['href']
        if not art_url.startswith('http'):
            art_url = "https://www.bisnis.com" + art_url
        
        if not pattern.search(art_url):
            continue
        
        title_elem = elem.find('h4', class_='artTitle') or link
        title = title_elem.get_text(strip=True) if title_elem else "No title"
        
        match = re.search(r'/read/(\d{4})(\d{2})(\d{2})', art_url)
        date = f"{match.group(1)}-{match.group(2)}-{match.group(3)}" if match else ""
        
        channel_elem = elem.find('div', class_='artChannel')
        channel = channel_elem.get_text(strip=True) if channel_elem else ""
        
        articles.append({
            'title': title,
            'url': art_url,
            'date': date,
            'channel': channel
        })
    
    print(f"Extracted {len(articles)} articles:\n")
    for i, art in enumerate(articles, 1):
        print(f"{i}. {art['title']}")
        print(f"   Channel: {art['channel']}")
        print(f"   URL: {art['url']}")
        print()
    
    # Save
    output_file = 'test_results/quick_test.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved to {output_file}")
    print(f"✓ Test completed successfully!\n")

if __name__ == '__main__':
    main()
