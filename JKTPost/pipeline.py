#!/usr/bin/env python3
"""
Jakarta Post Business News Pipeline
Orchestrates all agents to scrape and analyze Jakarta Post business news
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


def run_pipeline(days: int = None, max_pages: int = None):
    """
    Run the Jakarta Post Business news scraping pipeline
    
    Args:
        days: Number of days to look back (default: Config.SCRAPE_DAYS)
        max_pages: Maximum pages per category (default: Config.MAX_PAGES)
    """
    # Use defaults from config if not specified
    if days is None:
        days = Config.SCRAPE_DAYS
    if max_pages is None:
        max_pages = Config.MAX_PAGES
    
    # Initialize agents
    listing_agent = JakartaPostListingAgent()
    scraper_agent = ArticleScraperAgent()
    cleaning_agent = TextCleaningAgent()
    detection_agent = NegativeNewsDetectionAgent()
    storage_agent = StorageAgent()
    logger = LoggingAgent()
    
    # Get date range
    start_date, end_date = Config.get_date_range(days)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    logger.log_info(f"Starting Jakarta Post Business pipeline ({days} days: {start_str} to {end_str})")
    
    print("="*70)
    print("JAKARTA POST BUSINESS NEWS PIPELINE")
    print("="*70)
    print(f"Date Range: {start_str} to {end_str} ({days} days)")
    print(f"Max Pages/Category: {max_pages}")
    print(f"Categories: {', '.join(Config.CATEGORIES.keys())}")
    print("="*70)
    
    # Show existing stats
    stats = storage_agent.get_stats()
    if stats["exists"]:
        print(f"\n📊 Existing data: {stats['total_articles']} articles ({stats['negative_articles']} negative)")
    
    try:
        # Step 1: Fetch listings from all categories with pagination
        print(f"\n[1/5] Fetching articles from all categories...")
        articles = listing_agent.fetch_all_categories(start_date, end_date, max_pages)
        
        # Filter out existing URLs before processing
        existing_urls = storage_agent.get_existing_urls()
        new_articles = []
        skipped_existing = 0
        
        for article in articles:
            normalized_url = storage_agent._normalize_url(article.get("url", ""))
            if normalized_url not in existing_urls:
                new_articles.append(article)
            else:
                skipped_existing += 1
        
        articles = new_articles
        logger.log_info(f"Found {len(articles)} unique new articles from all categories (skipped {skipped_existing} existing)")
        print(f"\n  Total unique new articles found: {len(articles)} (skipped {skipped_existing} existing)")
        
        if not articles:
            logger.log_info("No new articles found")
            print("\nNo new articles found in specified date range")
            return
        
        # Step 2: Scrape full content for each article
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
        
        # Step 3-4: Process articles (clean, analyze)
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
            print(f"Total articles found: {len(articles)}")
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
    
    parser = argparse.ArgumentParser(description="Jakarta Post Business News Pipeline")
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help=f"Number of days to look back (default: {Config.SCRAPE_DAYS})"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help=f"Maximum pages per category (default: {Config.MAX_PAGES})"
    )
    
    args = parser.parse_args()
    run_pipeline(days=args.days, max_pages=args.max_pages)
