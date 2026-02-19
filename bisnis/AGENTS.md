# AGENTS.md — Bisnis.com News Scraper

Complete implementation guide for scraping Bisnis.com news articles with content extraction and multi-language translation support.

---

## 1. Project Overview

### 1.1 Objective

Build a comprehensive Python-based news scraper that:

- Scrapes articles from Bisnis.com (Indonesian business news portal)
- Supports configurable date ranges (defaults to last 2 days)
- Automatically paginates through article listings
- Prevents duplicate entries by tracking URLs
- Extracts full article content from individual pages
- Translates articles from Indonesian to English and/or Thai
- Logs all operations and errors
- Appends new data to existing JSON files

### 1.2 Target URL

**Base URL:** `https://www.bisnis.com/index?categoryId=43`

**Pagination Pattern:**
- Page 1: `https://www.bisnis.com/index?categoryId=43&page=1`
- Page 2: `https://www.bisnis.com/index?categoryId=43&page=2`
- Page N: `https://www.bisnis.com/index?categoryId=43&page=N`

**Article URL Pattern:** `https://{channel}.bisnis.com/read/{YYYYMMDD}/{categoryId}/{articleId}/{slug}`

Example: `https://ekonomi.bisnis.com/read/20260219/9/1954004/opini-reformasi-hukum-persaingan-usaha`

---

## 2. File Structure

```
bisnis/
├── AGENTS.md                        # This implementation guide
├── README.md                        # User documentation
├── scraper.py                       # Main scraping script (Python 3)
├── requirements.txt                 # Python dependencies
├── news_data.json                   # Main output: Original Indonesian data
├── news_data_translated_en.json     # English translation output
├── news_data_translated_th.json     # Thai translation output
└── scraper.log                      # Operation log file
```

---

## 3. Implementation Details

### 3.1 Core Features

#### 3.1.1 Article Listing Scraping

**HTML Structure Analysis:**
- **Article Container:** `div.artItem`
- **Title:** `h4.artTitle` inside `a.artLink`
- **Channel:** `div.artChannel`
- **Date:** Extracted from URL pattern (not available as text on listing page)

**Process:**
1. Fetch listing page using `urllib` (site blocks `requests` library)
2. Parse HTML with BeautifulSoup
3. Find all `div.artItem` elements
4. Extract title, URL, and channel from each article
5. Extract date from URL using regex pattern
6. Check against existing URLs to avoid duplicates
7. Continue to next page until date threshold reached

#### 3.1.2 Content Extraction (with `--fetch-content`)

When content fetching is enabled, the scraper visits each individual article page to extract comprehensive data:

**Fields Extracted:**

| Field | Source | Description |
|-------|--------|-------------|
| `content` | `div.description`, `div.detail__content` | Full article text (all paragraphs) |
| `content_html` | Raw HTML | Original HTML structure |
| `author` | Meta tags, author sections | Article author name |
| `author_role` | Author sections | Author position/title |
| `published_time` | `meta[property="article:published_time"]` | Exact publish timestamp |
| `modified_time` | `meta[property="article:modified_time"]` | Last modified timestamp |
| `summary` | First paragraph | Lead paragraph of article |
| `word_count` | Calculated | Total word count |
| `categories` | Breadcrumb navigation | List of categories |
| `subcategory` | Last breadcrumb item | Primary category |
| `tags` | `meta[name="keywords"]` | Article tags/keywords |
| `images` | Article images | Array with URLs and alt text |

**Image Extraction:**
- Hero image detected from `meta[property="og:image"]`
- Content images extracted from article body
- Each image includes: `url`, `alt` text, and `is_hero` flag

#### 3.1.3 Translation Support

**Two-Stage Translation Process:**

1. **Scraping Stage:** Extract all articles in Indonesian
2. **Translation Stage:** Translate new articles to target language(s)

**Translation Features:**
- Uses Google Translate via `deep-translator` library
- Source language: Indonesian (id)
- Target languages: English (en) and Thai (th)
- Translates: title, content, author, channel, categories, subcategory
- Preserves original data in `*_original` fields
- Adds metadata: `translated_at`, `translation_source`, `translation_target`
- Implements rate limiting (0.5s delay between translations)
- Supports text chunking for long articles (>4000 chars)

**Translation Output Fields:**
- `title` - Translated title
- `title_original` - Original Indonesian title
- `content` - Translated content (if --fetch-content used)
- `content_original` - Original content
- `channel` - Translated channel name
- `channel_original` - Original channel name
- `author` - Translated author name
- `author_original` - Original author name
- `translated_at` - ISO timestamp
- `translation_source` - "id"
- `translation_target` - "en" or "th"

### 3.2 Technical Implementation

#### 3.2.1 HTTP Client

**Why urllib instead of requests:**
- Bisnis.com blocks requests from `requests` library (returns 403)
- Uses `urllib.request` with custom headers
- Implements gzip decompression
- Handles multiple encodings (UTF-8, ISO-8859-1, Windows-1252)
- SSL context bypass for compatibility

