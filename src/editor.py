import os
import json
import logging
from google import genai

logger = logging.getLogger(__name__)

def generate_script_and_scenes(news_item):
    """
    Generates YouTube Shorts script and scene instructions using Gemini.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    if not api_key:
        logger.error("GEMINI_API_KEY is not set.")
        return None

    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are an expert YouTube Shorts content creator specializing in tech news.
    Based on the following tech news headline and context, generate a complete content payload for a 30-45 second short video.

    News Title: {news_item.get('title')}
    News Summary: {news_item.get('summary')}
    News Link: {news_item.get('link')}

    Return ONLY a valid JSON object matching this structure:
    {{
        "title": "Catchy YouTube Shorts Title (with hashtags)",
        "description": "Engaging video description with credits and links",
        "tags": ["tech", "ai", "news", "shorts"],
        "script": "Full spoken narration text for TTS. Make it fast-paced, direct, and engaging.",
        "scenes": [
            {{
                "scene_number": 1,
                "duration_seconds": 5,
                "text_overlay": "Short Punchy On-Screen Text",
                "bg_color": "#1A1A1A",
                "text_color": "#FFFFFF"
            }}
        ]
    }}
    """

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        content_payload = json.loads(response.text)
        return content_payload
    except Exception as e:
        logger.error(f"Error generating script from Gemini: {e}")
        return None