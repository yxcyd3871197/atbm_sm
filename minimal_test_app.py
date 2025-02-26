import os
import sys
import json
import logging
import uuid
import threading
import time
import requests  # Import the requests module
from flask import Flask, request, jsonify
from urllib.parse import urlparse, parse_qs

# Set environment variables
os.environ['API_KEY'] = 'test_api_key'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a minimal Flask app
app = Flask(__name__)

# Mock functions
def mock_download_file(url, path):
    return os.path.join(path, os.path.basename(url))

def mock_upload_file(filename):
    return f"https://storage.googleapis.com/test-bucket/{os.path.basename(filename)}"

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
        
        logger.info(f"Webhook would be sent to: {clean_url}")
        logger.info(f"Webhook data: {json.dumps(data, indent=2)}")
        
        # In a real scenario, we would send the webhook
        response = requests.post(clean_url, json=data)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Webhook failed: {e}")

def process_ffmpeg_compose(data, job_id, return_command=False):
    """Mock implementation of process_ffmpeg_compose"""
    # Build FFmpeg command
    command = ["ffmpeg"]
    
    # Add inputs
    for input_data in data["inputs"]:
        if "options" in input_data:
            for option in input_data["options"]:
                command.append(option["option"])
                if "argument" in option and option["argument"] is not None:
                    command.append(str(option["argument"]))
        input_path = mock_download_file(input_data["file_url"], "/tmp")
        command.extend(["-i", input_path])
    
    # Add filters
    if data.get("filters"):
        filter_complex = ";".join(filter_obj["filter"] for filter_obj in data["filters"])
        command.extend(["-filter_complex", filter_complex])
    
    # Add outputs
    output_filenames = []
    for i, output in enumerate(data["outputs"]):
        output_filename = f"/tmp/{job_id}_output_{i}.mp4"
        output_filenames.append(output_filename)
        
        for option in output["options"]:
            command.append(option["option"])
            if "argument" in option and option["argument"] is not None:
                command.append(str(option["argument"]))
        command.append(output_filename)
    
    # Mock metadata
    metadata = []
    if data.get("metadata"):
        for output_filename in output_filenames:
            metadata_item = {}
            if data["metadata"].get("filesize"):
                metadata_item["filesize"] = 75599473
            if data["metadata"].get("duration"):
                metadata_item["duration"] = 1934.56
            metadata.append(metadata_item)
    
    # Return the command if requested
    if return_command:
        return output_filenames, metadata, command
    return output_filenames, metadata

# Queue for asynchronous processing
class TaskQueue:
    def __init__(self):
        self.queue = []
        self.queue_id = id(self)
        self.thread = threading.Thread(target=self.process_queue, daemon=True)
        self.thread.start()
    
    def put(self, task):
        self.queue.append(task)
    
    def get(self):
        if self.queue:
            return self.queue.pop(0)
        return None
    
    def qsize(self):
        return len(self.queue)
    
    def process_queue(self):
        while True:
            task = self.get()
            if task:
                job_id, data, webhook_url, queue_start_time = task
                queue_time = time.time() - queue_start_time
                run_start_time = time.time()
                
                try:
                    # Process FFmpeg compose
                    output_filenames, metadata, ffmpeg_command = process_ffmpeg_compose(data, job_id, return_command=True)
                    logger.info(f"Job {job_id}: Generated FFmpeg Command: {' '.join(ffmpeg_command)}")
                    
                    # Mock execution of FFmpeg command
                    logger.info(f"Job {job_id}: Executing FFmpeg command...")
                    
                    # Mock upload of output files
                    output_urls = []
                    for i, output_filename in enumerate(output_filenames):
                        upload_url = mock_upload_file(output_filename)
                        output_info = {"file_url": upload_url}
                        
                        if metadata and i < len(metadata):
                            output_metadata = metadata[i]
                            output_info.update(output_metadata)
                        
                        output_urls.append(output_info)
                    
                    run_time = time.time() - run_start_time
                    total_time = time.time() - queue_start_time
                    
                    # Prepare webhook data
                    response_data = {
                        "endpoint": "/v1/ffmpeg/compose",
                        "code": 200,
                        "id": data.get("id"),
                        "job_id": job_id,
                        "response": output_urls,
                        "message": "success",
                        "pid": os.getpid(),
                        "queue_id": self.queue_id,
                        "run_time": round(run_time, 3),
                        "queue_time": round(queue_time, 3),
                        "total_time": round(total_time, 3),
                        "queue_length": self.qsize(),
                        "build_number": 123
                    }
                    
                    # Send webhook
                    if webhook_url:
                        send_webhook(webhook_url, response_data)
                
                except Exception as e:
                    logger.error(f"Job {job_id}: Error processing FFmpeg request - {str(e)}")
                    
                    # Prepare error webhook data
                    response_data = {
                        "endpoint": "/v1/ffmpeg/compose",
                        "code": 500,
                        "id": data.get("id"),
                        "job_id": job_id,
                        "message": str(e),
                        "pid": os.getpid(),
                        "queue_id": self.queue_id,
                        "run_time": round(time.time() - run_start_time, 3),
                        "queue_time": round(queue_time, 3),
                        "total_time": round(time.time() - queue_start_time, 3),
                        "queue_length": self.qsize(),
                        "build_number": 123
                    }
                    
                    # Send webhook
                    if webhook_url:
                        send_webhook(webhook_url, response_data)
            
            # Sleep to avoid high CPU usage
            time.sleep(0.1)

