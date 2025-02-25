import requests
import logging
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

def send_webhook(webhook_url, data):
    """Send a POST request to a webhook URL with the provided data."""
    try:
        # Extract query parameters from the webhook URL
        parsed_url = urlparse(webhook_url)
        query_params = parse_qs(parsed_url.query)
        
        # Add query parameters to the data payload
        # Convert from lists to single values (parse_qs returns lists)
        for key, value in query_params.items():
            if value and len(value) > 0:
                data[key] = value[0]
        
        # Remove query parameters from the URL
        clean_url = webhook_url.split('?')[0]
        
        logger.info(f"Attempting to send webhook to {clean_url} with data: {data}")
        response = requests.post(clean_url, json=data)
        response.raise_for_status()
        logger.info(f"Webhook sent: {data}")
    except requests.RequestException as e:
        logger.error(f"Webhook failed: {e}")
