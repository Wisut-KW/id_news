"""
Negative High-Impact Event Detection Pipeline
Processes news events and evaluates them against AGENTS_NEG_CHECK.md criteria
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import List, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents import NegativeEventDetector


def process_single_event(detector: NegativeEventDetector, title: str, content: str) -> str:
    """
    Process a single event and return yes/no result.
    
    Args:
        detector: NegativeEventDetector instance
        title: Event title
        content: Event content
        
    Returns:
        "yes" or "no"
    """
    return detector.detect_from_text(title, content)


def process_json_file(detector: NegativeEventDetector, input_file: str, output_file: Optional[str] = None) -> List[Dict]:
    """
    Process events from a JSON file.
    
    Args:
        detector: NegativeEventDetector instance
        input_file: Path to input JSON file
        output_file: Optional path to output JSON file
        
    Returns:
        List of processed events with results
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        events = json.load(f)
    
    results = []
    
    for event in events:
        title = event.get('title', '')
        content = event.get('content', '') or event.get('description', '') or event.get('summary', '')
        
        result = detector.detect_from_text(title, content)
        
        processed_event = {
            **event,
            'negative_high_impact': result,
            'processed_at': datetime.now().isoformat()
        }
        
        results.append(processed_event)
    
    if output_file:
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    
    return results


def process_stdin(detector: NegativeEventDetector) -> str:
    """
    Read event from stdin and return result.
    
    Args:
        detector: NegativeEventDetector instance
        
    Returns:
        "yes" or "no"
    """
    lines = sys.stdin.read().strip().split('\n')
    
    if len(lines) >= 2:
        title = lines[0]
        content = '\n'.join(lines[1:])
    elif len(lines) == 1:
        try:
            data = json.loads(lines[0])
            title = data.get('title', '')
            content = data.get('content', '') or data.get('description', '')
        except json.JSONDecodeError:
            title = lines[0]
            content = ''
    else:
        return "no"
    
    return detector.detect_from_text(title, content)


def interactive_mode(detector: NegativeEventDetector):
    """
    Run interactive mode for testing events.
    """
    print("=" * 60)
    print("NEGATIVE HIGH-IMPACT EVENT DETECTOR")
    print("=" * 60)
    print("Enter event details (type 'quit' to exit)")
    print()
    
    while True:
        print("-" * 40)
        title = input("Title: ").strip()
        
        if title.lower() == 'quit':
            break
        
        print("Content (press Enter twice to finish):")
        content_lines = []
        while True:
            line = input()
            if not line:
                break
            content_lines.append(line)
        content = '\n'.join(content_lines)
        
        result = detector.detect_from_text(title, content)
        print(f"\nResult: {result}")
        
        analysis = detector.get_detailed_analysis(title, content)
        if analysis['criteria_matches']:
            print("Matched criteria:")
            for match in analysis['criteria_matches']:
                print(f"  - {match['criterion']}: {', '.join(match['matched_keywords'])}")


def main():
    parser = argparse.ArgumentParser(
        description="Negative High-Impact Event Detection Pipeline"
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        help='Input JSON file with events to process'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output JSON file for results'
    )
    parser.add_argument(
        '--title', '-t',
        type=str,
        help='Event title (for single event mode)'
    )
    parser.add_argument(
        '--content', '-c',
        type=str,
        help='Event content (for single event mode)'
    )
    parser.add_argument(
        '--stdin',
        action='store_true',
        help='Read event from stdin'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode'
    )
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed analysis (only for single event mode)'
    )
    
    args = parser.parse_args()
    
    detector = NegativeEventDetector()
    
    if args.interactive:
        interactive_mode(detector)
    elif args.stdin:
        result = process_stdin(detector)
        print(result)
    elif args.title and args.content:
        if args.detailed:
            analysis = detector.get_detailed_analysis(args.title, args.content)
            print(json.dumps(analysis, indent=2))
        else:
            result = detector.detect_from_text(args.title, args.content)
            print(result)
    elif args.input:
        output_file = args.output or f"data/processed_{os.path.basename(args.input)}"
        results = process_json_file(detector, args.input, output_file)
        
        positive_count = sum(1 for r in results if r['negative_high_impact'] == 'yes')
        negative_count = len(results) - positive_count
        
        print(f"Processed {len(results)} events")
        print(f"  Negative high-impact: {positive_count}")
        print(f"  Not qualifying: {negative_count}")
        print(f"Output saved to: {output_file}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