# Create task queue
task_queue = TaskQueue()

@app.route('/v1/ffmpeg/compose', methods=['POST'])
def ffmpeg_compose():
    if not request.json:
        return jsonify({"message": "Missing JSON in request"}), 400
    
    data = request.json
    job_id = str(uuid.uuid4())
    
    # Check if webhook_url is provided
    webhook_url = data.get("webhook_url")
    if webhook_url:
        # Add to queue for asynchronous processing
        task_queue.put((job_id, data, webhook_url, time.time()))
        
        # Return 202 Accepted response
        return jsonify({
            "code": 202,
            "id": data.get("id"),
            "job_id": job_id,
            "message": "processing",
            "pid": os.getpid(),
            "queue_id": task_queue.queue_id,
            "max_queue_length": "unlimited",
            "queue_length": task_queue.qsize(),
            "build_number": 123
        }), 202
    else:
        # Process synchronously
        try:
            # Process FFmpeg compose
            output_filenames, metadata, ffmpeg_command = process_ffmpeg_compose(data, job_id, return_command=True)
            logger.info(f"Job {job_id}: Generated FFmpeg Command: {' '.join(ffmpeg_command)}")
            
            # Mock execution of FFmpeg command
            logger.info(f"Job {job_id}: Executing FFmpeg command...")
            
            # Mock upload of output files
            output_urls = []
            for i, output_filename in enumerate(output_filenames):
                upload_url = mock_upload_file(output_filename)
                output_info = {"file_url": upload_url}
                
                if metadata and i < len(metadata):
                    output_metadata = metadata[i]
                    output_info.update(output_metadata)
                
                output_urls.append(output_info)
            
            return jsonify({
                "code": 200,
                "id": data.get("id"),
                "job_id": job_id,
                "response": output_urls,
                "message": "success",
                "pid": os.getpid(),
                "queue_id": task_queue.queue_id,
                "queue_length": task_queue.qsize(),
                "build_number": 123
            }), 200
        
        except Exception as e:
            logger.error(f"Job {job_id}: Error processing FFmpeg request - {str(e)}")
            return jsonify({
                "code": 500,
                "id": data.get("id"),
                "job_id": job_id,
                "message": str(e),
                "pid": os.getpid(),
                "queue_id": task_queue.queue_id,
                "queue_length": task_queue.qsize(),
                "build_number": 123
            }), 500

if __name__ == '__main__':
    logger.info("Starting minimal test app for /v1/ffmpeg/compose endpoint")
    logger.info("This app mocks the FFmpeg processing and webhook functionality")
    logger.info("Server running at http://127.0.0.1:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)
