"""
Main News Pipeline
Orchestrates all agents to process news articles
"""

import os
import sys

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents import (
    RSSIngestionAgent,
    ArticleScraperAgent,
    TextCleaningAgent,
    NegativeNewsDetectionAgent,
    StorageAgent,
    LoggingAgent,
)


def run_pipeline():
    """
    Run the complete news processing pipeline
    
    Flow:
    1. Fetch RSS feed
    2. Filter today's articles
    3. Scrape full content
    4. Clean text
    5. Detect negative news
    6. Save results
    7. Log errors
    """
    # Initialize agents
    rss_agent = RSSIngestionAgent()
    scraper_agent = ArticleScraperAgent(delay=2.0, max_retries=3)
    cleaning_agent = TextCleaningAgent()
    detection_agent = NegativeNewsDetectionAgent()
    storage_agent = StorageAgent(data_dir="data")
    logger = LoggingAgent(logs_dir="logs")
    
    logger.log_info("Starting news pipeline")
    
    try:
        # Step 1: Fetch RSS feed
        logger.log_info("Fetching RSS feed")
        articles = rss_agent.fetch_feed()
        logger.log_info(f"Fetched {len(articles)} articles from RSS")
        
        # Step 2: Filter today's articles
        today_articles = rss_agent.filter_today_articles(articles)
        logger.log_info(f"Found {len(today_articles)} articles from today")
        
        if not today_articles:
            logger.log_info("No articles to process today")
            return
        
        # Step 3-5: Process each article
        processed_articles = []
        
        for i, article in enumerate(today_articles):
            url = article.get("url", "")
            title = article.get("title", "Unknown")
            
            logger.log_info(f"Processing article {i+1}/{len(today_articles)}: {title[:50]}...")
            
            # Scrape full content
            content = scraper_agent.scrape_article(url)
            
            if content is None:
                logger.log_error(url, "Failed to scrape article content")
                continue
            
            # Add content to article
            article["content"] = content
            
            # Clean text
            article = cleaning_agent.clean_article(article)
            
            # Skip empty content
            if not article["content"] or len(article["content"]) < 100:
                logger.log_error(url, "Article content too short or empty")
                continue
            
            # Detect negative news
            analysis = detection_agent.analyze(article["content"])
            article.update(analysis)
            
            processed_articles.append(article)
            logger.log_info(f"Processed: {title[:50]}... (Negative: {analysis['is_negative']})")
        
        # Step 6: Save results
        if processed_articles:
            output_path = storage_agent.save(processed_articles)
            logger.log_info(f"Saved {len(processed_articles)} articles to {output_path}")
            
            # Print summary
            negative_count = sum(1 for a in processed_articles if a["is_negative"])
            print(f"\n{'='*60}")
            print(f"PIPELINE COMPLETE")
            print(f"{'='*60}")
            print(f"Total articles processed: {len(processed_articles)}")
            print(f"Negative articles detected: {negative_count}")
            print(f"Output saved to: {output_path}")
            print(f"{'='*60}\n")
        else:
            logger.log_info("No articles were successfully processed")
            print("No articles were successfully processed")
        
    except Exception as e:
        logger.log_error("pipeline", str(e))
        raise


if __name__ == "__main__":
    run_pipeline()
