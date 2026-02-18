# Jakarta Post Business News Scraper

A Python script to scrape business news from The Jakarta Post website.

## Features

- Scrapes articles from the business section
- Configurable date range (defaults to last 2 days)
- Paginates automatically until date threshold is reached
- Appends new articles to JSON file
- Prevents duplicate entries (checks by URL)
- Comprehensive error logging

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic usage (default: last 2 days)
```bash
python scraper.py
```

### Specify custom date range
```bash
python scraper.py --days 7
```

### Custom output file
```bash
python scraper.py --output my_news.json
```

### Custom URL
```bash
python scraper.py --url https://www.thejakartapost.com/business/latest
```

## Output Format

The scraper outputs a JSON file with the following structure:

```json
[
  {
    "title": "Article Title",
    "url": "https://www.thejakartapost.com/business/...",
    "date": "2024-01-15T10:30:00",
    "summary": "Article summary or excerpt...",
    "scraped_at": "2024-01-15T12:00:00"
  }
]
```

## Logs

Errors and progress are logged to:
- Console output
- `scraper.log` file

## Files

- `scraper.py` - Main scraping script
- `requirements.txt` - Python dependencies
- `news_data.json` - Output file (created automatically)
- `scraper.log` - Log file
