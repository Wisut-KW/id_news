"""
Negative News Detection Agent
Detects negative events using weighted keywords and sentiment analysis
"""

import re
from typing import Dict

from .config import Config


class NegativeNewsDetectionAgent:
    """Agent to detect negative news events with weighted keywords"""
    
    def __init__(self):
        self.keywords = Config.NEGATIVE_KEYWORDS
        self.threshold = Config.NEGATIVE_THRESHOLD
        self.sentiment_threshold = Config.SENTIMENT_THRESHOLD
        
        # Try to import vaderSentiment
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self.analyzer = SentimentIntensityAnalyzer()
            self.has_sentiment = True
        except ImportError:
            self.analyzer = None
            self.has_sentiment = False
    
    def analyze(self, text: str) -> Dict:
        """
        Analyze text for negative content
        
        Args:
            text: Article text to analyze
            
        Returns:
            Dict with negative_score, sentiment_score, is_negative
        """
        keyword_score = self._calculate_keyword_score(text)
        sentiment_score = self._calculate_sentiment_score(text)
        is_negative = self._determine_negative(keyword_score, sentiment_score)
        
        return {
            "negative_score": keyword_score,
            "sentiment_score": sentiment_score,
            "is_negative": is_negative
        }
    
    def _calculate_keyword_score(self, text: str) -> int:
        """
        Calculate weighted keyword score
        
        Args:
            text: Text to analyze
            
        Returns:
            Total weighted keyword score
        """
        text_lower = text.lower()
        score = 0
        
        for keyword, weight in self.keywords.items():
            # Use word boundaries for better matching
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            matches = re.findall(pattern, text_lower)
            score += len(matches) * weight
        
        return score
    
    def _calculate_sentiment_score(self, text: str) -> float:
        """
        Calculate sentiment score
        
        Args:
            text: Text to analyze
            
        Returns:
            Compound sentiment score (-1 to 1)
        """
        if self.has_sentiment and self.analyzer:
            scores = self.analyzer.polarity_scores(text)
            return scores["compound"]
        
        # Fallback: return neutral if no sentiment analyzer
        return 0.0
    
    def _determine_negative(self, keyword_score: int, sentiment_score: float) -> bool:
        """
        Determine if article is negative
        
        Args:
            keyword_score: Weighted keyword score
            sentiment_score: Sentiment score
            
        Returns:
            True if article is negative
        """
        return keyword_score >= self.threshold or sentiment_score < self.sentiment_threshold
