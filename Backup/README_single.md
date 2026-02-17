# Indonesia News Pipeline - Single File Version

A complete, self-contained implementation of the news negative event detection system in a single Python file.

## Usage

### 1. Install Dependencies

```bash
pip install feedparser requests beautifulsoup4 lxml vaderSentiment
```

### 2. Run the Pipeline

```bash
python idxchannel_single.py
```

## Output

- **Data**: `data/YYYY-MM-DD_antaranews.json` - Processed articles with analysis
- **Logs**: `logs/YYYY-MM-DD_errors.log` - Error and event logs

## Features

All 6 agents combined into one file:

1. **RSS Ingestion Agent** - Fetches from Antara News RSS feed
2. **Article Scraper Agent** - Scrapes full content with retries and delays
3. **Text Cleaning Agent** - Normalizes text, removes HTML artifacts
4. **Negative News Detection Agent** - Keyword scoring + VADER sentiment analysis
5. **Storage Agent** - Saves results to timestamped JSON files
6. **Logging Agent** - Tracks errors and pipeline events

## Configuration

Edit the `Config` class at the top of the file to customize:

```python
class Config:
    RSS_URL = "https://en.antaranews.com/rss/news"
    DELAY_SECONDS = 2.0
    MAX_RETRIES = 3
    SENTIMENT_THRESHOLD = -0.3
    KEYWORD_THRESHOLD = 2
```

## Pipeline Flow

```
Fetch RSS → Filter Today's Articles → Scrape Content → 
Clean Text → Detect Negative Events → Save JSON + Log Errors
```
