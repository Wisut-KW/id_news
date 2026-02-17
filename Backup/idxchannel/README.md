# Indonesia Local News Negative Event Detection System

Automated pipeline to collect, scrape, analyze, and store Indonesian news with negative event detection.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Pipeline

```bash
python pipeline.py
```

## Pipeline Flow

1. **RSS Ingestion Agent** - Fetches articles from Antara News RSS
2. **Article Scraper Agent** - Scrapes full article content
3. **Text Cleaning Agent** - Cleans and normalizes text
4. **Negative News Detection Agent** - Detects negative events using keywords + sentiment
5. **Storage Agent** - Saves results to JSON
6. **Logging Agent** - Logs errors and events

## Output

- **Data**: `data/YYYY-MM-DD_antaranews.json`
- **Logs**: `logs/YYYY-MM-DD_errors.log`

## Project Structure

```
idxchannel/
├── agents/
│   ├── __init__.py
│   ├── rss_ingestion.py
│   ├── article_scraper.py
│   ├── text_cleaning.py
│   ├── negative_detection.py
│   ├── storage.py
│   └── logging_agent.py
├── data/
├── logs/
├── pipeline.py
├── requirements.txt
└── README.md
```

## Configuration

Edit agents in `pipeline.py` or individual agent files to customize:
- RSS feed URL
- Request delays
- Retry attempts
- Negative keyword categories
- Sentiment thresholds
