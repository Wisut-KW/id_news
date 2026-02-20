"""
Negative High-Impact Event Detection Agent
Evaluates news events for negative high-impact criteria per AGENTS_NEG_CHECK.md
"""

import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass


@dataclass
class EventContext:
    title: str
    content: str
    country: Optional[str] = None
    is_confirmed: bool = False
    has_material_impact: bool = False


class NegativeEventDetector:
    """
    Agent to detect negative high-impact events according to AGENTS_NEG_CHECK.md
    
    Returns strictly "yes" or "no" based on 14 qualification criteria.
    """
    
    TARGET_COUNTRIES: Set[str] = {
        "indonesia", "china", "vietnam", "cambodia", "laos",
        "indonesian", "chinese", "vietnamese", "cambodian", "laotian",
        "jakarta", "beijing", "hanoi", "phnom penh", "vientiane"
    }
    
    CRITERIA_KEYWORDS = {
        "production_disruption": {
            "keywords": [
                "factory shutdown", "factory shutdowns", "plant closure", "production halt", 
                "manufacturing disruption", "supply chain disruption",
                "port closure", "port shutdown", "port closed",
                "shipping disruption", "shipping halted",
                "logistics disruption", "airport closure", "energy crisis",
                "power outage", "blackout", "labor strike", "worker strike",
                "mass strike", "industrial action", "work stoppage",
                "factory fire", "explosion at", "production suspended",
                "operations halted", "supply shortage", "supply cut",
                "disruption confirmed", "shutdown confirmed",
                "strike began", "workers' strike", "announced shutdowns"
            ],
            "weight": 3.0
        },
        "corporate_distress": {
            "keywords": [
                "bankruptcy", "bankrupt", "default", "defaults on",
                "insolvency", "insolvent", "debt restructuring", 
                "credit downgrade", "rating downgrade", "downgraded to",
                "liquidity crisis", "cash crisis", "unable to pay",
                "filed for bankruptcy", "chapter 11", "creditors meeting",
                "debt default confirmed", "restructuring confirmed"
            ],
            "weight": 3.0
        },
        "sovereign_stress": {
            "keywords": [
                "sovereign default", "sovereign downgrade", 
                "country downgrade", "national default",
                "imf bailout", "imf program", "imf loan",
                "emergency bailout", "capital controls", "capital flight",
                "bank run", "banking crisis", "bank collapse",
                "interbank freeze", "financial system collapse",
                "currency crisis", "currency devaluation",
                "foreign reserves depleted", "sovereign debt crisis"
            ],
            "weight": 3.5
        },
        "trade_restrictions": {
            "keywords": [
                "tariff imposed", "tariff increase", "new tariffs",
                "export ban", "import ban", "trade ban",
                "sanctions imposed", "sanctions announced",
                "trade barriers", "market access denied",
                "trade restrictions", "embargo", "export restrictions",
                "import restrictions", "trade war", "retaliatory tariffs"
            ],
            "weight": 3.0
        },
        "regulatory_political_shock": {
            "keywords": [
                "nationalization", "nationalised", "nationalized",
                "asset seizure", "assets seized", "expropriation",
                "industry ban", "sector ban", "regulatory crackdown",
                "government crackdown", "forced shutdown",
                "political crisis", "government collapse",
                "leadership removed", "president removed", "prime minister removed",
                "coup", "military takeover", "state of emergency declared",
                "institution dissolved", "parliament dissolved"
            ],
            "weight": 3.5
        },
        "capital_withdrawal": {
            "keywords": [
                "business closure", "company exit", "market exit",
                "withdrawal from market", "pulling out", "exiting country",
                "capital flight", "foreign investment withdrawn",
                "operations relocated", "factory relocated",
                "mass layoffs", "workforce reduction",
                "hiring freeze", "investment cancelled",
                "project cancelled", "expansion cancelled",
                "shutdown announced", "closure confirmed"
            ],
            "weight": 2.5
        },
        "demand_contraction": {
            "keywords": [
                "demand collapse", "demand fell", "demand dropped",
                "consumer spending fell", "consumer spending declined",
                "exports declined", "exports fell", "exports dropped",
                "industrial demand fell", "b2b transactions declined",
                "sales plummeted", "orders cancelled", "order backlog",
                "sustained decline", "continued contraction",
                "recession", "economic contraction", "quarter of contraction"
            ],
            "weight": 2.5
        },
        "natural_disaster": {
            "keywords": [
                "earthquake", "typhoon", "hurricane", "cyclone",
                "flood", "flooding", "major fire", "wildfire",
                "epidemic", "pandemic", "disease outbreak",
                "drought", "landslide", "tsunami", "volcanic eruption",
                "death toll", "casualties reported", "evacuation ordered",
                "disaster zone", "state of emergency", "emergency declared"
            ],
            "weight": 2.5
        },
        "infrastructure_failure": {
            "keywords": [
                "power grid failure", "grid collapse", "blackout",
                "port shutdown", "port closed", "port disruption",
                "telecommunications outage", "network failure",
                "payment system down", "banking system down",
                "cyberattack", "cyber attack", "ransomware",
                "transport system failure", "rail disruption",
                "air traffic halted", "infrastructure failure"
            ],
            "weight": 3.0
        },
        "corporate_outlook_cuts": {
            "keywords": [
                "negative outlook", "outlook cut", "profit warning",
                "earnings warning", "guidance cut", "lowered forecast",
                "capex cut", "capital expenditure cut", "investment cut",
                "project cancelled", "expansion cancelled",
                "hiring freeze", "job cuts", "layoffs announced",
                "restructuring announced", "cost cutting"
            ],
            "weight": 2.0
        },
        "fiscal_tightening": {
            "keywords": [
                "stimulus ended", "stimulus withdrawn", "support ended",
                "subsidy cut", "subsidy removed", "subsidy expired",
                "new tax", "tax increase", "tax hike",
                "austerity measures", "spending cuts", "budget cuts",
                "fiscal tightening", "government spending cut"
            ],
            "weight": 2.5
        },
        "market_instability": {
            "keywords": [
                "market crash", "stock market plunge", "stocks tumble",
                "index fell", "market volatility", "sharp decline",
                "currency plunge", "currency crash", "exchange rate fall",
                "commodity crash", "oil price crash", "price collapse",
                "trading halted", "circuit breaker", "sell-off"
            ],
            "weight": 2.0
        },
        "geopolitical_escalation": {
            "keywords": [
                "military conflict", "armed conflict", "border clash",
                "military confrontation", "maritime blockade",
                "naval blockade", "civil unrest", "riots", "protests turn violent",
                "state of emergency declared", "mobilization",
                "troops deployed", "military action", "escalation confirmed"
            ],
            "weight": 3.5
        },
        "structural_escalation": {
            "keywords": [
                "first time", "unprecedented", "never before",
                "record high", "record low", "worst since",
                "sharpest decline", "largest drop", "historic",
                "all-time", "exceptional", "extraordinary measures"
            ],
            "weight": 1.5
        }
    }
    
    EXCLUSION_PATTERNS = [
        r'\b(may|might|could|would|should|potentially|possibly|expected|forecast|projected|predicted|anticipated|likely|rumored|speculated)\b',
        r'\b(proposal|proposed|draft|plan to|considering|discussing|negotiating|talks about)\b',
        r'\b(if|whether|whether or not|in case|hypothetical|scenario)\b',
        r'\b(risk of|threat of|concern about|fear of|worry about)\b',
        r'\b(warns|warning|caution|advisory|alert)\b(?!\s+(of\s+)?(confirmed|announced|declared))'
    ]
    
    CONFIRMATION_PATTERNS = [
        r'\b(confirmed|announced|declared|official|finalized|completed|executed|implemented)\b',
        r'\b(has occurred|occurred on|took place|happened)\b',
        r'\b(reported that|stated that|announced that)\b'
    ]
    
    def __init__(self):
        pass
    
    def detect(self, event: EventContext) -> str:
        """
        Main detection method.
        
        Args:
            event: EventContext with title, content, and optional metadata
            
        Returns:
            "yes" if event qualifies as negative high-impact, "no" otherwise
        """
        text = f"{event.title} {event.content}".lower()
        
        if not self._check_geographic_requirement(text):
            return "no"
        
        if not self._check_confirmed_outcome(text):
            return "no"
        
        if self._check_exclusion_patterns(text):
            return "no"
        
        criteria_score = self._evaluate_criteria(text)
        
        if criteria_score >= 2.0:
            return "yes"
        
        return "no"
    
    def detect_from_text(self, title: str, content: str) -> str:
        """
        Convenience method to detect from title and content strings.
        
        Args:
            title: Event title
            content: Event content/description
            
        Returns:
            "yes" or "no"
        """
        event = EventContext(
            title=title,
            content=content
        )
        return self.detect(event)
    
    def _check_geographic_requirement(self, text: str) -> bool:
        """Check if event relates to target countries."""
        text_lower = text.lower()
        
        for country in self.TARGET_COUNTRIES:
            if country in text_lower:
                return True
        
        return False
    
    def _check_confirmed_outcome(self, text: str) -> bool:
        """Check if the event describes a confirmed, finalized outcome."""
        has_confirmation = False
        
        for pattern in self.CONFIRMATION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                has_confirmation = True
                break
        
        past_tense_indicators = [
            r'\b(shut down|closed|collapsed|defaulted|filed|declared|announced|implemented|imposed|occurred|happened)\b',
            r'\b(has shut|has closed|has collapsed|has defaulted|has filed)\b',
            r'\b(has been|were)\s+(shut|closed|destroyed|damaged|cancelled|halted|stopped)\b',
            r'\b(operations)\s+(halted|stopped|suspended)\b'
        ]
        
        for pattern in past_tense_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                has_confirmation = True
                break
        
        disaster_indicators = [
            "earthquake struck", "typhoon hit", "flood hit", "fire destroyed",
            "killed", "died", "injured", "evacuated", "destroyed"
        ]
        for indicator in disaster_indicators:
            if indicator in text.lower():
                has_confirmation = True
                break
        
        return has_confirmation
    
    def _check_exclusion_patterns(self, text: str) -> bool:
        """Check for speculative/future language patterns."""
        exclusion_count = 0
        
        for pattern in self.EXCLUSION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            exclusion_count += len(matches)
        
        return exclusion_count >= 3
    
    def _evaluate_criteria(self, text: str) -> float:
        """Evaluate all criteria and return weighted score."""
        total_score = 0.0
        text_lower = text.lower()
        
        for criterion, config in self.CRITERIA_KEYWORDS.items():
            keywords = config["keywords"]
            weight = config["weight"]
            
            for keyword in keywords:
                if keyword in text_lower:
                    total_score += weight
                    break
        
        return total_score
    
    def get_detailed_analysis(self, title: str, content: str) -> Dict:
        """
        Get detailed analysis including which criteria matched.
        
        Args:
            title: Event title
            content: Event content
            
        Returns:
            Dict with analysis details
        """
        text = f"{title} {content}".lower()
        
        result = {
            "result": self.detect_from_text(title, content),
            "geographic_match": self._check_geographic_requirement(text),
            "confirmed_outcome": self._check_confirmed_outcome(text),
            "excluded": self._check_exclusion_patterns(text),
            "criteria_matches": [],
            "total_score": 0.0
        }
        
        matched_criteria = []
        total_score = 0.0
        
        for criterion, config in self.CRITERIA_KEYWORDS.items():
            matched_keywords = []
            for keyword in config["keywords"]:
                if keyword in text:
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                matched_criteria.append({
                    "criterion": criterion,
                    "matched_keywords": matched_keywords[:3],
                    "weight": config["weight"]
                })
                total_score += config["weight"]
        
        result["criteria_matches"] = matched_criteria
        result["total_score"] = total_score
        
        return result
