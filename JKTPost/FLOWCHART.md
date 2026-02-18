# Jakarta Post Business News Scraper - Flow Process Chart

## Overall Pipeline Flow

```mermaid
flowchart TD
    Start([Start Pipeline]) --> Config[Load Configuration<br/>- Date range<br/>- Categories<br/>- Max pages]
    Config --> Stats[Show Existing Stats<br/>from Storage Agent]
    
    Stats --> Fetch[1. Fetch Listings<br/>JakartaPostListingAgent]
    
    subgraph Listing_Process[Listing Process - Per Category]
        direction TB
        CatPage[Fetch Category Page] --> ParseList[Parse Article Listings]
        ParseList --> FilterCat{Is Article URL?<br/>Has date pattern}
        FilterCat -->|No| SkipCat[Skip Category Page]
        FilterCat -->|Yes| CheckDate{Within Date<br/>Range?}
        CheckDate -->|No| StopCat[Stop Pagination]
        CheckDate -->|Yes| AddList[Add to List]
        AddList --> NextPage{More Pages?}
        NextPage -->|Yes| CatPage
        NextPage -->|No| StopCat
    end
    
    Fetch --> Listing_Process
    Listing_Process --> FilterExist[2. Filter Existing URLs<br/>Skip already scraped articles]
    
    FilterExist --> Scrape[3. Scrape Articles<br/>ArticleScraperAgent]
    
    subgraph Scraping_Process[Scraping Process - Per Article]
        direction TB
        FetchArticle[Fetch Article URL] --> Extract[Extract Content]
        Extract --> CheckAMP{Content Found?}
        CheckAMP -->|No| TryAMP[Try AMP Version]
        CheckAMP -->|Yes| CleanScrape[Clean Content]
        TryAMP --> CleanScrape
        CleanScrape --> MergeData[Merge with Metadata]
    end
    
    Scrape --> Scraping_Process
    Scraping_Process --> Process[4. Process Articles]
    
    subgraph Processing_Process[Processing - Per Article]
        direction TB
        CleanText[Clean Text<br/>TextCleaningAgent] --> CheckLen{Content > 100 chars?}
        CheckLen -->|No| SkipShort[Skip - Too Short]
        CheckLen -->|Yes| Analyze[Analyze Sentiment<br/>NegativeNewsDetectionAgent]
        Analyze --> CalcScore[Calculate:<br/>- Negative Score<br/>- Sentiment Score<br/>- Is Negative?]
    end
    
    Process --> Processing_Process
    Processing_Process --> Save[5. Save Results<br/>StorageAgent]
    
    subgraph Save_Process[Save Process]
        direction TB
        LoadExist[Load Existing Data] --> NormURLs[Normalize All URLs]
        NormURLs --> MergeNew[Merge with New Articles<br/>Deduplicate by URL]
        MergeNew --> SaveFile[Save to JSON File]
    end
    
    Save --> Save_Process
    Save_Process --> Report[Generate Report<br/>- Articles found<br/>- Successfully scraped<br/>- Negative articles<br/>- Total cumulative]
    Report --> End([End Pipeline])
    
    %% Error handling
    Fetch -.->|Error| LogError[Log Error<br/>Continue]
    Scrape -.->|Error| LogError
    Process -.->|Error| LogError
    LogError --> Continue[Continue with<br/>next article]
```

---

## Agent Interactions

```mermaid
sequenceDiagram
    participant Main as Main Pipeline
    participant Config as Config
    participant Listing as JakartaPost<br/>Listing Agent
    participant Scraper as Article<br/>Scraper Agent
    participant TextClean as Text Cleaning<br/>Agent
    participant Detect as Negative<br/>Detection Agent
    participant Storage as Storage<br/>Agent
    participant Logger as Logging<br/>Agent

    Main->>Config: Get date range, categories
    Config-->>Main: start_date, end_date
    
    Main->>Storage: get_stats()
    Storage-->>Main: existing count
    
    loop For each category
        Main->>Listing: fetch_category()
        loop Pagination
            Listing->>Listing: Fetch page
            Listing->>Listing: Parse listings
            Listing->>Listing: Filter category URLs
            Listing-->>Main: Article metadata
        end
    end
    
    Main->>Storage: get_existing_urls()
    Storage-->>Main: Set of existing URLs
    Main->>Main: Filter existing URLs
    
    loop For each new article
        Main->>Scraper: scrape_article(url)
        Scraper->>Scraper: Fetch & extract
        Scraper-->>Main: content, summary, author
        
        Main->>TextClean: clean_article(article)
        TextClean-->>Main: cleaned article
        
        Main->>Detect: analyze(content)
        Detect-->>Main: negative_score, sentiment_score, is_negative
    end
    
    Main->>Storage: save(processed_articles)
    Storage->>Storage: Normalize URLs
    Storage->>Storage: Deduplicate
    Storage->>Storage: Write to file
    Storage-->>Main: filepath
    
    Main->>Logger: log_info()/log_error()
```

