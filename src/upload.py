import os
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

def upload_to_youtube(video_file_path, content_payload):
    """
    Uploads generated video file to YouTube Shorts via YouTube Data API v3.
    """
    token_file = "token.json"
    if not os.path.exists(token_file):
        logger.error("token.json not found. Run auth_once.py first.")
        return False

    privacy_status = os.environ.get("YOUTUBE_PRIVACY_STATUS", "private")

    try:
        creds = Credentials.from_authorized_user_file(token_file)
        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": content_payload.get("title", "AI Tech Short #Shorts"),
                "description": content_payload.get("description", "Daily Tech News Updates #Shorts"),
                "tags": content_payload.get("tags", ["tech", "shorts"]),
                "categoryId": "28"  # Science & Technology
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(video_file_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = request.execute()
        logger.info(f"Video uploaded successfully! Video ID: {response.get('id')}")
        return True
    except Exception as e:
        logger.error(f"YouTube upload failed: {e}")
        return False