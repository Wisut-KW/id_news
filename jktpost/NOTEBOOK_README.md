# Jakarta Post Scraper - Jupyter Notebook Version

Interactive notebook version of the Jakarta Post business news scraper.

## Files

- `scraper.ipynb` - Jupyter notebook with interactive scraper
- `scraper.py` - Command-line version (same logic)

## Quick Start

1. **Open the notebook:**
   ```bash
   jupyter notebook scraper.ipynb
   # or
   jupyter lab scraper.ipynb
   ```

2. **Run cells sequentially:**
   - Cell 1-2: Install dependencies and import libraries
   - Cell 3: Configure scraping parameters
   - Cell 4: Define scraper class
   - Cell 5: Run the scraper
   - Cell 6-7: View results
   - Cell 8-9: Export and analyze data
   - Cell 10: Interactive search

## Configuration

Edit **Cell 3** to customize:

```python
DAYS_BACK = 2              # Number of days back to scrape
OUTPUT_FILE = "news_data.json"
BASE_URL = "https://www.thejakartapost.com/business/latest"
FETCH_CONTENT = True       # Set to True for full content
```

## Notebook Features

### Interactive Configuration
- Easy parameter adjustment in dedicated cells
- Visual feedback during scraping
- Progress indicators for content fetching

### Data Exploration
- Built-in summary statistics
- Sample article display
- Pandas DataFrame conversion
- CSV export option
- Keyword search functionality

### Advantages Over CLI Version
1. **Interactive:** Change parameters and re-run easily
2. **Visual:** See results immediately in the notebook
3. **Exploratory:** Built-in tools for data analysis
4. **Educational:** Step-by-step execution shows how it works

## Example Workflow

```python
# Cell 3: Set configuration
DAYS_BACK = 7
FETCH_CONTENT = True

# Cell 5: Run scraper
# (Shows progress in real-time)

# Cell 6: View summary
# Articles by date, content stats

# Cell 8: Export to CSV
# For use in Excel or other tools

# Cell 10: Search articles
keyword = "mining"  # Find specific topics
```

## Output

Same JSON format as CLI version:
```json
{
  "title": "Article Title",
  "url": "https://www.thejakartapost.com/business/...",
  "date": "2026-02-18T12:32:56",
  "summary": "Brief excerpt...",
  "author": "Author Name",
  "category": "Companies",
  "tags": ["tag1", "tag2"],
  "content": "Full article text...",
  "scraped_at": "2026-02-18T08:55:09"
}
```

## Tips

1. **First run:** Start with `FETCH_CONTENT = False` for faster testing
2. **Re-scraping:** Change `DAYS_BACK` to get more/less articles
3. **Analysis:** Use the Pandas DataFrame for complex filtering
4. **Export:** CSV export makes data easy to share

## Running Without Jupyter

If you don't have Jupyter installed, use the CLI version:
```bash
python scraper.py --days 7 --fetch-content
```
