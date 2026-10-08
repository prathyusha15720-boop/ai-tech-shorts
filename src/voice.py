import os
import logging
from gtts import gTTS

logger = logging.getLogger(__name__)

def generate_tts_narration(script_text, output_audio_path="output.mp3"):
    """
    Generates audio TTS narration using Google Text-to-Speech (gTTS).
    """
    if not script_text:
        logger.error("Script text is empty. Cannot generate TTS.")
        return None

    try:
        logger.info("Generating TTS narration using gTTS...")
        # Converting text to speech using gTTS
        tts = gTTS(text=script_text, lang='te', slow=False)
        tts.save(output_audio_path)

        logger.info(f"Audio file saved successfully to {output_audio_path}")
        return output_audio_path
    except Exception as e:
        logger.error(f"Failed to generate TTS audio: {e}")
        return None