import requests
import yaml
import logging
from datetime import datetime

class DifySync:
    def __init__(self, config_path='config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.headers = {
            'Authorization': f"Bearer {self.config['dify']['api_key']}",
            'Content-Type': 'application/json'
        }

    def sync_article(self, article):
        try:
            # Get current timestamp for consistent timing
            current_time = datetime.now()
            
            # Create document name with current timestamp
            doc_name = self._create_doc_name(article, current_time)
            
            # Prepare the document content
            content = self._format_content(article, current_time)
            
            payload = {
                "name": doc_name,
                "text": content,
                "indexing_technique": "high_quality",
                "process_rule": {
                    "mode": "custom",
                    "rules": {
                        "pre_processing_rules": [],
                        "segmentation": {
                            "type": "paragraph",
                            "separator": "\n\n",
                            "max_tokens": 500
                        }
                    }
                },
                "metadata": {
                    "source": article['url'],
                    "document_name": doc_name,
                    "uploader": "reuters_sync",
                    "upload_date": current_time.isoformat(),
                    "last_update_date": current_time.isoformat(),
                    "category": "reuters_news",
                    "published_date": current_time.strftime('%Y-%m-%d')
                }
            }

            response = requests.post(
                f"{self.config['dify']['api_endpoint']}/v1/datasets/{self.config['dify']['dataset_id']}/document/create_by_text",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            # Log success with document details
            logging.info(f"Successfully synced article: {article['title']}")
            return True
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error syncing article to Dify: {e}")
            if hasattr(e.response, 'text'):
                logging.error(f"Response details: {e.response.text}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error while syncing article: {e}")
            return False

    def _create_doc_name(self, article, timestamp):
        # Use article title directly, with necessary cleaning and conversion
        title = article['title']\
            .replace('/', '-')\
            .replace('\\', '-')\
            .replace(':', '')\
            .replace('*', '')\
            .replace('?', '')\
            .replace('"', '')\
            .replace('<', '')\
            .replace('>', '')\
            .replace('|', '')\
            .strip()
        
        # If title is empty, use timestamp as fallback
        if not title:
            return timestamp.strftime('%Y%m%d_%H%M%S_untitled')
        
        # If title is too long, truncate to first 100 characters
        if len(title) > 100:
            title = title[:97] + '...'
        
        return title
        # Use provided timestamp for consistent timing
        date_str = timestamp.strftime('%Y%m%d_%H%M%S')
        
        # Create a URL-safe title slug
        title_slug = article['title'].lower()\
            .replace(' ', '-')\
            .replace('/', '-')\
            .replace('"', '')\
            .replace("'", '')\
            .replace('?', '')\
            .replace('!', '')\
            .replace(',', '')\
            .replace('.', '')\
            [:100]  # Truncate to reasonable length
        
        return f"{date_str}_{title_slug}"

    def _format_content(self, article, timestamp):
        # Format content with clear section breaks for better chunking
        sections = [
            f"# {article['title']}",
            f"Source URL: {article['url']}",
            f"Published Date: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "## Content",
            article['body']
        ]
        return "\n\n".join(sections)