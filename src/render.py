import os
import subprocess
import logging
import textwrap
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

def create_scene_image(scene, index, output_dir="temp_scenes"):
    """
    Creates a 1080x1920 portrait slide with a unique background image per scene and clear text overlay.
    """
    os.makedirs(output_dir, exist_ok=True)
    width, height = 1080, 1920

    # Fetching unique background image per scene based on content keyword/index
    img = None
    try:
        # Using unique seeds so each scene gets a distinct place/person/thing image
        img_url = f"https://picsum.photos/seed/{index + 100}/1080/1920"
        response = requests.get(img_url, timeout=5)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content)).convert("RGB")
    except Exception as e:
        logger.warning(f"Could not fetch dynamic background image for scene {index}: {e}")

    if not img:
        bg_color = scene.get("bg_color", "#111827")
        img = Image.new("RGB", (width, height), color=bg_color)
    else:
        img = img.resize((width, height), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(img)
    text_color = scene.get("text_color", "#FFFFFF")
    text_overlay = scene.get("text_overlay", "")

    # Load proper font with a larger size for clear visibility
    try:
        font = ImageFont.truetype("C:\\Windows\\Fonts\\Nirmala.ttf", size=65)
    except IOError:
        try:
            font = ImageFont.truetype("C:\\Windows\\Fonts\\Gautami.ttf", size=65)
        except IOError:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=65)
            except IOError:
                font = ImageFont.load_default()

    if text_overlay:
        # Wrap text nicely for portrait screen width
        wrapped_text = textwrap.fill(text_overlay, width=18)
        
        bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, align="center")
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (width - text_width) / 2
        y = (height - text_height) / 2

        # Draw a prominent dark box behind the text for high contrast and readability
        padding = 40
        box_coords = [
            x - padding,
            y - padding,
            x + text_width + padding,
            y + text_height + padding
        ]
        draw.rectangle(box_coords, fill=(15, 23, 42, 230))

        # Draw clear Telugu text over the box
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
    Renders a multi-scene 1080x1920 MP4 video with unique images per scene, normal speed, and sync.
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
    num_scenes = max(len(scenes), 1)
    duration_per_scene = audio_duration / num_scenes
    fps = 30
    frames_per_scene = int(duration_per_scene * fps)

    cmd = ["ffmpeg", "-y"]
    for img_path in scene_images:
        cmd.extend(["-loop", "1", "-t", f"{duration_per_scene:.2f}", "-i", img_path])
    
    cmd.extend(["-i", audio_path])

    filter_parts = []
    concat_inputs = []
    for i in range(num_scenes):
        filter_parts.append(
            f"[{i}:v]scale=1080:1920,zoompan=z='min(zoom+0.0015,1.15)':d={frames_per_scene}:s=1080x1920:fps={fps}[v{i}]"
        )
        concat_inputs.append(f"[v{i}]")

    concat_filter = "".join(concat_inputs) + f"concat=n={num_scenes}:v=1:a=0[outv]"
    filter_parts.append(concat_filter)

    filter_complex_str = ";".join(filter_parts)

    cmd.extend([
        "-filter_complex", filter_complex_str,
        "-map", "[outv]",
        "-map", f"{num_scenes}:a",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_filename
    ])

    try:
        logger.info(f"Running multi-scene rendering with visible text and correct timing...")
        subprocess.run(cmd, check=True)
        logger.info(f"Successfully rendered {output_filename}")
        return output_filename
    except Exception as e:
        logger.error(f"FFmpeg rendering failed: {e}")
        return None