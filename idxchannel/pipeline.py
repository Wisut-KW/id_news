"""
Main IDX Channel News Pipeline with Translation and Index Page Support
Orchestrates all agents to process IDX Channel news articles
"""

import os
import sys
from datetime import datetime, timedelta

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents import (
    IDXChannelListingAgent,
    ArticleScraperAgent,
    TextCleaningAgent,
    TranslationAgent,
    NegativeNewsDetectionAgent,
    StorageAgent,
    LoggingAgent,
)


def run_pipeline(days_back: int = 3):
    """
    Run the complete IDX Channel news processing pipeline with translation
    
    Args:
        days_back: Number of days to look back (default: 3)
    
    Flow:
    1. Fetch articles from index pages for each date (last N days)
    2. Scrape full content for each article
    3. Clean text
    4. Translate to English
    5. Detect negative events using translated text
    6. Append to existing JSON
    7. Log errors
    """
    # Initialize agents
    listing_agent = IDXChannelListingAgent(delay=2.0, max_retries=3)
    scraper_agent = ArticleScraperAgent(delay=2.0, max_retries=3)
    cleaning_agent = TextCleaningAgent()
    translation_agent = TranslationAgent(use_google_translate=True, use_local_model=False)
    detection_agent = NegativeNewsDetectionAgent()
    storage_agent = StorageAgent(data_dir="data")
    logger = LoggingAgent(logs_dir="logs")
    
    # Calculate date range
    today = datetime.now()
    cutoff_date = today - timedelta(days=days_back-1)
    cutoff_str = cutoff_date.strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")
    
    logger.log_info(f"Starting IDX Channel news pipeline (last {days_back} days, from {cutoff_str} to {today_str})")
    print("="*60)
    print(f"IDX CHANNEL NEWS PIPELINE")
    print(f"Date Range: {cutoff_str} to {today_str} ({days_back} days)")
    print("="*60)
    
    # Show existing stats before processing
    stats = storage_agent.get_stats(f"{today_str}_idxchannel.json")
    if stats["exists"]:
        print(f"\n📊 Existing data: {stats['total_articles']} articles ({stats['negative_articles']} negative)")
    
    try:
        # Step 1: Fetch articles from index pages for each date
        print(f"\n[1/7] Fetching articles from index pages...")
        articles = listing_agent.fetch_listings_by_date_range(days=days_back)
        logger.log_info(f"Found {len(articles)} articles from index pages")
        
        if not articles:
            logger.log_info("No articles found in index pages")
            print("\nNo articles found")
            return
        
        # Step 2: Scrape full content
        print(f"\n[2/7] Scraping full article content...")
        scraped_articles = []
        skipped_count = 0
        
        for i, article in enumerate(articles):
            url = article.get("url", "")
            title = article.get("title", "Unknown")
            article_date = article.get("published_date", "unknown")
            
            print(f"  [{i+1}/{len(articles)}] [{article_date}] {title[:50]}...")
            logger.log_info(f"Scraping article {i+1}/{len(articles)}: {title[:50]}...")
            
            scraped_data = scraper_agent.scrape_article(url)
            
            if scraped_data is None:
                logger.log_error(url, "Failed to scrape article content")
                print(f"    ✗ Failed")
                skipped_count += 1
                continue
            
            # Merge scraped data
            article["content"] = scraped_data["content"]
            if scraped_data["author"]:
                article["author"] = scraped_data["author"]
            
            scraped_articles.append(article)
        
        print(f"\n  Scraped: {len(scraped_articles)} successful, {skipped_count} failed")
        
        if not scraped_articles:
            logger.log_info("No articles were successfully scraped")
            print("\nNo articles could be scraped")
            return
        
        # Step 3-6: Process articles (clean, translate, analyze)
        processed_articles = []
        
        print(f"\n[3-6/7] Processing {len(scraped_articles)} articles...")
        
        for i, article in enumerate(scraped_articles):
            url = article.get("url", "")
            title = article.get("title", "Unknown")
            article_date = article.get("published_date", "unknown")
            
            print(f"\n  [{i+1}/{len(scraped_articles)}] [{article_date}] {title[:45]}...")
            
            # Step 3: Clean text
            print(f"    → Cleaning...")
            article = cleaning_agent.clean_article(article)
            
            # Skip empty content
            if not article["content"] or len(article["content"]) < 100:
                logger.log_error(url, "Article content too short or empty")
                print(f"    ✗ Content too short")
                continue
            
            # Step 4: Translate to English
            print(f"    → Translating (ID → EN)...")
            article = translation_agent.translate_article(article)
            
            # Check if translation was successful
            if not article.get("translation_success", False):
                print(f"    ⚠ Translation may have failed, using original text")
                logger.log_info(f"Translation warning for: {url}")
            
            # Step 5: Detect negative news using TRANSLATED text
            print(f"    → Analyzing sentiment...")
            text_for_analysis = article.get("content_translated", article["content"])
            analysis = detection_agent.analyze(text_for_analysis)
            article.update(analysis)
            
            # Step 6: Add metadata
            article["source"] = "idxchannel"
            article["language_original"] = "id"
            article["language_translated"] = "en"
            
            processed_articles.append(article)
            status = "⚠ NEGATIVE" if analysis["is_negative"] else "✓ OK"
            print(f"    {status} (score: {analysis['negative_score']}, sentiment: {analysis['sentiment_score']:.2f})")
            logger.log_info(f"Processed: {title[:50]}... (Negative: {analysis['is_negative']})")
        
        # Step 7: Save/Append results
        print(f"\n[7/7] Saving results (appending to existing data)...")
        if processed_articles:
            output_path = storage_agent.save(processed_articles)
            logger.log_info(f"Saved {len(processed_articles)} articles to {output_path}")
            
            # Get final stats
            final_stats = storage_agent.get_stats(f"{today_str}_idxchannel.json")
            
            # Print summary
            negative_count = sum(1 for a in processed_articles if a["is_negative"])
            successful_translations = sum(1 for a in processed_articles if a.get("translation_success", False))
            
            print(f"\n{'='*60}")
            print(f"PIPELINE COMPLETE")
            print(f"{'='*60}")
            print(f"Total articles found: {len(articles)}")
            print(f"Successfully scraped: {len(scraped_articles)}")
            print(f"Successfully processed: {len(processed_articles)}")
            print(f"Successful translations: {successful_translations}/{len(processed_articles)}")
            print(f"Negative articles this run: {negative_count}")
            print(f"-"*60)
            print(f"Total cumulative articles: {final_stats['total_articles']}")
            print(f"Total cumulative negative: {final_stats['negative_articles']}")
            print(f"Output saved to: {output_path}")
            print(f"{'='*60}\n")
        else:
            logger.log_info("No new articles were successfully processed")
            print("\nNo new articles were successfully processed")
        
    except Exception as e:
        logger.log_error("pipeline", str(e))
        print(f"\nERROR: {e}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="IDX Channel News Pipeline")
    parser.add_argument(
        "--days", 
        type=int, 
        default=3,
        help="Number of days to look back (default: 3)"
    )
    
    args = parser.parse_args()
    run_pipeline(days_back=args.days)
