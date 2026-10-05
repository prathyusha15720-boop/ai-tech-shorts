import os
import logging
from google import genai

logger = logging.getLogger(__name__)

def generate_tts_narration(script_text, output_audio_path="output.mp3"):
    """
    Generates audio TTS narration using Google Gemini API.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    tts_model = os.environ.get("GEMINI_TTS_MODEL", "gemini-2.5-flash")
    voice_name = os.environ.get("TTS_VOICE", "Kore")

    if not api_key:
        logger.error("GEMINI_API_KEY is not set.")
        return None

    client = genai.Client(api_key=api_key)

    try:
        # Requesting audio generation from Gemini
        response = client.models.generate_content(
            model=tts_model,
            contents=f"Read this tech news script aloud naturally and clearly: {script_text}",
            config={"response_mime_type": "audio/mp3"}
        )

        with open(output_audio_path, "wb") as f:
            f.write(response.candidates[0].content.parts[0].inline_data.data)

        logger.info(f"Audio file saved to {output_audio_path}")
        return output_audio_path
    except Exception as e:
        logger.error(f"Failed to generate TTS audio: {e}")
        return None