**Headers Used:**
```python
{
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}
```

#### 3.2.2 Date Extraction

Since listing pages don't show absolute dates:
- Extract date from URL pattern: `/read/YYYYMMDD/...`
- Parse using regex: `r'/read/(\d{4})(\d{2})(\d{2})/(\d+)/(\d+)/'`
- Convert to datetime object for filtering
- Compare against cutoff date (now - days_back)

#### 3.2.3 Duplicate Prevention

- Load existing URLs from output JSON
- Store in `set()` for O(1) lookup
- Skip articles with URLs already in set
- Add new URLs to set as they're processed

#### 3.2.4 Pagination Logic

1. Start at page 1
2. Fetch page and extract articles
3. Check if all articles on page are older than cutoff
4. If yes, stop pagination
5. If no, continue to next page
6. Safety limit: max 100 pages

---

## 4. Data Output Formats

### 4.1 Basic Scraping (without --fetch-content)

**File:** `news_data.json`

```json
[
  {
    "title": "Article Title in Indonesian",
    "url": "https://ekonomi.bisnis.com/read/20260219/9/1954004/slug",
    "date": "2026-02-19T00:00:00",
    "date_parsed": "2026-02-19 00:00:00",
    "channel": "Ekonomi",
    "is_existing": false,
    "scraped_at": "2026-02-19T08:30:00"
  }
]
```

### 4.2 With Content Extraction (--fetch-content)

**File:** `news_data.json` (enhanced with content)

```json
[
  {
    "title": "Article Title",
    "url": "https://ekonomi.bisnis.com/read/...",
    "date": "2026-02-19T00:00:00",
    "channel": "Ekonomi",
    "author": "Author Name",
    "author_role": "Editor",
    "published_time": "2026-02-19T08:30:00",
    "modified_time": "2026-02-19T10:15:00",
    "summary": "Lead paragraph...",
    "content": "Full article text...",
    "content_html": "<div class='description'>...</div>",
    "categories": ["Ekonomi", "Bisnis"],
    "subcategory": "Investasi",
    "tags": ["ekonomi", "investasi", "indonesia"],
    "images": [
      {"url": "https://images.bisnis.com/...", "alt": "Caption", "is_hero": true}
    ],
    "word_count": 1250,
    "scraped_at": "2026-02-19T08:30:00"
  }
]
```

### 4.3 English Translation (--translate)

**File:** `news_data_translated_en.json`

```json
[
  {
    "title": "Article Title in English",
    "url": "https://ekonomi.bisnis.com/read/...",
    "date": "2026-02-19T00:00:00",
    "channel": "Economy",
    "content": "Full article in English...",
    "title_original": "Article Title in Indonesian",
    "channel_original": "Ekonomi",
    "content_original": "Full article in Indonesian...",
    "translated_at": "2026-02-19T08:35:00",
    "translation_source": "id",
    "translation_target": "en"
  }
]
```

### 4.4 Thai Translation (--translate-thai)

**File:** `news_data_translated_th.json`

```json
[
  {
    "title": "หัวข้อบทความภาษาไทย",
    "url": "https://ekonomi.bisnis.com/read/...",
    "date": "2026-02-19T00:00:00",
    "channel": "เศรษฐกิจ",
    "content": "เนื้อหาบทความภาษาไทย...",
    "title_original": "Article Title in Indonesian",
    "channel_original": "Ekonomi",
    "content_original": "Full article in Indonesian...",
    "translated_at": "2026-02-19T08:40:00",
    "translation_source": "id",
    "translation_target": "th"
  }
]
```

---

## 5. Usage Guide

### 5.1 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Required packages:
# - beautifulsoup4>=4.11.0
# - lxml>=4.9.0
# - deep-translator>=1.11.4
```

### 5.2 Basic Usage

```bash
# Scrape last 2 days (default)
python scraper.py

# Scrape last 7 days
python scraper.py --days 7

# Custom output file
python scraper.py --output my_news.json

# Custom URL/category
python scraper.py --url "https://www.bisnis.com/index?categoryId=44"
```

### 5.3 Content Extraction

```bash
# Scrape with full content
python scraper.py --fetch-content

# Or use short flag
python scraper.py -c

# Content with custom days
python scraper.py --days 3 --fetch-content
```

### 5.4 Translation

```bash
# Translate to English
python scraper.py --translate

# Translate to Thai
python scraper.py --translate-thai

# Translate to both languages
python scraper.py --translate --translate-thai

# Translation with content
python scraper.py --fetch-content --translate

# Full workflow
python scraper.py --days 2 --fetch-content --translate --translate-thai
```

### 5.5 Combined Options

```bash
# Complete workflow
python scraper.py \
  --days 7 \
  --fetch-content \
  --translate \
  --translate-thai \
  --output news_data.json \
  --translated-output english_news.json \
  --translated-thai-output thai_news.json
