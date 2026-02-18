# Jakarta Post Business News Scraper

A Python script to scrape business news from The Jakarta Post website.

## Features

- Scrapes articles from the business section
- **NEW: Fetch full article content** from individual article pages
- Configurable date range (defaults to last 2 days)
- Paginates automatically until date threshold is reached
- Appends new articles to JSON file
- Prevents duplicate entries (checks by URL)
- Extracts author, category, and tags
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

### Fetch full article content (slower but complete)
```bash
python scraper.py --fetch-content
# or
python scraper.py -c
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

### Combined options
```bash
python scraper.py --days 7 --fetch-content --output full_articles.json
```

## Output Format

### Without --fetch-content (default)
```json
[
  {
    "title": "Article Title",
    "url": "https://www.thejakartapost.com/business/2026/02/18/article.html",
    "date": "2026-02-18T12:32:56",
    "summary": "Article summary from listing page...",
    "scraped_at": "2026-02-18T08:55:09"
  }
]
```

### With --fetch-content
```json
[
  {
    "title": "Article Title",
    "url": "https://www.thejakartapost.com/business/2026/02/18/article.html",
    "date": "2026-02-18T12:32:56",
    "date_parsed": "2026-02-18 12:32:56",
    "summary": "Article summary from listing page...",
    "author": "Author Name",
    "category": "Companies",
    "tags": ["tag1", "tag2", "tag3"],
    "content": "Full article content with all paragraphs...",
    "scraped_at": "2026-02-18T08:55:09"
  }
]
```

## Data Fields

| Field | Description | With --fetch-content |
|-------|-------------|---------------------|
| `title` | Article headline | Always |
| `url` | Full article URL | Always |
| `date` | Publication date (ISO format) | Always |
| `date_parsed` | Parsed datetime object | Optional |
| `summary` | Short excerpt from listing | Always |
| `author` | Article author name | With -c flag |
| `category` | Article category/section | With -c flag |
| `tags` | List of article tags | With -c flag |
| `content` | Full article text | With -c flag |
| `scraped_at` | When the article was scraped | Always |

## Performance Notes

- **Without --fetch-content**: Fast, only scrapes listing pages (~2-5 seconds per page)
- **With --fetch-content**: Slower, fetches each individual article page (~1-2 seconds per article)
  - Example: 50 articles ≈ 60-120 seconds total

## Logs

Errors and progress are logged to:
- Console output
- `scraper.log` file

## Files

- `scraper.py` - Main scraping script
- `requirements.txt` - Python dependencies
- `news_data.json` - Output file (created automatically)
- `scraper.log` - Log file
- `README.md` - This documentation

## Example Workflow

```bash
# Initial scrape with content
python scraper.py --days 7 --fetch-content

# Subsequent runs (only new articles, faster without content)
python scraper.py --days 2

# Or get content for new articles only
python scraper.py --days 2 --fetch-content
```
