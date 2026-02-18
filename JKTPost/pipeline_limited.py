#!/usr/bin/env python3
"""
Jakarta Post Business News Pipeline - Limited Version
Scrapes only 50 news articles per category (200 total max)
"""

import os
import sys
from datetime import datetime

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents import (
    Config,
    JakartaPostListingAgent,
    ArticleScraperAgent,
    TextCleaningAgent,
    NegativeNewsDetectionAgent,
    StorageAgent,
    LoggingAgent,
)


class LimitedListingAgent(JakartaPostListingAgent):
    """Extended listing agent that limits articles per category"""
    
    def fetch_limited_articles(self, limit_per_category: int = 50, max_pages: int = 10) -> list:
        """
        Fetch limited number of articles from each category
        
        Args:
            limit_per_category: Maximum articles per category (default: 50)
            max_pages: Maximum pages to check per category
            
        Returns:
            List of article metadata
        """
        all_articles = []
        
        for category_name, category_url in Config.CATEGORIES.items():
            print(f"\n  Scraping category: {category_name.upper()}")
            category_articles = self._fetch_category_limited(
                category_name, category_url, limit_per_category, max_pages
            )
            all_articles.extend(category_articles)
        
        # Remove duplicates
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                unique_articles.append(article)
        
        return unique_articles
    
    def _fetch_category_limited(self, category_name: str, base_url: str,
                                limit: int, max_pages: int) -> list:
        """
        Fetch limited articles from a single category
        
        Args:
            category_name: Name of the category
            base_url: Base URL for the category
            limit: Maximum articles to fetch
            max_pages: Maximum pages to check
            
        Returns:
            List of article metadata
        """
        category_articles = []
        page = 1
        
        while page <= max_pages and len(category_articles) < limit:
            print(f"    Page {page}...", end=" ")
            
            # Build page URL
            page_url = self._build_page_url(base_url, page)
            
            # Fetch page
            articles = self._fetch_page(page_url, category_name)
            
            if not articles:
                print("No articles found")
                break
            
            # Add articles up to limit
            for article in articles:
                if len(category_articles) < limit:
                    category_articles.append(article)
                else:
                    break
            
            print(f"{len(category_articles)}/{limit} collected")
            
            # Stop if we reached the limit
            if len(category_articles) >= limit:
                print(f"    → Reached limit of {limit} articles")
                break
            
            # Delay between requests
            import random
            import time
            time.sleep(random.uniform(self.delay_min, self.delay_max))
            page += 1
        
        return category_articles


