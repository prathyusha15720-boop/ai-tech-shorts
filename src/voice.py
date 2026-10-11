import os
import subprocess
import logging
from gtts import gTTS

logger = logging.getLogger(__name__)

def generate_tts_narration(text, output_filename="output.mp3", speed_factor=1.50):
    """
    Generates TTS audio in Telugu and speeds it up using FFmpeg to 1.50x for punchy shorts.
    """
    temp_raw_audio = "temp_raw_narration.mp3"
    
    try:
        # Generate standard audio using gTTS
        tts = gTTS(text=text, lang='te', slow=False)
        tts.save(temp_raw_audio)

        # Speed up the generated audio using FFmpeg atempo filter
        cmd = [
            "ffmpeg", "-y",
            "-i", temp_raw_audio,
            "-filter:a", f"atempo={speed_factor}",
            "-vn",
            output_filename
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Clean up temporary raw audio file
        if os.path.exists(temp_raw_audio):
            os.remove(temp_raw_audio)
            
        logger.info(f"Audio file saved successfully with {speed_factor}x speed to {output_filename}")
        return output_filename

    except Exception as e:
        logger.error(f"Error generating voiceover: {e}")
        # Fallback to normal saved audio if ffmpeg fails
        if os.path.exists(temp_raw_audio):
            os.rename(temp_raw_audio, output_filename)
            return output_filename
        return None