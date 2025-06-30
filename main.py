import schedule
import time
import logging
import signal
import sys
from crawler import ReutersCrawler
from dify_sync import DifySync
import yaml

import warnings
warnings.filterwarnings('ignore')

# Global flag for graceful shutdown
shutdown_flag = False

def signal_handler(signum, frame):
    global shutdown_flag
    logging.info("Shutdown signal received. Waiting for current sync to complete...")
    shutdown_flag = True

def sync_articles():
    # Load all sites from configuration file
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    dify = DifySync()
    total_articles = 0
    successful_syncs = 0
    failed_syncs = 0
    
    # Iterate through all configured sites
    for site_id, site_config in config['sites'].items():
        try:
            # Dynamically import and instantiate crawler
            crawler_class = get_crawler_class(site_id)
            crawler = crawler_class()
            
            logging.info(f"Starting article collection from {site_config['name']}...")
            articles = crawler.get_article_links()
            
            if not articles:
                logging.error(f"No articles found from {site_config['name']}")
                continue
            
            total_articles += len(articles)
            
            # Process articles
            for index, article_link in enumerate(articles, 1):
                if shutdown_flag:
                    break
                    
                try:
                    article_data = crawler.parse_article(article_link['url'])
                    if article_data:
                        article_data = clean_article_content(article_data)
                        article_data['source'] = site_config['name']
                        if dify.sync_article(article_data):
                            successful_syncs += 1
                        else:
                            failed_syncs += 1
                except Exception as e:
                    logging.error(f"Error processing article: {str(e)}")
                    failed_syncs += 1
                    
        except Exception as e:
            logging.error(f"Error processing site {site_config['name']}: {str(e)}")
    
    # Output summary report
    logging.info("\nSync Summary:")
    logging.info(f"Total articles found: {total_articles}")
    logging.info(f"Successfully synced: {successful_syncs}")
    logging.info(f"Failed: {failed_syncs}")
    if total_articles > 0:
        logging.info(f"Success rate: {(successful_syncs/total_articles)*100:.2f}%\n")

def clean_article_content(article_data):
    # Remove extra whitespace and normalize line endings
    article_data['body'] = ' '.join(article_data['body'].split())
    
    # Remove any unwanted text patterns
    unwanted_patterns = [
        "EmailXLinkedin",
        "ShareXFacebookXLinkedinXEmail",
        "Purchase Licensing Rights"
    ]
    
    for pattern in unwanted_patterns:
        article_data['body'] = article_data['body'].replace(pattern, '')
    
    return article_data

# Crawler class mapping dictionary
CRAWLER_CLASSES = {
    'reuters': ReutersCrawler
}

def get_crawler_class(site_id):
    """Get the appropriate crawler class for a given site ID.
    
    Args:
        site_id (str): The identifier of the site to crawl
        
    Returns:
        class: The crawler class for the specified site
        
    Raises:
        ValueError: If no crawler class is found for the given site ID
    """
    crawler_class = CRAWLER_CLASSES.get(site_id)
    if not crawler_class:
        raise ValueError(f"No crawler class found for site: {site_id}")
    return crawler_class

def main():
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run immediately on start
    sync_articles()
    
    # Schedule to run every hour
    schedule.every().hour.at(":00").do(sync_articles)
    
    while not shutdown_flag:
        schedule.run_pending()
        time.sleep(60)
    
    logging.info("Shutdown complete")
    sys.exit(0)

if __name__ == "__main__":
    main()