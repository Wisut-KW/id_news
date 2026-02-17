
---

# AGENTS.md

## Indonesia Local News Negative Event Detection System

---

## 1. Project Overview

This project builds an automated pipeline to:

1. Collect daily news from RSS
2. Scrape full article content
3. Detect negative news
4. Store enriched structured data

News Source:

* Antara News
* Website: [https://en.antaranews.com/](https://en.antaranews.com/)
* RSS Feed: [https://en.antaranews.com/rss/news](https://en.antaranews.com/rss/news)

The system runs in **Jupyter Notebook (.ipynb)**.

---

## 2. System Architecture

The pipeline consists of the following logical agents:

1. **RSS Ingestion Agent**
2. **Article Scraper Agent**
3. **Text Cleaning Agent**
4. **Negative News Detection Agent**
5. **Storage Agent**
6. **Logging Agent**

---

## 3. End-to-End Flow

```
1. Fetch RSS Feed
2. Filter Today's Articles
3. Scrape Full Content
4. Clean Text
5. Detect Negative News
6. Enrich Article Metadata
7. Save JSON Output
8. Log Errors
```

---

## 4. Environment Requirements

### Python Version

* Python 3.10+

### Required Libraries

```bash
pip install requests beautifulsoup4 feedparser pandas lxml python-dateutil nltk transformers torch
```

---

## 5. Folder Structure

```
project/
│
├── AGENTS.md
├── news_pipeline.ipynb
├── data/
│   └── YYYY-MM-DD_antaranews.json
└── logs/
```

---

## 6. Agent Specifications

---

### 6.1 RSS Ingestion Agent

**Objective:**
Retrieve structured news metadata from RSS feed.

**Input:**
RSS URL

**Output Fields:**

* title
* url
* published_date
* summary

**Filter Logic:**

* Only keep articles where `published_date == today`

---

### 6.2 Article Scraper Agent

**Objective:**
Extract full article body from each news URL.

**Process:**

* Send HTTP GET request
* Parse HTML with BeautifulSoup
* Extract paragraph tags
* Join as full text

**Safeguards:**

* 2-second delay between requests
* Max 3 retries
* Log failed URLs

---

### 6.3 Text Cleaning Agent

**Tasks:**

* Remove extra whitespace
* Remove HTML artifacts
* Normalize unicode
* Remove “ANTARA -” prefix
* Strip unwanted scripts

---

### 6.4 Negative News Detection Agent

This agent determines whether an article contains negative events.

#### Layer 1 — Keyword Detection

Example keyword categories:

* Natural disasters (earthquake, flood, tsunami)
* Crime (arrested, murder, corruption)
* Accident (crash, explosion, fire)
* Health (outbreak, virus)
* Conflict (protest, violence)
* Economic distress (bankruptcy, inflation)

**Scoring Method:**

* Count keyword occurrences
* Assign `negative_score`

---

#### Layer 2 — Sentiment Analysis

Using VADER:

* Compute compound sentiment score
* Negative if compound < -0.3

---

#### Final Decision Logic

```
If keyword_score >= 2 OR sentiment_score < -0.3:
    is_negative = True
Else:
    is_negative = False
```

---

## 7. Output Data Structure

All processed articles are saved as:

```
data/YYYY-MM-DD_antaranews.json
```

### JSON Schema

```json
[
  {
    "title": "",
    "url": "",
    "published_date": "",
    "summary": "",
    "content": "",
    "negative_score": 0,
    "sentiment_score": 0.0,
    "is_negative": false,
    "processed_at": ""
  }
]
```

---

## 8. Logging Strategy

Errors are written to:

```
logs/YYYY-MM-DD_errors.log
```

Log Format:

```
URL | error_message
```

---

## 9. Performance & Safety Rules

* Prefer RSS over homepage scraping
* Respect robots.txt
* Add delay between requests
* Avoid duplicate processing
* Use URL as unique identifier
* Skip empty content
* Do not aggressively crawl

---

## 10. Execution Steps in Notebook

### Cell 1 — Import Libraries

### Cell 2 — Configuration Variables

### Cell 3 — Define RSS Functions

### Cell 4 — Define Scraper Functions

### Cell 5 — Define Negative Detection Functions

### Cell 6 — Run Pipeline

### Cell 7 — Save Results

---

## 11. Future Extensions

Planned improvements:

* Transformer-based classifier
* Event-type classification (Natural Disaster, Crime, Health, etc.)
* Named Entity Recognition (location extraction)
* Province-level aggregation
* Real-time alert trigger
* API deployment (FastAPI)
* Dashboard monitoring

---

## 12. Pipeline Summary

This system provides:

* Automated daily news ingestion
* Full article extraction
* Negative event detection
* Structured JSON output
* Error logging
* Modular agent design

---