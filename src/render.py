import os
import subprocess
import logging
import textwrap
import requests
import io
from PIL import Image, ImageOps, ImageDraw
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

logger = logging.getLogger(__name__)

# Configure matplotlib to support Telugu fonts natively on Windows
font_paths = [
    r"C:\Windows\Fonts\Nirmala.ttf",
    r"C:\Windows\Fonts\NirmalaB.ttf",
    r"C:\Windows\Fonts\Gautami.ttf"
]
for f_path in font_paths:
    if os.path.exists(f_path):
        fm.fontManager.addfont(f_path)
        prop = fm.FontProperties(fname=f_path)
        plt.rcParams['font.sans-serif'] = prop.get_name()
        break

plt.rcParams['axes.unicode_minus'] = False

def create_scene_image(scene, index, output_dir="temp_scenes"):
    """
    Creates a 1080x1920 portrait slide with unique background and robust Telugu text rendering via Matplotlib.
    """
    os.makedirs(output_dir, exist_ok=True)
    width, height = 1080, 1920

    # Guaranteed unique background image per scene
    img = None
    try:
        keyword = scene.get('image_keyword', 'tech')
        unique_seed = (index + 1) * 137 + sum(ord(c) for c in keyword)
        img_url = f"https://picsum.photos/seed/{unique_seed}/1080/1920"
        
        response = requests.get(img_url, timeout=5)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content)).convert("RGB")
    except Exception as e:
        logger.warning(f"Could not fetch dynamic background image for scene {index}: {e}")

    if not img:
        bg_color = scene.get("bg_color", "#111827")
        img = Image.new("RGB", (width, height), color=bg_color)
    else:
        img = ImageOps.fit(img, (width, height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))

    text_overlay = scene.get("text_overlay", "")

    if text_overlay:
        # Wrap text nicely for portrait width
        wrapped_text = textwrap.fill(text_overlay, width=20)

        # Use Matplotlib to render Telugu & English mixed text perfectly
        fig, ax = plt.subplots(figsize=(10, 10), dpi=100)
        ax.axis('off')
        fig.patch.set_facecolor('none')
        ax.set_facecolor('none')

        # Add text with a stylish rounded background box using the loaded font
        ax.text(
            0.5, 0.5, wrapped_text,
            fontsize=26,
            color='white',
            ha='center',
            va='center',
            weight='bold',
            wrap=True,
            fontproperties=prop if 'prop' in locals() else None,
            bbox=dict(
                boxstyle='round,pad=1.2',
                facecolor='#0f172a',
                alpha=0.92,
                edgecolor='#334155',
                linewidth=2
            )
        )

        # Save matplotlib figure to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, transparent=True)
        buf.seek(0)
        text_img = Image.open(buf).convert("RGBA")
        plt.close(fig)

        # Resize text overlay image to fit nicely
        text_img.thumbnail((950, 1200))
        
        # Paste the text image onto the center of the background image
        paste_x = (width - text_img.width) // 2
        paste_y = (height - text_img.height) // 2
        img.paste(text_img, (paste_x, paste_y), text_img)

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
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps={fps},zoompan=z='min(zoom+0.001,1.05)':d={frames_per_scene}:s=1080x1920:fps={fps}[v{i}]"
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
        logger.info(f"Running multi-scene rendering with correct aspect ratio and timing...")
        subprocess.run(cmd, check=True)
        logger.info(f"Successfully rendered {output_filename}")
        return output_filename
    except Exception as e:
        logger.error(f"FFmpeg rendering failed: {e}")
        return None