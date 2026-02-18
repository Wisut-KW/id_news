# AGENTS.md — Jakarta Post Business Scraper

(Python Tech Stack Version)

---

# 1. Objective

Build a **Python-based news scraping agent** that:

* Scrapes Jakarta Post business categories
* Defaults to last **2 days**
* Allows configurable date range
* Paginates until date threshold reached
* Detects negative financial events
* Appends to existing dataset (never overwrite)
* Deduplicates by URL
* Logs errors without stopping execution

---

# 2. Source Categories

Base domain:

```
https://www.thejakartapost.com
```

Categories:

1. **Company**
   [https://www.thejakartapost.com/business/companies/latest?utm_source=(direct)&utm_medium=channel_companies](https://www.thejakartapost.com/business/companies/latest?utm_source=%28direct%29&utm_medium=channel_companies)

2. **Market**
   [https://www.thejakartapost.com/index.php/business/markets?utm_source=(direct)&utm_medium=header](https://www.thejakartapost.com/index.php/business/markets?utm_source=%28direct%29&utm_medium=header)

3. **Regulation**
   [https://www.thejakartapost.com/index.php/business/regulations?utm_source=(direct)&utm_medium=header](https://www.thejakartapost.com/index.php/business/regulations?utm_source=%28direct%29&utm_medium=header)

4. **Economy**
   [https://www.thejakartapost.com/index.php/business/economy?utm_source=(direct)&utm_medium=header](https://www.thejakartapost.com/index.php/business/economy?utm_source=%28direct%29&utm_medium=header)

---

# 3. Tech Stack (Python)

## Core Libraries

```text
Python 3.10+
requests
beautifulsoup4
lxml
python-dateutil
vaderSentiment (or transformers for sentiment)
json
logging
time
datetime
os
```

---

## Optional (Recommended for Production)

```text
pandas (data validation)
tenacity (retry logic)
aiohttp (async version)
schedule / APScheduler (automation)
```

---

# 4. Configuration

```python
SCRAPE_DAYS = 2          # DEFAULT DATE RANGE
APPEND_MODE = True       # Always append
OUTPUT_FILE = "data/jakartapost_business.json"
MAX_PAGES = 20           # Safety pagination limit
REQUEST_DELAY = (1, 3)   # Random delay seconds
NEGATIVE_THRESHOLD = 4
```

---

# 5. Date Window Logic

```python
start_date = today - timedelta(days=SCRAPE_DAYS - 1)
end_date = today
```

Keep only:

```
start_date <= published_date <= end_date
```

---

# 6. Pagination Logic

For each category:

### Crawl Until:

* Oldest article on page < start_date
  OR
* MAX_PAGES reached
  OR
* No articles found

---

## Pagination Algorithm

```python
page = 1

while page <= MAX_PAGES:

    fetch page
    
    extract article listings
    
    if empty:
        break

    stop_category = True

    for article in page_articles:

        parse published_date

        if published_date >= start_date:
            stop_category = False

        if start_date <= published_date <= end_date:
            scrape_full_article()

    if stop_category:
        break

    page += 1
```

---

# 7. Article Data Extraction

Extract:

* title
* url (cleaned, no tracking params)
* published_date (YYYY-MM-DD)
* category
* author (if available)
* summary (first 2–3 paragraphs)
* content (all `<p>` inside article body)
* processed_at (ISO timestamp)

Remove:

* script tags
* ads
* style tags
* unrelated blocks

---

# 8. Negative News Detection

## A. Weighted Keyword Score

```python
NEGATIVE_KEYWORDS = {
    "loss": 2,
    "decline": 2,
    "drop": 2,
    "layoff": 3,
    "bankrupt": 4,
    "default": 4,
    "lawsuit": 2,
    "corruption": 3,
    "fraud": 3,
    "recession": 4,
    "slowdown": 2,
    "sanction": 3,
    "investigation": 2,
    "penalty": 2
}
```

Calculate total weighted count.

---

## B. Sentiment Analysis

Using:

* `vaderSentiment`
  OR
* HuggingFace transformer model

Return:

```
sentiment_score ∈ [-1, 1]
```

---

## C. Classification Rule

```python
is_negative = (
    negative_score >= NEGATIVE_THRESHOLD
    or sentiment_score < -0.2
)
```

---

# 9. Append-Only Storage Logic

## Step 1 — Load Existing File

```python
if os.path.exists(OUTPUT_FILE):
    load existing JSON
else:
    existing_data = []
```

---

## Step 2 — Deduplicate

```python
existing_urls = {item["url"] for item in existing_data}

if new_article_url not in existing_urls:
    append
```

---

## Step 3 — Save

Always write:

```
existing_data + new_unique_articles
```

Never delete historical records.

---

# 10. Output Format (STRICT JSON)

```json
[
  {
    "title": "",
    "url": "",
    "published_date": "YYYY-MM-DD",
    "category": "",
    "author": "",
    "summary": "",
    "content": "",
    "negative_score": 0,
    "sentiment_score": 0.0,
    "is_negative": false,
    "source": "jakartapost_business",
    "processed_at": "YYYY-MM-DDTHH:MM:SS"
  }
]
```

---

# 11. Logging

Use Python `logging` module.

Log file:

```
logs/YYYY-MM-DD_errors.log
```

Log:

* Timestamp
* Category
* URL
* Exception type
* Error message

Continue execution if an article fails.

---

# 12. Rate Limiting

* Random delay between 1–3 seconds
* Respect robots.txt
* Do not exceed MAX_PAGES
* Use descriptive User-Agent header

---

# 13. Recommended Project Structure

```
project/
│
├── scraper/
│   ├── __init__.py
│   ├── config.py
│   ├── scraper.py
│   ├── parser.py
│   ├── classifier.py
│
├── data/
│   └── jakartapost_business.json
│
├── logs/
│
└── main.py
```

---

# 14. Final Clean Agent Instruction

You are a Python-based business news scraping agent.

You must:

1. Default SCRAPE_DAYS = 2 unless overridden.
2. Scrape all 4 Jakarta Post business categories.
3. Paginate until:

   * Oldest article < start_date
   * OR MAX_PAGES reached.
4. Extract full article content.
5. Clean text.
6. Compute negative_score and sentiment_score.
7. Classify is_negative.
8. Append results to existing JSON dataset.
9. Deduplicate by URL.
10. Log errors and continue execution.
11. Output strict JSON only.

Never overwrite historical data.
