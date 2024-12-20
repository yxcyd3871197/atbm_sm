import os
import whisper
import srt
from datetime import timedelta
from whisper.utils import WriteSRT, WriteVTT
from services.file_management import download_file
import logging
import uuid

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Set the default local storage directory
STORAGE_PATH = "/tmp/"

def process_transcription(media_url, output_type, max_chars=56, language=None):
    """Transcribe media and return the transcript, SRT or ASS file path."""
    logger.info(f"Starting transcription for media URL: {media_url} with output type: {output_type}")
    input_filename = download_file(media_url, os.path.join(STORAGE_PATH, 'input_media'))
    logger.info(f"Downloaded media to local file: {input_filename}")

    try:
        model = whisper.load_model("base")
        logger.info("Loaded Whisper model")

        if output_type == 'transcript':
            result = model.transcribe(input_filename, language=language)
            output = result['text']
            logger.info("Generated transcript output")
        elif output_type in ['srt', 'vtt']:
            result = model.transcribe(input_filename)
            srt_subtitles = []
            for i, segment in enumerate(result['segments'], start=1):
                start = timedelta(seconds=segment['start'])
                end = timedelta(seconds=segment['end'])
                text = segment['text'].strip()
                srt_subtitles.append(srt.Subtitle(i, start, end, text))
            
            output_content = srt.compose(srt_subtitles)
            
            output_filename = os.path.join(STORAGE_PATH, f"{uuid.uuid4()}.{output_type}")
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(output_content)
            
            output = output_filename
            logger.info(f"Generated {output_type.upper()} output: {output}")
        elif output_type == 'ass':
            result = model.transcribe(
                input_filename,
                word_timestamps=True,
                task='transcribe',
                verbose=False
            )
            logger.info("Transcription completed with word-level timestamps")
            ass_content = generate_ass_subtitle(result, max_chars)
            logger.info("Generated ASS subtitle content")
            
            output_content = ass_content

            output_filename = os.path.join(STORAGE_PATH, f"{uuid.uuid4()}.{output_type}")
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(output_content) 
            output = output_filename
            logger.info(f"Generated {output_type.upper()} output: {output}")
        else:
            raise ValueError("Invalid output type. Must be 'transcript', 'srt', or 'vtt'.")

        os.remove(input_filename)
        logger.info(f"Removed local file: {input_filename}")
        logger.info(f"Transcription successful, output type: {output_type}")
        return output
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise
