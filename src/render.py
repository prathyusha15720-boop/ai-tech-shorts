import os
import subprocess
import logging
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

def create_scene_image(scene, index, output_dir="temp_scenes"):
    """
    Creates a 1080x1920 portrait slide with text overlay.
    """
    os.makedirs(output_dir, exist_ok=True)
    width, height = 1080, 1920

    # Parse color or fallback
    bg_color = scene.get("bg_color", "#111827")
    text_color = scene.get("text_color", "#FFFFFF")
    text_overlay = scene.get("text_overlay", "Tech News")

    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Use default font or load TTF if available
    try:
        font = ImageFont.truetype("arial.ttf", size=60)
    except IOError:
        font = ImageFont.load_default()

    # Center text placement
    bbox = draw.textbbox((0, 0), text_overlay, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (width - text_width) / 2
    y = (height - text_height) / 2

    draw.text((x, y), text_overlay, fill=text_color, font=font)

    image_path = os.path.join(output_dir, f"scene_{index}.png")
    img.save(image_path)
    return image_path

def render_short_video(content_payload, audio_path, output_filename="output_short.mp4"):
    """
    Renders the final 1080x1920 MP4 video combining scene images and audio using FFmpeg.
    """
    scenes = content_payload.get("scenes", [])
    if not scenes:
        logger.error("No scenes found in payload.")
        return None

    scene_images = []
    for idx, scene in enumerate(scenes):
        img_path = create_scene_image(scene, idx)
        scene_images.append(img_path)

    first_image = scene_images[0]
    
    # Updated FFmpeg Command with proper framerate and vertical scaling filter
    # Updated FFmpeg Command with proper input framerate before -i
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate", "30",
        "-loop", "1",
        "-i", first_image,
        "-i", audio_path,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_filename
    ]

    try:
        logger.info(f"Running FFmpeg render: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        return output_filename
    except Exception as e:
        logger.error(f"FFmpeg rendering failed: {e}")
        return None