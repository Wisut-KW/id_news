# Jakarta Post News Scraper

A Python script to scrape news articles from The Jakarta Post business companies section.

## Features

- Scrapes articles from `https://www.thejakartapost.com/business/companies/latest`
- Configurable date range (default: last 2 days)
- Automatic pagination until date threshold is reached
- Appends new articles to JSON file
- Prevents duplicate entries (checks against existing URLs)
- Comprehensive logging to console and file

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage (default: last 2 days)

```bash
python jakarta_post_scraper.py
```

### Specify Date Range

```bash
# Scrape last 5 days
python jakarta_post_scraper.py --days 5

# Scrape last week
python jakarta_post_scraper.py -d 7
```

### Custom Output File

```bash
python jakarta_post_scraper.py --output my_news.json
```

## Output Format

The script generates a JSON file with the following structure:

```json
[
  {
    "title": "Article Title",
    "url": "https://www.thejakartapost.com/...",
    "date_string": "Mon, 17 February 2025",
    "summary": "Article summary or excerpt...",
    "image_url": "https://...",
    "scraped_at": "2025-02-18T12:00:00"
  }
]
```

## Files

- `jakarta_post_scraper.py` - Main scraper script
- `requirements.txt` - Python dependencies
- `news_data.json` - Default output file (created on first run)
- `scraper.log` - Log file with execution details

## Logging

The script logs all activities to:
1. Console (stdout)
2. `scraper.log` file

## Notes

- The scraper uses a User-Agent header to mimic a browser request
- Duplicate URLs are automatically filtered out
- Maximum of 50 pages are scraped as a safety measure
- Date parsing supports multiple common formats
