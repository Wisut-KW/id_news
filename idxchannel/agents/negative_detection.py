"""
Negative News Detection Agent
Detects negative events using business/finance keywords and sentiment analysis
"""

import re
from typing import Dict
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class NegativeNewsDetectionAgent:
    """Agent to detect negative news events"""
    
    # Business/Finance focused negative keywords
    KEYWORDS = {
        "market_decline": [
            "crash", "collapse", "plunge", "tumble", "slump", "downturn",
            "bearish", "sell-off", "meltdown", "freefall", "nosedive"
        ],
        "economic_distress": [
            "recession", "inflation", "stagflation", "deflation", "crisis",
            "bankruptcy", "insolvency", "default", "bailout", "rescue"
        ],
        "corporate_issues": [
            "layoffs", "downsizing", "restructuring", "closure", "shutdown",
            "loss", "losses", "deficit", "write-off", "impairment"
        ],
        "regulatory_legal": [
            "investigation", "penalty", "fine", "sanction", "violation",
            "fraud", "scandal", "lawsuit", "litigation", "indictment"
        ],
        "financial_trouble": [
            "debt", "indebtedness", "liquidity", "solvency", "distress",
            "underperform", "missed target", "earnings warning", "profit warning"
        ],
        "market_volatility": [
            "volatile", "uncertainty", "instability", "turmoil", "disruption",
            "contagion", "panic", "fear", "concern", "risk"
        ]
    }
    
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
    
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
        Count negative keyword occurrences
        
        Args:
            text: Text to analyze
            
        Returns:
            Total keyword count
        """
        text_lower = text.lower()
        score = 0
        
        for category, keywords in self.KEYWORDS.items():
            for keyword in keywords:
                # Use word boundaries for better matching
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                matches = re.findall(pattern, text_lower)
                score += len(matches)
        
        return score
    
    def _calculate_sentiment_score(self, text: str) -> float:
        """
        Calculate sentiment score using VADER
        
        Args:
            text: Text to analyze
            
        Returns:
            Compound sentiment score (-1 to 1)
        """
        scores = self.analyzer.polarity_scores(text)
        return scores["compound"]
    
    def _determine_negative(self, keyword_score: int, sentiment_score: float) -> bool:
        """
        Determine if article is negative based on scores
        
        Args:
            keyword_score: Count of negative keywords
            sentiment_score: VADER compound sentiment score
            
        Returns:
            True if article is negative
        """
        return keyword_score >= 2 or sentiment_score < -0.3
