# Jakarta Post Business News Scraper

Python-based news scraping agent for Jakarta Post business categories with negative event detection.

## Features

- **Multi-category scraping**: Company, Market, Regulation, Economy
- **Pagination support**: Crawls multiple pages per category until date threshold reached
- **Date filtering**: Configurable date range (default: last 2 days)
- **Negative event detection**: Weighted keyword scoring + sentiment analysis
- **Append mode**: Never overwrites existing data, always merges
- **Deduplication**: Automatically skips duplicate articles by URL
- **Error logging**: Logs errors without stopping execution

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Pipeline

**Default (last 2 days):**
```bash
python pipeline.py
```

**Custom date range (last 5 days):**
```bash
python pipeline.py --days 5
```

**Custom max pages per category:**
```bash
python pipeline.py --days 3 --max-pages 10
```

## Source Categories

1. **Company**: `/business/companies/latest`
2. **Market**: `/index.php/business/markets`
3. **Regulation**: `/index.php/business/regulations`
4. **Economy**: `/index.php/business/economy`

## Pipeline Flow

1. **Jakarta Post Listing Agent** - Scrapes all 4 categories with pagination
2. **Article Scraper Agent** - Scrapes full article content
3. **Text Cleaning Agent** - Cleans and normalizes text
4. **Negative News Detection Agent** - Weighted keywords + sentiment analysis
5. **Storage Agent** - **Appends** results to JSON (no data loss)

## Pagination Logic

For each category, the scraper:
- Fetches page 1, 2, 3... up to MAX_PAGES
- Stops when oldest article on page < start_date
- Stops when no more articles found
- Respects rate limiting (1-3 second delays)

## Negative News Detection

### Weighted Keywords

| Keyword | Weight |
|---------|--------|
| loss, decline, drop | 2 |
| layoff | 3 |
| bankrupt, default, recession | 4 |
| fraud, corruption | 3 |

### Classification Rule

```python
is_negative = (
    negative_score >= 4
    or sentiment_score < -0.2
)
```

## Output Format

```json
[
  {
    "title": "Article Title",
    "url": "https://www.thejakartapost.com/...",
    "published_date": "2026-02-17",
    "category": "company",
    "author": "Author Name",
    "summary": "First 2-3 paragraphs...",
    "content": "Full article content...",
    "negative_score": 6,
    "sentiment_score": -0.35,
    "is_negative": true,
    "source": "jakartapost_business",
    "processed_at": "2026-02-17T10:30:00"
  }
]
```

## Output Files

- **Data**: `data/jakartapost_business.json`
- **Logs**: `logs/YYYY-MM-DD_errors.log`

## Configuration

Edit `agents/config.py` to customize:

```python
SCRAPE_DAYS = 2              # Default date range
MAX_PAGES = 20               # Max pages per category
REQUEST_DELAY_MIN = 1        # Min delay between requests
REQUEST_DELAY_MAX = 3        # Max delay between requests
NEGATIVE_THRESHOLD = 4       # Keyword score threshold
SENTIMENT_THRESHOLD = -0.2   # Sentiment threshold
```

## Project Structure

```
jakartapost_business/
├── agents/
│   ├── __init__.py
│   ├── config.py              # Configuration settings
│   ├── jakarta_post_listing.py # Listing scraper with pagination
│   ├── article_scraper.py     # Full content scraper
│   ├── text_cleaning.py       # Text cleaning
│   ├── negative_detection.py  # Weighted keyword + sentiment
│   ├── storage.py             # Append mode with deduplication
│   └── logging_agent.py       # Error logging
├── data/
│   └── jakartapost_business.json
├── logs/
│   └── YYYY-MM-DD_errors.log
├── pipeline.py
├── requirements.txt
└── README.md
```

## Key Features

### 📅 Configurable Date Range
- Default: Last 2 days
- Override with `--days N`

### 📄 Pagination Support
- Automatically crawls multiple pages per category
- Stops when reaching articles outside date range
- Respects MAX_PAGES limit

### 💾 Append Mode
- New articles merged with existing data
- Duplicates automatically detected and skipped
- Safe to run multiple times

### 🎯 Weighted Keyword Detection
- Different weights for different keywords
- More severe words (bankrupt, recession) = higher weight
- Combined with sentiment analysis

## Example Output

```
======================================================================
JAKARTA POST BUSINESS NEWS PIPELINE
======================================================================
Date Range: 2026-02-16 to 2026-02-17 (2 days)
Max Pages/Category: 20
Categories: company, market, regulation, economy
======================================================================

[1/5] Fetching articles from all categories...

  Scraping category: COMPANY
    Page 1... 12 articles
    Page 2... 10 articles
    Page 3... 8 articles
    → Oldest article outside date range, stopping
  ...

  Total unique articles found: 45

[2/5] Scraping full article content...
  Scraped: 43 successful, 2 failed

[3-4/5] Processing 43 articles...
  [1/43] [company] Article title here...
    → Analyzing sentiment...
    ✓ OK (score: 1, sentiment: 0.15)
  ...

[5/5] Saving results...
  Merged: 120 existing + 43 new = 163 total (43 new added)

======================================================================
PIPELINE COMPLETE
======================================================================
Total articles found: 45
Successfully scraped: 43
Successfully processed: 43
Negative articles this run: 5
----------------------------------------------------------------------
Total cumulative articles: 163
Total cumulative negative: 18
Output saved to: data/jakartapost_business.json
======================================================================
```
