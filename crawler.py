import requests
from bs4 import BeautifulSoup
import yaml
import time
from datetime import datetime
import logging
import random
from fake_useragent import UserAgent

class BaseCrawler:
    def __init__(self, site_config):
        self.config = site_config
        self.session = requests.Session()
        self.ua = UserAgent()
        self.session_pool = [self.create_new_session() for _ in range(3)]
        self.current_session_index = 0
        self.setup_session()

    def setup_session(self):
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        self.session.headers.update(headers)

        # Enable cookies if configured
        if self.config.get('cookies_enabled', True):
            self.session.cookies.clear()

        # Setup proxy if available
        if self.config.get('proxy_list'):
            proxy = random.choice(self.config['proxy_list'])
            self.session.proxies = {
                'http': proxy,
                'https': proxy
            }

    def create_new_session(self):
        session = requests.Session()
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        }
        session.headers.update(headers)
        return session

    def get_next_session(self):
        self.current_session_index = (self.current_session_index + 1) % len(self.session_pool)
        return self.session_pool[self.current_session_index]

class ReutersCrawler(BaseCrawler):
    def __init__(self, config_path='config.yaml'):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        site_config = config['sites']['reuters']
        super().__init__(site_config)
        
        # Save configurations
        self.parser_config = site_config['parser']
        self.base_url = site_config['base_url']
        self.request_delay = site_config.get('request_delay', 5)
        self.max_retries = site_config.get('max_retries', 3)

    def get_article_links(self):
        try:
            # Initial landing page visit to get cookies
            self.session.get('https://www.reuters.com/', timeout=30)
            time.sleep(2 + random.random() * 3)  # Random delay between 2-5 seconds
            
            # Rotate session settings before main request
            self.setup_session()
            
            # Add referrer for more legitimacy
            self.session.headers.update({
                'Referer': 'https://www.reuters.com/'
            })
            
            response = self.session.get(
                self.base_url,  # Use the base_url from class attribute
                allow_redirects=True,
                timeout=30
            )
            
            # Log response details for debugging
            logging.info(f"Response status: {response.status_code}")
            logging.info(f"Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Save HTML for debugging if no articles found
            if not soup.select(self.parser_config['article_selector']):
                logging.error("No articles found in the page. HTML structure might have changed.")
                with open('debug_page.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                logging.info("Saved HTML to debug_page.html for inspection")
                return []

            articles = []
            for article in soup.select(self.parser_config['article_selector']):
                link = article.find('a')
                if link and 'href' in link.attrs:
                    articles.append({
                        'url': f"https://www.reuters.com{link['href']}",
                        'title': link.get_text().strip()
                    })
            
            if articles:
                logging.info(f"Successfully found {len(articles)} articles")
            
            return articles

        except requests.exceptions.RequestException as e:
            logging.error(f"Request error: {e}")
            if hasattr(e.response, 'text'):
                logging.error(f"Response content: {e.response.text[:500]}...")
            return []
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return []

    def parse_article(self, url):
        try:
            # Add random delay between requests
            delay = self.request_delay * (1 + random.random() * 0.5)
            time.sleep(delay)
            
            # Get a fresh session
            session = self.get_next_session()
            
            # Visit homepage first
            session.get('https://www.reuters.com/', timeout=30)
            time.sleep(2 + random.random() * 2)
            
            # Add referrer
            session.headers.update({
                'Referer': 'https://www.reuters.com/',
                'User-Agent': self.ua.random  # Rotate user agent
            })
            
            response = session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')

            # Check for anti-bot measures
            if soup.find('div', {'class': ['captcha', 'robot-check', 'error-page']}):
                logging.error(f"Bot detection encountered for {url}")
                return None

            title = soup.select_one(self.parser_config['title_selector'])
            body = soup.select_one(self.parser_config['body_selector'])
            date = soup.select_one(self.parser_config['date_selector'])

            # Extract date with fallback to current date
            article_date = None
            if date:
                # Try multiple date attributes
                for attr in ['datetime', 'data-date', 'content']:
                    article_date = date.get(attr)
                    if article_date:
                        break
                # Try parsing text content if no attribute found
                if not article_date:
                    article_date = date.get_text().strip()

            # Use current date as fallback
            if not article_date:
                article_date = datetime.now().strftime('%Y-%m-%d')
                logging.warning(f"No date found for article {url}, using current date")

            return {
                'url': url,
                'title': title.get_text().strip() if title else '',
                'body': body.get_text().strip() if body else '',
                'date': article_date
            }
        except Exception as e:
            logging.error(f"Error parsing article {url}: {e}")
            return None