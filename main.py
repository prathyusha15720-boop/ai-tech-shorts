import os
import sys
import logging
from src.research import fetch_latest_tech_news
from src.editor import generate_script_and_scenes
from src.sheet import log_content_data
from src.voice import generate_tts_narration
from src.render import render_short_video
from src.upload import upload_to_youtube

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_pipeline():
    logging.info("Starting AI Tech Shorts Pipeline...")

    # 1. Tech News Research
    logging.info("Fetching latest tech news...")
    news_item = fetch_latest_tech_news()
    if not news_item:
        logging.error("Failed to fetch news. Exiting pipeline.")
        sys.exit(1)

    # 2. Gemini Script & Scene Generation
    logging.info("Generating script and scene design using Gemini...")
    content_payload = generate_script_and_scenes(news_item)
    if not content_payload:
        logging.error("Failed to generate content payload. Exiting.")
        sys.exit(1)

    # 3. Log to Excel Matrix (content_log.xlsx)
    logging.info("Logging entry into Excel matrix...")
    log_content_data(content_payload)

    # 4. Generate TTS Audio
    logging.info("Generating TTS narration audio...")
    audio_path = generate_tts_narration(content_payload["script"])

    # 5. Render Video (1080x1920 9:16)
    logging.info("Rendering short video using FFmpeg/Pillow...")
    output_video_path = render_short_video(content_payload, audio_path)

    # 6. Upload to YouTube Shorts
    logging.info("Uploading video to YouTube Shorts...")
    upload_status = upload_to_youtube(output_video_path, content_payload)
    
    if upload_status:
        logging.info("Pipeline completed successfully!")
    else:
        logging.error("Upload failed.")

if __name__ == "__main__":
    run_pipeline()