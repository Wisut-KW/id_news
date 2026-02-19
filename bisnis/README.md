# Bisnis.com News Scraper

A Python script to scrape news articles from Bisnis.com website.

## Features

- Scrapes articles from the index page with category filter
- **Fetch full article content** from individual article pages
- **Translate articles from Indonesian to English** and save to separate file
- Configurable date range (defaults to last 2 days)
- Paginates automatically until date threshold is reached
- Appends new articles to JSON file
- Prevents duplicate entries (checks by URL)
- Extracts author, category, and content
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
python scraper.py --url "https://www.bisnis.com/index?categoryId=43"
```

### Combined options
```bash
python scraper.py --days 7 --fetch-content --output full_articles.json
```

### Translate articles to English
```bash
python scraper.py --translate
# or
python scraper.py -t
```

### Translate with custom output file
```bash
python scraper.py --translate --translated-output english_news.json
```

### Translate to Thai
```bash
python scraper.py --translate-thai
```

### Translate to both English and Thai
```bash
python scraper.py --translate --translate-thai
```

### Translate with content fetching
```bash
python scraper.py --fetch-content --translate
```

### Full workflow: content + both translations
```bash
python scraper.py --days 2 --fetch-content --translate --translate-thai
```

## Output Format

### Without --fetch-content (default)
```json
[
  {
    "title": "Article Title",
    "url": "https://ekonomi.bisnis.com/read/20260219/9/1954004/article-slug",
    "date": "2026-02-19",
    "channel": "Ekonomi",
    "scraped_at": "2026-02-19T08:55:09"
  }
]
```

### With --fetch-content
```json
[
  {
    "title": "Article Title",
    "url": "https://ekonomi.bisnis.com/read/20260219/9/1954004/article-slug",
    "date": "2026-02-19",
    "date_parsed": "2026-02-19",
    "channel": "Ekonomi",
    "author": "Author Name",
    "author_role": "Editor",
    "published_time": "2026-02-19T08:30:00",
    "modified_time": "2026-02-19T10:15:00",
    "summary": "Lead paragraph of the article...",
    "content": "Full article content with all paragraphs...",
    "content_html": "<div class='description'>...</div>",
    "categories": ["Ekonomi", "Bisnis"],
    "subcategory": "Investasi",
    "tags": ["ekonomi", "investasi", "indonesia"],
    "images": [
      {"url": "https://images.bisnis.com/...", "alt": "Image caption", "is_hero": true},
      {"url": "https://images.bisnis.com/...", "alt": "Another image"}
    ],
    "word_count": 1250,
    "scraped_at": "2026-02-19T08:55:09"
  }
]
```

### Translated output (--translate)
```json
[
  {
    "title": "RI Collaborates with US to Build Semiconductor Industry",
    "url": "https://ekonomi.bisnis.com/read/20260219/257/1953994/...",
    "date": "2026-02-19",
    "channel": "Manufacturing",
    "title_original": "RI Gandeng AS Bangun Industri Semikonduktor...",
    "channel_original": "Manufaktur",
    "translated_at": "2026-02-19T06:13:15",
    "translation_source": "id",
    "translation_target": "en"
  }
]
```

### Thai translation output (--translate-thai)
```json
[
  {
    "title": "RI ร่วมมือกับสหรัฐอเมริกาเพื่อสร้างอุตสาหกรรมเซมิคอนดักเตอร์",
    "url": "https://ekonomi.bisnis.com/read/20260219/257/1953994/...",
    "date": "2026-02-19",
    "channel": "การผลิต",
    "author": "อัคบาร์ อีวานดิโอ",
    "content": "Bisnis.com, จาการ์ตา – ประธานาธิบดีปราโบโว ซูเบียนโต ระบุว่ารัฐบาลของเขาประสบความสำเร็จในการประหยัดงบประมาณ...",
    "title_original": "RI Gandeng AS Bangun Industri Semikonduktor...",
    "channel_original": "Manufaktur",
    "author_original": "Akbar Evandio",
    "content_original": "Bisnis.com, JAKARTA – Presiden Prabowo Subianto menyatakan pemerintahannya berhasil...",
    "translated_at": "2026-02-19T06:19:48",
    "translation_source": "id",
    "translation_target": "th"
  }
]
```

## Data Fields

| Field | Description | With --fetch-content | With --translate |
|-------|-------------|---------------------|-----------------|
| `title` | Article headline | Always | Translated to target language |
| `url` | Full article URL | Always | Always |
| `date` | Publication date (ISO format) | Always | Always |
| `date_parsed` | Parsed datetime object | Optional | Always |
| `channel` | Article channel/section | Always | Translated to target language |
| `author` | Article author name | With -c flag | Translated to target language |
| `author_role` | Author's role/position | With -c flag | Translated to target language |
| `published_time` | Exact publication timestamp | With -c flag | Always |
| `modified_time` | Last modified timestamp | With -c flag | Always |
| `summary` | Lead paragraph/summary | With -c flag | Translated to target language |
| `content` | Full article text | With -c flag | Translated to target language |
| `content_html` | Raw HTML content | With -c flag | - |
| `categories` | List of categories | With -c flag | Translated to target language |
| `subcategory` | Primary subcategory | With -c flag | Translated to target language |
| `tags` | List of article tags | With -c flag | - |
| `images` | List of article images | With -c flag | - |
| `word_count` | Number of words in content | With -c flag | Always |
| `scraped_at` | When the article was scraped | Always | Always |
| `title_original` | Original Indonesian title | - | Always |
| `channel_original` | Original Indonesian channel | - | Always |
| `content_original` | Original Indonesian content | - | With -c flag |
| `translated_at` | When translation was done | - | Always |
| `translation_source` | Source language code | - | Always |
| `translation_target` | Target language code | - | Always |

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
- `news_data_translated_en.json` - English translated output (created with --translate flag)
- `news_data_translated_th.json` - Thai translated output (created with --translate-thai flag)
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

# Scrape and translate to English
python scraper.py --days 2 --translate

# Scrape and translate to Thai
python scraper.py --days 2 --translate-thai

# Scrape and translate to both English and Thai
python scraper.py --days 2 --translate --translate-thai

# Full workflow: scrape content and translate
python scraper.py --days 2 --fetch-content --translate
```

## URL Patterns

- **Listing page**: `https://www.bisnis.com/index?categoryId=43&page=N`
- **Article page**: `https://{channel}.bisnis.com/read/{YYYYMMDD}/{categoryId}/{articleId}/{slug}`

## Notes

- Dates on listing pages are in relative format (e.g., "5 menit yang lalu"), so the scraper extracts dates from article URLs
- The summary/description is not available on the index page and requires `--fetch-content` to get full article text
- CategoryId 43 corresponds to a specific news category filter on Bisnis.com
