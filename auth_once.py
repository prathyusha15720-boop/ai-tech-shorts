import json
from google_auth_oauthlib.flow import InstalledAppFlow

# YouTube Data API v3 Upload & Read Scope
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"]

def main():
    print("Starting OAuth flow for YouTube API...")
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json", SCOPES
    )
    creds = flow.run_local_server(port=0)

    # Save credentials to token.json
    with open("token.json", "w", encoding="utf-8") as token_file:
        token_file.write(creds.to_json())

    print("Success! token.json has been created in the root directory.")

if __name__ == "__main__":
    main()
    