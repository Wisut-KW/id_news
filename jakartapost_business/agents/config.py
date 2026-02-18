"""
Configuration for Jakarta Post Business Scraper
"""

import os
from datetime import datetime, timedelta


class Config:
    """Configuration settings for the Jakarta Post Business scraper"""
    
    # Date settings
    SCRAPE_DAYS = 2  # Default: last 2 days
    
    # File paths
    DATA_DIR = "data"
    LOGS_DIR = "logs"
    OUTPUT_FILENAME = "jakartapost_business.json"
    
    # Scraping settings
    MAX_PAGES = 20
    REQUEST_DELAY_MIN = 1
    REQUEST_DELAY_MAX = 3
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 30
    
    # Source categories
    CATEGORIES = {
        "company": "https://www.thejakartapost.com/business/companies/latest",
        "market": "https://www.thejakartapost.com/index.php/business/markets",
        "regulation": "https://www.thejakartapost.com/index.php/business/regulations",
        "economy": "https://www.thejakartapost.com/index.php/business/economy",
    }
    
    BASE_URL = "https://www.thejakartapost.com"
    
    # Negative detection settings
    NEGATIVE_THRESHOLD = 4
    SENTIMENT_THRESHOLD = -0.2
    
    # Negative keywords with weights
    NEGATIVE_KEYWORDS = {
        "loss": 2,
        "losses": 2,
        "decline": 2,
        "dropped": 2,
        "drop": 2,
        "fall": 2,
        "fell": 2,
        "decrease": 2,
        "layoff": 3,
        "layoffs": 3,
        "bankrupt": 4,
        "bankruptcy": 4,
        "default": 4,
        "lawsuit": 2,
        "litigation": 2,
        "corruption": 3,
        "fraud": 3,
        "scandal": 3,
        "recession": 4,
        "slowdown": 2,
        "sanction": 3,
        "sanctions": 3,
        "investigation": 2,
        "investigated": 2,
        "penalty": 2,
        "penalties": 2,
        "fine": 2,
        "fined": 2,
        "crisis": 3,
        "crash": 3,
        "collapse": 4,
        "plunge": 3,
        "tumble": 3,
        "slump": 3,
    }
    
    @classmethod
    def get_date_range(cls, days: int = None):
        """
        Get start and end dates for scraping
        
        Args:
            days: Number of days to look back (default: SCRAPE_DAYS)
            
        Returns:
            Tuple of (start_date, end_date) as datetime objects
        """
        if days is None:
            days = cls.SCRAPE_DAYS
            
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days-1)
        
        return start_date, end_date
    
    @classmethod
    def get_output_filepath(cls):
        """Get full path to output file"""
        return os.path.join(cls.DATA_DIR, cls.OUTPUT_FILENAME)
