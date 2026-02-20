"""
Test cases for Negative High-Impact Event Detector
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents import NegativeEventDetector


def run_tests():
    detector = NegativeEventDetector()
    
    test_cases = [
        {
            "title": "Major earthquake hits Indonesia, killing hundreds",
            "content": "A powerful 7.5 magnitude earthquake struck Sulawesi, Indonesia on Friday, killing at least 400 people and destroying thousands of homes. The government has declared a state of emergency.",
            "expected": "yes"
        },
        {
            "title": "Company considers potential layoffs next year",
            "content": "PT Manufacturing is considering the possibility of reducing its workforce next year if market conditions do not improve.",
            "expected": "no"
        },
        {
            "title": "Vietnam factory shuts down after confirmed bankruptcy",
            "content": "Samsung's supplier in Vietnam has confirmed the closure of its factory after filing for bankruptcy. 5,000 workers have been laid off.",
            "expected": "yes"
        },
        {
            "title": "Analysts predict China economic growth may slow",
            "content": "Economic analysts predict that China's growth may slow down in the coming quarters due to various factors.",
            "expected": "no"
        },
        {
            "title": "Cambodia announces tariff increase on imports",
            "content": "The Cambodian government has officially announced a 25% tariff increase on all imported electronics, effective immediately.",
            "expected": "yes"
        },
        {
            "title": "Laos banking system faces liquidity crisis",
            "content": "The Central Bank of Laos has confirmed a severe liquidity crisis affecting multiple commercial banks. Emergency measures have been implemented.",
            "expected": "yes"
        },
        {
            "title": "New proposal discussed for infrastructure investment",
            "content": "Government officials are discussing a new proposal for infrastructure investment that could potentially benefit the economy.",
            "expected": "no"
        },
        {
            "title": "Port of Jakarta confirmed closed due to strike",
            "content": "The Port of Jakarta has been confirmed closed after a massive workers' strike began on Monday. All shipping operations have been halted indefinitely.",
            "expected": "yes"
        },
        {
            "title": "Company reports quarterly earnings",
            "content": "PT Telekom reported its quarterly earnings today, showing steady performance in line with expectations.",
            "expected": "no"
        },
        {
            "title": "Indonesia imposes export ban on raw nickel ore",
            "content": "The Indonesian government has officially implemented an export ban on raw nickel ore, effective January 1st. The policy has been confirmed and finalized.",
            "expected": "yes"
        }
    ]
    
    print("=" * 70)
    print("NEGATIVE HIGH-IMPACT EVENT DETECTOR - TEST RESULTS")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        result = detector.detect_from_text(test["title"], test["content"])
        expected = test["expected"]
        status = "PASS" if result == expected else "FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"\n[{i}] {test['title'][:50]}...")
        print(f"    Expected: {expected} | Got: {result} | {status}")
    
    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