---

## Data Flow

```mermaid
flowchart LR
    subgraph Input[Input]
        URL1[Category URLs]
        Config[Config Settings]
    end
    
    subgraph RawData[Raw Data]
        Listings[Article Listings<br/>- title<br/>- url<br/>- published_date<br/>- category]
    end
    
    subgraph Enriched[Enriched Data]
        FullArticles[Full Articles<br/>+ content<br/>+ summary<br/>+ author]
    end
    
    subgraph Processed[Processed Data]
        Analyzed[Analyzed Articles<br/>+ negative_score<br/>+ sentiment_score<br/>+ is_negative<br/>+ source<br/>+ processed_at]
    end
    
    subgraph Output[Output - JSON]
        File[data/jakartapost_business.json]
    end
    
    URL1 --> |JakartaPostListingAgent| Listings
    Config --> Listings
    Listings --> |ArticleScraperAgent| FullArticles
    FullArticles --> |TextCleaningAgent +<br/>NegativeNewsDetectionAgent| Analyzed
    Analyzed --> |StorageAgent| File
```

---

## URL Filtering Logic

```mermaid
flowchart TD
    URL[Raw URL] --> Check1{Has /YYYY/MM/DD<br/>pattern?}
    Check1 -->|No| Reject1[Reject<br/>Category Page]
    Check1 -->|Yes| Check2{Already in<br/>existing data?}
    Check2 -->|Yes| Reject2[Reject<br/>Duplicate]
    Check2 -->|No| Check3{Content length<br/>> 100 chars?}
    Check3 -->|No| Reject3[Reject<br/>Too Short]
    Check3 -->|Yes| Accept[Accept Article]
    
    Reject1 --> Log1[Log Skip]
    Reject2 --> Log1
    Reject3 --> Log1
    Accept --> Scrape[Scrape & Process]
```

---

## Negative News Detection

```mermaid
flowchart LR
    subgraph Keywords[Keyword Scoring]
        Word1[loss: 2]
        Word2[decline: 2]
        Word3[drop: 2]
        Word4[layoff: 3]
        Word5[bankrupt: 4]
        Word6[default: 4]
        Word7[fraud: 3]
        Word8[recession: 4]
    end
    
    Content[Article Content] --> TextClean[Text Cleaning]
    TextClean --> KeywordCount[Count Keywords<br/>Weighted Score]
    TextClean --> Sentiment[VADER Sentiment<br/>Analysis]
    
    KeywordCount --> Score{Total Score >= 4<br/>OR<br/>Sentiment < -0.2?}
    Sentiment --> Score
    
    Score -->|Yes| Negative[Is Negative = true]
    Score -->|No| NotNegative[Is Negative = false]
    
    Negative --> Save[Save with scores]
    NotNegative --> Save
```

---

## File Structure

```
project/
│
├── pipeline.py                 # Main orchestration
├── cleanup_data.py             # Data cleaning utility
│
├── agents/
│   ├── config.py              # Configuration settings
│   ├── jakarta_post_listing.py # Fetch article listings
│   ├── article_scraper.py     # Scrape full articles
│   ├── text_cleaning.py       # Clean text content
│   ├── negative_detection.py  # Sentiment analysis
│   ├── storage.py             # Save/load JSON data
│   └── logging_agent.py       # Error/info logging
│
├── data/
│   └── jakartapost_business.json  # Output data
│
└── logs/                      # Error logs
    └── YYYY-MM-DD_errors.log
```

---

## Configuration

```mermaid
flowchart TD
    Config[Config.py] --> Date[SCRAPE_DAYS = 2<br/>Default date range]
    Config --> Pages[MAX_PAGES = 20<br/>Pagination limit]
    Config --> Delay[REQUEST_DELAY = 1-3s<br/>Rate limiting]
    Config --> Output[OUTPUT_FILENAME<br/>jakartapost_business.json]
    Config --> Cats[CATEGORIES<br/>- Company<br/>- Market<br/>- Regulation<br/>- Economy]
    Config --> Threshold[NEGATIVE_THRESHOLD = 4<br/>Keyword score threshold]
```

---

## Key Improvements Made

| Issue | Solution |
|-------|----------|
| Category pages scraped | URL pattern filter (`/YYYY/MM/DD/`) |
| Duplicate URLs | Normalization (http→https, www consistency) |
| Re-scraping existing | Pre-filter before scraping step |
| Multiple URL formats | Always normalize to single format |
| Data corruption | Append-only, never overwrite |

---

## Run Commands

```bash
# Run pipeline with default settings (2 days, 20 pages)
python pipeline.py

# Run with custom days
python pipeline.py --days 5

# Run with fewer pages for testing
python pipeline.py --max-pages 2

# Clean existing data (remove duplicates/categories)
python cleanup_data.py
```