```

---

## 6. Command-Line Arguments

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--days` | `-d` | 2 | Number of days back to scrape |
| `--output` | `-o` | news_data.json | Main output file |
| `--url` | | BASE_URL | Base URL to scrape |
| `--fetch-content` | `-c` | False | Fetch full article content |
| `--translate` | `-t` | False | Translate to English |
| `--translate-thai` | | False | Translate to Thai |
| `--translated-output` | | auto | English translation output file |
| `--translated-thai-output` | | auto | Thai translation output file |

---

## 7. Data Fields Reference

### 7.1 Core Fields (Always Present)

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Article headline |
| `url` | string | Full article URL |
| `date` | string | Publication date (ISO format) |
| `date_parsed` | datetime | Parsed datetime object |
| `channel` | string | Article channel/section |
| `is_existing` | boolean | Whether article already existed |
| `scraped_at` | string | Scrape timestamp |

### 7.2 Content Fields (--fetch-content)

| Field | Type | Description |
|-------|------|-------------|
| `content` | string | Full article text |
| `content_html` | string | Raw HTML content |
| `summary` | string | Lead paragraph |
| `author` | string | Author name |
| `author_role` | string | Author position |
| `published_time` | string | Exact publish time |
| `modified_time` | string | Last modified time |
| `categories` | array | List of categories |
| `subcategory` | string | Primary subcategory |
| `tags` | array | Article tags |
| `images` | array | Article images |
| `word_count` | integer | Word count |

### 7.3 Translation Fields

| Field | Type | Description |
|-------|------|-------------|
| `title_original` | string | Original Indonesian title |
| `content_original` | string | Original Indonesian content |
| `channel_original` | string | Original Indonesian channel |
| `author_original` | string | Original Indonesian author |
| `translated_at` | string | Translation timestamp |
| `translation_source` | string | Source language (id) |
| `translation_target` | string | Target language (en/th) |

---

## 8. Troubleshooting

### 8.1 Common Issues

**Issue:** 403 Forbidden error
**Solution:** Using urllib instead of requests library (already implemented)

**Issue:** No articles found
**Solution:** Check date range, verify URL is accessible, check HTML structure hasn't changed

**Issue:** Translation fails
**Solution:** Check internet connection, verify deep-translator is installed, check rate limits

**Issue:** Encoding errors
**Solution:** The scraper handles multiple encodings with fallback to UTF-8

### 8.2 Rate Limiting

- Built-in 0.5s delay between translation requests
- 0.5s delay between content fetching
- Respects server response times

### 8.3 Log Files

Check `scraper.log` for detailed operation logs including:
- Fetch attempts and results
- Translation progress
- Error messages
- Processing statistics

---

## 9. Performance Considerations

### 9.1 Speed

- **Basic scraping:** ~2-3 seconds per page
- **With content:** ~1-2 seconds per article
- **With translation:** ~1-2 seconds per article per language

### 9.2 File Sizes

Typical sizes for 90 articles:
- `news_data.json`: ~300-350 KB (basic), ~1-2 MB (with content)
- `news_data_translated_en.json`: ~600-700 KB
- `news_data_translated_th.json`: ~1.0-1.2 MB (Thai uses multi-byte characters)

### 9.3 Memory Usage

- Loads existing data for duplicate checking
- Processes articles in batches
- Suitable for scraping thousands of articles

---

## 10. Implementation History

| Date | Changes |
|------|---------|
| 2026-02-19 | Initial implementation based on jktpost pattern |
| 2026-02-19 | Switched from requests to urllib (403 errors) |
| 2026-02-19 | Added English translation support |
| 2026-02-19 | Added Thai translation support |
| 2026-02-19 | Enhanced content extraction with full article parsing |
| 2026-02-19 | Added metadata extraction (author, timestamps, images, etc.) |

---

## 11. Notes for Developers

### 11.1 HTML Structure Changes

If Bisnis.com updates their website structure:
1. Update selectors in `_find_articles_on_page()`
2. Update selectors in `_fetch_article_content()`
3. Test with sample URLs before full scrape

### 11.2 Adding New Languages

To add a new translation language:
1. Add new `--translate-{lang}` argument in `main()`
2. Add translator initialization in `__init__`
3. Add translation loop in `scrape()`
4. Add output file handling

### 11.3 Extending Content Extraction

To extract additional fields:
1. Add field to `content_data` dict in `_fetch_article_content()`
2. Add extraction logic using BeautifulSoup selectors
3. Update documentation

---

## 12. Example Workflows

### 12.1 Daily News Update

```bash
# Run daily to get last 2 days with English translation
python scraper.py --translate
```

### 12.2 Weekly Archive with Full Content

```bash
# Get last 7 days with full content and both translations
python scraper.py --days 7 --fetch-content --translate --translate-thai
```

### 12.3 Research Dataset

```bash
# Get comprehensive dataset for analysis
python scraper.py \
  --days 30 \
  --fetch-content \
  --translate \
  --output research_data.json \
  --translated-output research_en.json
```

---

**End of Implementation Guide**
