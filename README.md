# Auto Scraper

An automated multi-site web scraping and synchronization tool that extracts content from target websites and syncs it to Dify knowledge base.

## Core Value

Automate the process of collecting and structuring content from multiple websites through configuration-based scheduling, significantly reducing manual maintenance costs. Built-in intelligent session pool and anti-crawler strategies ensure stability and high availability for long-term operations.

## Use Cases

- **Media Monitoring**: Real-time monitoring and archiving of financial, technology, and industry news websites.
- **Enterprise Knowledge Base**: Regular import of high-quality external content into internal knowledge management platforms.
- **Data Analysis Preparation**: Automated collection of raw text data for subsequent natural language processing and sentiment analysis.

## System Architecture

### Scheduler (main.py)
- Uses the schedule library to trigger scraping tasks hourly
- Supports graceful shutdown with SIGINT/SIGTERM handlers

### Crawler Module
- **BaseCrawler**: Provides common anti-crawler logic including session pool, dynamic UA, proxy, and delay mechanisms
- **ReutersCrawler**: Inherits from BaseCrawler, implements specific website parsing for both listing pages (get_article_links) and content pages (parse_article)

### Parser & Cleaner
- Utilizes BeautifulSoup to extract titles, content, and publication dates using configured CSS selectors
- Implements clean_article_content function for character cleaning and template text removal

### DifySync Module
- Assembles articles into Dify API-compliant JSON structure
- Synchronizes content through /v1/datasets/{dataset_id}/document/create_by_text endpoint

### Configuration Center (config.yaml)
- Centralized management of:
  - Target site information
  - Request delays
  - Retry counts
  - Scraping rules
  - Dify API endpoints and credentials

## Project Structure
├── config.yaml         # Configuration file
├── crawler.py         # Core crawler implementation
├── dify_sync.py       # Dify synchronization module
├── main.py           # Main program entry
└── run_sync.bat      # Windows execution script


## Setup and Configuration

1. Install dependencies:
```bash
pip install -r requirements.txt
```
2. Configure config.yaml with:
- Target website information
- Scraping rules
- Dify API settings


## Usage

```bash
# Windows
run_sync.bat

# Other systems
python main.py
```