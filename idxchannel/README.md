# IDX Channel News Scraper (with Translation & Date Range)

Automated pipeline to collect, scrape, translate, analyze, and store Indonesian business/finance news from IDX Channel with negative event detection.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Pipeline

**Default (last 3 days):**
```bash
python pipeline.py
```

**Custom date range (e.g., last 7 days):**
```bash
python pipeline.py --days 7
```

## Pipeline Flow

1. **IDX Channel Listing Agent** - Scrapes news from index pages with date parameter (`/indeks?date=DD/MM/YYYY`)
2. **Article Scraper Agent** - Scrapes full article content
3. **Text Cleaning Agent** - Cleans and normalizes text
4. **Translation Agent** - Translates Indonesian text to English
5. **Negative News Detection Agent** - Detects negative events using business/finance keywords + sentiment (on translated text)
6. **Storage Agent** - **Appends** results to existing JSON (no data loss)
7. **Logging Agent** - Logs errors and events

## Key Features

### 📅 Date Range Support (Using Index Page)
- **Uses IDX Channel index page** with date parameter: `/indeks?date=DD/MM/YYYY&idkanal=`
- Fetches articles for each specific date in the range
- Configurable lookback period (default: 3 days)
- Example: `--days 3` = today + yesterday + 2 days ago

**Why use index page?** The index page allows direct querying by date, giving accurate results for specific dates instead of relying on homepage listings which may be mixed.

### 💾 Append Mode (No Data Loss)
- New articles are **merged** with existing data
- Duplicates are automatically detected and skipped (based on URL)
- Safe to run multiple times per day

### 🌐 Translation
- Indonesian → English translation
- Uses Google Translate API (free)
- Fallback to local model if needed

### 📊 Smart Analytics
- Negative event detection on English text
- Business/finance focused keywords
- Sentiment analysis using VADER

## Output Format

```json
[
  {
    "title": "Original Indonesian Title",
    "title_original": "Original Indonesian Title",
    "title_translated": "English Translated Title",
    "url": "https://www.idxchannel.com/...",
    "published_date": "2026-02-17",
    "summary": "Indonesian summary...",
    "summary_original": "Indonesian summary...",
    "summary_translated": "English translated summary...",
    "content": "Indonesian content...",
    "content_original": "Indonesian content...",
    "content_translated": "English translated content...",
    "author": "Author Name",
    "category": "Market News",
    "negative_score": 3,
    "sentiment_score": -0.45,
    "is_negative": true,
    "source": "idxchannel",
    "language_original": "id",
    "language_translated": "en",
    "translation_method": "google_translate",
    "translation_success": true,
    "processed_at": "2026-02-17T10:30:00"
  }
]
```

## Output Files

- **Data**: `data/YYYY-MM-DD_idxchannel.json` (daily file with merged data)
- **Logs**: `logs/YYYY-MM-DD_errors.log`

## Project Structure

```
idxchannel/
├── agents/
│   ├── __init__.py
│   ├── idx_listing_scraper.py  # IDX Channel specific listing scraper
│   ├── article_scraper.py
│   ├── text_cleaning.py
│   ├── translation_agent.py    # Indonesian to English translation
│   ├── negative_detection.py   # Business/finance focused keywords
│   ├── storage.py              # Merge/append functionality
│   └── logging_agent.py
├── data/                       # JSON output files
├── logs/                       # Error logs
├── pipeline.py
├── requirements.txt
└── README.md
```

## Usage Examples

### Run with default 3-day window:
```bash
python pipeline.py
```

### Run with 7-day window:
```bash
python pipeline.py --days 7
```

### Run with 1-day window (today only):
```bash
python pipeline.py --days 1
```

## How Append Mode Works

1. **First Run:** Creates new JSON file with processed articles
2. **Subsequent Runs:** 
   - Loads existing JSON data
   - Processes new articles
   - Merges new with existing (skipping duplicates)
   - Saves updated file

Example output after multiple runs:
```
📊 Existing data: 15 articles (3 negative)
...
  Merged: 15 existing + 5 new = 20 total (5 new added)
```

## Translation Options

The pipeline supports two translation methods:

### Option 1: Google Translate (Default)
Uses `googletrans` library (free, no API key required):

```python
translation_agent = TranslationAgent(use_google_translate=True)
```

### Option 2: Local HuggingFace Model
Uses Helsinki-NLP model (works offline, no API calls):

```python
translation_agent = TranslationAgent(use_local_model=True)
```

**Note:** Local model requires more memory and slower but works offline.

## Configuration

Edit agents in `pipeline.py` or individual agent files to customize:
- Request delays (default: 2 seconds)
- Retry attempts (default: 3)
- Date range (default: 3 days)
- Translation method (Google Translate vs Local model)
- Negative keyword categories
- Sentiment thresholds

## Summary Statistics

After each run, the pipeline displays:
- Articles found in date range
- Successfully processed vs skipped
- Translation success rate
- Negative articles detected
- **Total cumulative count** in the JSON file

```
============================================================
PIPELINE COMPLETE
============================================================
Articles from last 3 days: 12
Successfully processed: 10
Skipped/Failed: 2
Successful translations: 10/10
Negative articles this run: 3
------------------------------------------------------------
Total articles in file: 25          ← Cumulative!
Total negative articles: 7
Output saved to: data/2026-02-17_idxchannel.json
============================================================
```
