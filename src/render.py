import os
import subprocess
import logging
import textwrap
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

def create_scene_image(scene, index, output_dir="temp_scenes"):
    """
    Creates a 1080x1920 portrait slide with wrapped text overlay.
    """
    os.makedirs(output_dir, exist_ok=True)
    width, height = 1080, 1920

    bg_color = scene.get("bg_color", "#111827")
    text_color = scene.get("text_color", "#FFFFFF")
    text_overlay = scene.get("text_overlay", "Tech News")

    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Font fallback for Windows and Linux (GitHub Actions Runner)
    try:
        font = ImageFont.truetype("arial.ttf", size=55)
    except IOError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=55)
        except IOError:
            font = ImageFont.load_default()

    # Wrap text nicely to fit portrait width
    wrapped_text = textwrap.fill(text_overlay, width=22)

    # Center multi-line text placement
    bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, align="center")
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (width - text_width) / 2
    y = (height - text_height) / 2

    draw.multiline_text((x, y), wrapped_text, fill=text_color, font=font, align="center")

    image_path = os.path.join(output_dir, f"scene_{index}.png")
    img.save(image_path)
    return image_path

def get_audio_duration(audio_path):
    """
    Get exact audio duration using ffprobe.
    """
    try:
        cmd = [
            "ffprobe", "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            audio_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        logger.warning(f"Could not get audio duration: {e}. Defaulting to 15 seconds.")
        return 15.0

def render_short_video(content_payload, audio_path, output_filename="output_short.mp4"):
    """
    Renders a multi-scene 1080x1920 MP4 video slideshow with smooth zoompan motion and audio.
    """
    scenes = content_payload.get("scenes", [])
    if not scenes:
        logger.error("No scenes found in payload.")
        return None

    output_dir = "temp_scenes"
    scene_images = []
    for idx, scene in enumerate(scenes):
        img_path = create_scene_image(scene, idx, output_dir=output_dir)
        scene_images.append(img_path)

    audio_duration = get_audio_duration(audio_path)
    duration_per_scene = audio_duration / max(len(scenes), 1)

    # Create FFmpeg concat input file for multi-scene slideshow
    concat_file = os.path.join(output_dir, "concat.txt")
    with open(concat_file, "w") as f:
        for img_path in scene_images:
            abs_img_path = os.path.abspath(img_path).replace("\\", "/")
            f.write(f"file '{abs_img_path}'\n")
            f.write(f"duration {duration_per_scene:.2f}\n")
        # Repeat last frame briefly to prevent cutoffs
        if scene_images:
            last_img_path = os.path.abspath(scene_images[-1]).replace("\\", "/")
            f.write(f"file '{last_img_path}'\n")

    # FFmpeg Command with zoompan (moving/cinematic effect) and audio merging
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-i", audio_path,
        "-vf", "zoompan=z='min(zoom+0.0015,1.15)':d=125:s=1080x1920,format=yuv420p",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_filename
    ]

    try:
        logger.info(f"Running FFmpeg multi-scene render: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        return output_filename
    except Exception as e:
        logger.error(f"FFmpeg rendering failed: {e}")
        return None