import os
import logging
import subprocess
from flask import Blueprint, request, jsonify
from app_utils import *
from services.v1.ffmpeg.ffmpeg_compose import process_ffmpeg_compose
from services.authentication import authenticate
from services.cloud_storage import upload_file

v1_ffmpeg_compose_bp = Blueprint('v1_ffmpeg_compose', __name__)
logger = logging.getLogger(__name__)

@v1_ffmpeg_compose_bp.route('/v1/ffmpeg/compose', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "inputs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file_url": {"type": "string", "format": "uri"},
                    "options": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "option": {"type": "string"},
                                "argument": {"type": ["string", "number", "null"]}
                            },
                            "required": ["option"]
                        }
                    }
                },
                "required": ["file_url"]
            },
            "minItems": 1
        },
        "filters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "filter": {"type": "string"}
                },
                "required": ["filter"]
            }
        },
        "outputs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "options": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "option": {"type": "string"},
                                "argument": {"type": ["string", "number", "null"]}
                            },
                            "required": ["option"]
                        }
                    }
                },
                "required": ["options"]
            },
            "minItems": 1
        },
        "global_options": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "option": {"type": "string"},
                    "argument": {"type": ["string", "number", "null"]}
                },
                "required": ["option"]
            }
        },
        "metadata": {
            "type": "object",
            "properties": {
                "thumbnail": {"type": "boolean"},
                "filesize": {"type": "boolean"},
                "duration": {"type": "boolean"},
                "bitrate": {"type": "boolean"},
                "encoder": {"type": "boolean"}
            }
        },
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["inputs", "outputs"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def ffmpeg_api(job_id, data):
    logger.info(f"Job {job_id}: Received flexible FFmpeg request")

    try:
        # Process FFmpeg compose and log the generated command
        output_filenames, metadata, ffmpeg_command = process_ffmpeg_compose(data, job_id, return_command=True)
        
        logger.debug(f"Job {job_id}: Generated FFmpeg Command: {' '.join(ffmpeg_command)}")

        # Execute the FFmpeg command and log outputs
        try:
            result = subprocess.run(ffmpeg_command, capture_output=True, text=True)
            logger.debug(f"Job {job_id}: FFmpeg Output: {result.stdout}")
            logger.debug(f"Job {job_id}: FFmpeg Error: {result.stderr}")
        except Exception as ffmpeg_error:
            logger.error(f"Job {job_id}: Error executing FFmpeg command: {ffmpeg_error}")
            raise ffmpeg_error

        # Upload output files to GCP and create result array
        output_urls = []
        for i, output_filename in enumerate(output_filenames):
            if os.path.exists(output_filename):
                upload_url = upload_file(output_filename)
                output_info = {"file_url": upload_url}
                
                if metadata and i < len(metadata):
                    output_metadata = metadata[i]
                    if 'thumbnail' in output_metadata:
                        thumbnail_path = output_metadata['thumbnail']
                        if os.path.exists(thumbnail_path):
                            thumbnail_url = upload_file(thumbnail_path)
                            del output_metadata['thumbnail']
                            output_metadata['thumbnail_url'] = thumbnail_url
                            os.remove(thumbnail_path)  # Clean up local thumbnail file
                    output_info.update(output_metadata)
                
                output_urls.append(output_info)
                os.remove(output_filename)  # Clean up local output file after upload
            else:
                raise Exception(f"Expected output file {output_filename} not found")

        return output_urls, "/v1/ffmpeg/compose", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error processing FFmpeg request - {str(e)}")
        return str(e), "/v1/ffmpeg/compose", 500
