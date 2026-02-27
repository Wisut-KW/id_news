# Jakarta Globe News Scraper

A comprehensive Python-based news scraper for scraping articles from Jakarta Globe (Indonesian news portal) with content extraction and multi-language translation support.

## Features

- **Article Listing Scraping**: Automatically paginates through article listings
- **Content Extraction**: Fetches full article content including author, timestamps, images
- **Duplicate Prevention**: Tracks existing URLs to prevent duplicate entries
- **Translation Support**: Translates articles to English and/or Thai
- **Configurable Date Range**: Scrape articles from the last N days (default: 2)
- **Logging**: Comprehensive logging of all operations

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

Required packages:
- beautifulsoup4>=4.11.0
- lxml>=4.9.0
- requests>=2.28.0
- deep-translator>=1.11.4

## Usage

### Basic Usage

```bash
# Scrape last 2 days (default)
python scraper.py

# Scrape last 7 days
python scraper.py --days 7
```

### Content Extraction

```bash
# Scrape with full content
python scraper.py --fetch-content

# Short flag
python scraper.py -c

# Content with custom days
python scraper.py --days 3 --fetch-content
```

### Translation

```bash
# Translate to English
python scraper.py --translate

# Translate to Thai
python scraper.py --translate-thai

# Translate to both languages
python scraper.py --translate --translate-thai

# Full workflow
python scraper.py --days 2 --fetch-content --translate --translate-thai
```

### Custom Options

```bash
# Custom output file
python scraper.py --output my_news.json

# Custom URL
python scraper.py --url "https://jakartaglobe.id/search/business/1"

# Custom translation output files
python scraper.py --translate --translated-output english_news.json --translated-thai-output thai_news.json
```

## Command-Line Arguments

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--days` | `-d` | 2 | Number of days back to scrape |
| `--output` | `-o` | news_data.json | Main output file |
| `--url` | | Base URL | Base URL to scrape |
| `--fetch-content` | `-c` | False | Fetch full article content |
| `--translate` | `-t` | False | Translate to English |
| `--translate-thai` | | False | Translate to Thai |
| `--translated-output` | | auto | English translation output file |
| `--translated-thai-output` | | auto | Thai translation output file |

## Output Files

- `news_data.json` - Main output: Original Indonesian data
- `news_data_translated_en.json` - English translation output
- `news_data_translated_th.json` - Thai translation output
- `scraper.log` - Operation log file

## Data Fields

### Core Fields (Always Present)

- `title` - Article headline
- `url` - Full article URL
- `date` - Publication date (ISO format)
- `category` - Article category/section
- `is_existing` - Whether article already existed
- `scraped_at` - Scrape timestamp

### Content Fields (with --fetch-content)

- `content` - Full article text
- `content_html` - Raw HTML content
- `summary` - Lead paragraph
- `author` - Author name
- `author_role` - Author position
- `published_time` - Exact publish time
- `modified_time` - Last modified time
- `categories` - List of categories
- `subcategory` - Primary subcategory
- `tags` - Article tags
- `images` - Article images
- `word_count` - Word count

### Translation Fields

- `title_original` - Original Indonesian title
- `content_original` - Original Indonesian content
- `category_original` - Original Indonesian category
- `author_original` - Original Indonesian author
- `translated_at` - Translation timestamp
- `translation_source` - Source language (id)
- `translation_target` - Target language (en/th)

## Target URLs

**Base URL:** `https://jakartaglobe.id/search/business/1`

**Pagination:**
- Page 1: `https://jakartaglobe.id/search/business/1`
- Page 2: `https://jakartaglobe.id/search/business/2`
- etc.

## Troubleshooting

### No articles found
- Check date range with `--days`
- Verify URL is accessible
- Check if HTML structure has changed

### Connection errors
- Check internet connection
- Verify URL is accessible

### Translation fails
- Check internet connection
- Verify deep-translator is installed
- Check rate limits

## Performance

- **Basic scraping**: ~2-3 seconds per page
- **With content**: ~1-2 seconds per article
- **With translation**: ~1-2 seconds per article per language

## License

MIT License
