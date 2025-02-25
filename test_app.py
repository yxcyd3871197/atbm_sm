import os
import sys
import subprocess

# Set environment variables
os.environ['API_KEY'] = 'test_api_key'
os.environ['GCP_BUCKET_NAME'] = 'test_bucket'
os.environ['GCP_SA_CREDENTIALS'] = '{}'

# Import the app after setting environment variables
sys.path.append('.')
from app import app

if __name__ == '__main__':
    # Run the app
    app.run(host='0.0.0.0', port=8080, debug=True)
