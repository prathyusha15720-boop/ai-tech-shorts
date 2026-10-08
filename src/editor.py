import os
import json
import logging
from google import genai

logger = logging.getLogger(__name__)

def generate_script_and_scenes(news_item):
    """
    Generates YouTube Shorts script and multiple dynamic scenes instructions using Gemini.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    if not api_key:
        logger.error("GEMINI_API_KEY is not set.")
        return None

    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are an expert YouTube Shorts content creator specializing in tech news for a Telugu audience.
    Based on the following tech news headline and context, generate a complete content payload for a 30-45 second short video.

    News Title: {news_item.get('title')}
    News Summary: {news_item.get('summary')}
    News Link: {news_item.get('link')}

    CRITICAL INSTRUCTIONS:
    1. The "script" and scene "text_overlay" MUST be written in natural, engaging spoken Telugu language.
    2. You MUST generate **MULTIPLE distinct scenes (at least 4 to 6 scenes)** inside the "scenes" array so the video changes backgrounds, places, persons, and things dynamically corresponding to the narration.
    3. Each scene must have a unique `image_keyword` representing different places, persons, or technical objects.

    Return ONLY a valid JSON object matching this exact structure:
    {{
        "title": "Catchy YouTube Shorts Title in Telugu/English with hashtags",
        "description": "Engaging video description",
        "tags": ["tech", "telugu", "ai", "news", "shorts"],
        "script": "Full spoken narration text strictly in Telugu. Make it fast-paced, direct, and engaging.",
        "scenes": [
            {{
                "scene_number": 1,
                "duration_seconds": 5,
                "text_overlay": "Short Punchy Telugu Text for Scene 1",
                "image_keyword": "futuristic AI data center server room"
            }},
            {{
                "scene_number": 2,
                "duration_seconds": 5,
                "text_overlay": "Telugu Text for Scene 2",
                "image_keyword": "software developer coding on laptop office"
            }},
            {{
                "scene_number": 3,
                "duration_seconds": 5,
                "text_overlay": "Telugu Text for Scene 3",
                "image_keyword": "modern smartphone futuristic hologram interface"
            }},
            {{
                "scene_number": 4,
                "duration_seconds": 5,
                "text_overlay": "Telugu Text for Scene 4",
                "image_keyword": "global cybersecurity digital network map"
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