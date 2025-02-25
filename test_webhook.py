import os
import sys
import json
from urllib.parse import urlparse, parse_qs

# Add the current directory to the Python path
sys.path.append('.')

# Import the webhook function
from services.webhook import send_webhook

def test_webhook():
    # Test URL with query parameters
    webhook_url = "https://webhook.site/e75bd100-541d-458a-9535-0762dc634b59?record_id=438"
    
    # Test data
    data = {
        "endpoint": "/v1/ffmpeg/compose",
        "code": 200,
        "id": "create-podcast-video",
        "job_id": "155eb47c-1bf5-4bbf-a712-f90e331a0c6a",
        "response": [
            {
                "file_url": "https://storage.googleapis.com/podcast-bucket-gunda/155eb47c-1bf5-4bbf-a712-f90e331a0c6a_output_0.mp4",
                "filesize": 75599473,
                "duration": 1934.56
            }
        ],
        "message": "success",
        "pid": 14,
        "queue_id": 140461497017344,
        "run_time": 841.591,
        "queue_time": 0.001,
        "total_time": 841.592,
        "queue_length": 0,
        "build_number": 120
    }
    
    # Parse the URL to extract query parameters
    parsed_url = urlparse(webhook_url)
    query_params = parse_qs(parsed_url.query)
    
    print(f"Original URL: {webhook_url}")
    print(f"Parsed query parameters: {query_params}")
    
    # Add query parameters to the data payload
    for key, value in query_params.items():
        if value and len(value) > 0:
            data[key] = value[0]
    
    # Remove query parameters from the URL
    clean_url = webhook_url.split('?')[0]
    
    print(f"Clean URL: {clean_url}")
    print(f"Data with query parameters: {json.dumps(data, indent=2)}")
    
    # Note: We're not actually sending the webhook to avoid making real HTTP requests
    print("In a real scenario, this would send a POST request to the webhook URL with the data payload")

if __name__ == "__main__":
    test_webhook()