def run_pipeline(limit_per_category: int = 50, max_pages: int = 10):
    """
    Run the Jakarta Post Business pipeline with article limits
    
    Args:
        limit_per_category: Maximum articles per category (default: 50)
        max_pages: Maximum pages to check per category
    """
    # Initialize agents
    listing_agent = LimitedListingAgent()
    scraper_agent = ArticleScraperAgent()
    cleaning_agent = TextCleaningAgent()
    detection_agent = NegativeNewsDetectionAgent()
    storage_agent = StorageAgent()
    logger = LoggingAgent()
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    total_limit = limit_per_category * len(Config.CATEGORIES)
    
    logger.log_info(f"Starting Jakarta Post Business pipeline (limited: {limit_per_category}/category)")
    
    print("="*70)
    print("JAKARTA POST BUSINESS NEWS PIPELINE - LIMITED VERSION")
    print("="*70)
    print(f"Limit: {limit_per_category} articles per category")
    print(f"Categories: {', '.join(Config.CATEGORIES.keys())}")
    print(f"Expected max total: {total_limit} articles")
    print("="*70)
    
    # Show existing stats
    stats = storage_agent.get_stats()
    if stats["exists"]:
        print(f"\n📊 Existing data: {stats['total_articles']} articles ({stats['negative_articles']} negative)")
    
    try:
        # Step 1: Fetch limited articles from all categories
        print(f"\n[1/5] Fetching up to {limit_per_category} articles per category...")
        articles = listing_agent.fetch_limited_articles(limit_per_category, max_pages)
        logger.log_info(f"Found {len(articles)} articles total")
        print(f"\n  Total articles collected: {len(articles)}")
        
        if not articles:
            logger.log_info("No articles found")
            print("\nNo articles found")
            return
        
        # Show breakdown by category
        from collections import Counter
        category_counts = Counter(a.get("category", "unknown") for a in articles)
        print("\n  Breakdown by category:")
        for cat, count in sorted(category_counts.items()):
            print(f"    - {cat}: {count} articles")
        
        # Step 2: Scrape full content
        print(f"\n[2/5] Scraping full article content...")
        scraped_articles = []
        skipped_count = 0
        
        for i, article in enumerate(articles):
            url = article.get("url", "")
            title = article.get("title", "Unknown")
            category = article.get("category", "unknown")
            
            print(f"  [{i+1}/{len(articles)}] [{category}] {title[:50]}...")
            
            scraped_data = scraper_agent.scrape_article(url)
            
            if scraped_data is None:
                logger.log_error(category, url, "Failed to scrape article content")
                print(f"    ✗ Failed to scrape")
                skipped_count += 1
                continue
            
            # Merge data
            article["content"] = scraped_data["content"]
            article["summary"] = scraped_data["summary"]
            if scraped_data["author"]:
                article["author"] = scraped_data["author"]
            
            scraped_articles.append(article)
        
        print(f"\n  Scraped: {len(scraped_articles)} successful, {skipped_count} failed")
        
        if not scraped_articles:
            logger.log_info("No articles were successfully scraped")
            print("\nNo articles could be scraped")
            return
        
        # Step 3-4: Process articles
        processed_articles = []
        
        print(f"\n[3-4/5] Processing {len(scraped_articles)} articles...")
        
        for i, article in enumerate(scraped_articles):
            url = article.get("url", "")
            title = article.get("title", "Unknown")
            category = article.get("category", "unknown")
            
            print(f"\n  [{i+1}/{len(scraped_articles)}] [{category}] {title[:50]}...")
            
            # Step 3: Clean text
            article = cleaning_agent.clean_article(article)
            
            # Skip empty content
            if not article["content"] or len(article["content"]) < 100:
                logger.log_error(category, url, "Article content too short")
                print(f"    ✗ Content too short")
                continue
            
            # Step 4: Detect negative news
            print(f"    → Analyzing sentiment...")
            analysis = detection_agent.analyze(article["content"])
            article.update(analysis)
            
            # Add metadata
            article["source"] = "jakartapost_business"
            article["processed_at"] = datetime.now().isoformat()
            
            processed_articles.append(article)
            status = "⚠ NEGATIVE" if analysis["is_negative"] else "✓ OK"
            print(f"    {status} (score: {analysis['negative_score']}, sentiment: {analysis['sentiment_score']:.2f})")
            logger.log_info(f"Processed: {title[:50]}... (Negative: {analysis['is_negative']})")
        
        # Step 5: Save/Append results
        print(f"\n[5/5] Saving results (appending to existing data)...")
        if processed_articles:
            output_path = storage_agent.save(processed_articles)
            logger.log_info(f"Saved {len(processed_articles)} articles to {output_path}")
            
            # Get final stats
            final_stats = storage_agent.get_stats()
            
            # Print summary
            negative_count = sum(1 for a in processed_articles if a["is_negative"])
            
            print(f"\n{'='*70}")
            print(f"PIPELINE COMPLETE")
            print(f"{'='*70}")
            print(f"Target per category: {limit_per_category}")
            print(f"Total articles collected: {len(articles)}")
            print(f"Successfully scraped: {len(scraped_articles)}")
            print(f"Successfully processed: {len(processed_articles)}")
            print(f"Negative articles this run: {negative_count}")
            print(f"-"*70)
            print(f"Total cumulative articles: {final_stats['total_articles']}")
            print(f"Total cumulative negative: {final_stats['negative_articles']}")
            print(f"Output saved to: {output_path}")
            print(f"{'='*70}\n")
        else:
            logger.log_info("No new articles were successfully processed")
            print("\nNo new articles were successfully processed")
        
    except Exception as e:
        logger.log_error("pipeline", "", str(e))
        print(f"\nERROR: {e}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Jakarta Post Business News Pipeline - Limited Version (50 articles per category)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum articles per category (default: 50)"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=10,
        help="Maximum pages to check per category (default: 10)"
    )
    
    args = parser.parse_args()
    run_pipeline(limit_per_category=args.limit, max_pages=args.max_pages)
