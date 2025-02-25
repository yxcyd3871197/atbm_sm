import os
import sys
import json
import subprocess

# Add the current directory to the Python path
sys.path.append('.')

# Import the process_ffmpeg_compose function
from services.v1.ffmpeg.ffmpeg_compose import process_ffmpeg_compose

def test_process_ffmpeg_compose():
    # Mock subprocess.run to avoid actually running FFmpeg
    original_subprocess_run = subprocess.run
    
    def mock_subprocess_run(*args, **kwargs):
        class MockCompletedProcess:
            def __init__(self):
                self.returncode = 0
                self.stdout = ""
                self.stderr = ""
        return MockCompletedProcess()
    
    subprocess.run = mock_subprocess_run
    # Test data
    data = {
        "inputs": [
            {
                "file_url": "https://storage.googleapis.com/podcast-bucket-gunda/image_for_render/Youtube-video-BG.png",
                "options": [
                    { "option": "-loop", "argument": "1" },
                    { "option": "-t", "argument": "90" }
                ]
            },
            {
                "file_url": "https://storage.googleapis.com/podcast-bucket-gunda/intro-outro/Intro_Podcast.mp3"
            }
        ],
        "filters": [
            {
                "filter": "[0:v][1:a]concat=n=1:v=1:a=1[out]"
            }
        ],
        "outputs": [
            {
                "options": [
                    { "option": "-map", "argument": "[out]" },
                    { "option": "-c:v", "argument": "libx264" },
                    { "option": "-pix_fmt", "argument": "yuv420p" },
                    { "option": "-c:a", "argument": "aac" },
                    { "option": "-b:a", "argument": "192k" }
                ]
            }
        ]
    }
    
    # Test job_id
    job_id = "test-job-id"
    
    # Mock the download_file function to avoid actually downloading files
    import services.file_management
    original_download_file = services.file_management.download_file
    
    def mock_download_file(url, path):
        return os.path.join(path, os.path.basename(url))
    
    services.file_management.download_file = mock_download_file
    
    try:
        # Test with return_command=False (default)
        print("Testing process_ffmpeg_compose with return_command=False")
        output_filenames, metadata = process_ffmpeg_compose(data, job_id)
        print(f"Output filenames: {output_filenames}")
        print(f"Metadata: {metadata}")
        
        # Test with return_command=True
        print("\nTesting process_ffmpeg_compose with return_command=True")
        output_filenames, metadata, command = process_ffmpeg_compose(data, job_id, return_command=True)
        print(f"Output filenames: {output_filenames}")
        print(f"Metadata: {metadata}")
        print(f"Command: {' '.join(command)}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Restore the original functions
        services.file_management.download_file = original_download_file
        subprocess.run = original_subprocess_run

if __name__ == "__main__":
    test_process_ffmpeg_compose()
