# AGENTS.md — Additional Source: IDX Channel

### Source Overview

IDX Channel is a major Indonesian business news portal focused on:

* Economic news
* Market updates
* Business & finance developments
* Corporate announcements
* Sector-specific trends

Website: [https://www.idxchannel.com/](https://www.idxchannel.com/) ([https://www.idxchannel.com/][1])

---

## Agent Integration

Add the following agent to your overall pipeline to pull news from IDX Channel and classify negative events.

---

## 1 — Source Endpoint(s)

Since no official RSS feed is known for IDX Channel, use the following content pages:

* **News list page**: [https://www.idxchannel.com/news](https://www.idxchannel.com/news) — general headlines and recent stories ([https://www.idxchannel.com/][2])
* **Market news**: [https://www.idxchannel.com/market-news](https://www.idxchannel.com/market-news) — financial/market specific updates ([https://www.idxchannel.com/][3])

---

## 2 — IDX Channel Scraper Agent

### Objective

Collect the latest news articles from IDX Channel **that were published today**.

### Tasks

#### Step 1 — Fetch List Pages

Programmatically GET the news listing pages:

* `/news`
* `/market-news`

Extract article links, titles, and timestamps (if available).

#### Step 2 — Filter by Today

Parse each article’s publication time and keep only those with dates matching your system date (e.g., `2026-02-18`). If the listing pages don’t include exact timestamps, assume articles on the first page are recent.

#### Step 3 — Scrape Full Article Content

For each selected URL:

1. Send HTTP GET
2. Parse with your HTML parser (`BeautifulSoup`)
3. Extract text from `<p>` and headline tags

Recommended fields to extract:

* **Title**
* **URL**
* **Published date** (parse from listing or article page)
* **Category** (if available)
* **Full content body**
* **Author** (if available)

---

## 3 — Text Cleaning

Same as your Antara pipeline:

* Trim whitespace
* Normalize text
* Remove scripts & ads
* Strip HTML tags

---

## 4 — Negative News Detection

Use **negative scoring + sentiment analysis** as with the Antara source:

* Keyword list for economic downturn, market crashes, layoffs, etc.
* Negative sentiment score below threshold
* Classify `is_negative` flag

This helps catch negative finance/business developments (e.g., big losses, market corrections).

---

## 5 — Output Format

Structure identical to the Antara output:

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
    "source": "idxchannel",
    "processed_at": ""
  }
]
```

Add `"source": "idxchannel"` for clarity.

---

## 6 — Agent Execution Flow

Integrate into your pipeline:

```text
1. Fetch IDX Channel news pages
2. Parse article list
3. Filter by today’s date
4. Scrape each article
5. Clean text
6. Detect negative events
7. Save JSON
```

---

## 7 — Logging

Same logging strategy as before: write link + error details to `logs/YYYY-MM-DD_errors.log` for scraper failures.

---

## 8 — Rate Limiting & Politeness

* Wait 1–3 seconds between requests
* Avoid brute-forcing deep pages
* Respect site structure (robots.txt)

---

## 9 — Notes on Source

* IDX Channel provides business and market updates in Indonesian and English; classification should be sensitive to economic context. ([https://www.idxchannel.com/][1])
* Because there is no confirmed public RSS feed, direct scraping is necessary (monitor for structural changes often).

---

## 10 — Future RSS Consideration

If IDX Channel later publishes a machine-readable feed (RSS/Atom), you can replace scraping with a feed parser for more robust ingestion.

---

If you’d like, I can also generate:

* A **scraper module code (Python)** specific to `idxchannel.com`,
* A combined runner in your Jupyter notebook that merges Antara and IDX Channel data,
* A normalized dataset format combining multiple sources,
* A **real-time Scheduler** for periodic scraping.

[1]: https://www.idxchannel.com/?utm_source=chatgpt.com "IDX Channel: Berita Ekonomi, Bisnis, Keuangan, Investasi ..."
[2]: https://www.idxchannel.com/news?utm_source=chatgpt.com "Berita Ekonomi Terkini Indonesia Dan Dunia Hari Ini"
[3]: https://www.idxchannel.com/market-news?utm_source=chatgpt.com "Berita Bursa Efek Indonesia Dan Market Terkini"
