import os
import pickle
from typing import Any, Optional, cast

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError


class YouTubeClient:
    """Client for interacting with YouTube API"""

    SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

    def __init__(self, credentials_path: str, token_path: str, playlist_id: str):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.playlist_id = playlist_id
        self.youtube: Optional[Resource] = None
        self.error_log = []

    def authenticate(self) -> None:
        """Authenticate with YouTube API using OAuth2"""
        credentials = self._load_or_refresh_credentials()
        self.youtube = cast(Resource, build("youtube", "v3", credentials=credentials))

    def _load_or_refresh_credentials(self) -> Credentials:
        """Load credentials from file, refresh if expired, or run full OAuth flow"""
        credentials = self._load_credentials_from_file()

        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
            except Exception as e:
                self.error_log.append(f"Error refreshing credentials: {e}")
                credentials = None

        if not credentials or not credentials.valid:
            credentials = self._run_auth_flow()

        return credentials

    def _load_credentials_from_file(self) -> Optional[Credentials]:
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, "rb") as token:
                    return pickle.load(token)
            except (pickle.UnpicklingError, EOFError) as e:
                self.error_log.append(f"Error loading credentials: {e}")
        return None

    def _run_auth_flow(self) -> Credentials:
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, self.SCOPES
            )
            credentials = flow.run_local_server(
                port=8080,
                prompt="consent",
                success_message="Auth complete, you can close this window.",
                open_browser=True,
            )
            with open(self.token_path, "wb") as token:
                pickle.dump(credentials, token)
            return credentials
        except Exception as e:
            self.error_log.append(f"Authorization error: {e}")
            raise

    def test_connection(self) -> bool:
        """Check API connectivity"""
        try:
            self.youtube.channels().list(part="snippet", mine=True).execute()  # type: ignore[attr-defined]
            return True
        except Exception as e:
            self.error_log.append(f"Failed to connect to YouTube API: {e}")
            return False

    def extract_video_id(self, url: str) -> str:
        """Extract the video ID from a YouTube URL"""
        if "youtu.be" in url:
            return url.split("/")[-1]
        return url.split("v=")[1].split("&")[0]

    def _get_playlist_items(self) -> list[str]:
        """Retrieve all video IDs currently in the playlist"""
        video_ids = []
        try:
            request = self.youtube.playlistItems().list(  # type: ignore[attr-defined]
                part="contentDetails", playlistId=self.playlist_id, maxResults=50
            )
            while request:
                response = request.execute()
                video_ids.extend(
                    item["contentDetails"]["videoId"]
                    for item in response.get("items", [])
                )
                request = self.youtube.playlistItems().list_next(request, response)  # type: ignore[attr-defined]
        except Exception as e:
            self.error_log.append(f"Error fetching playlist items: {e}")
        return video_ids

    def is_video_in_playlist(self, video_id: str) -> bool:
        """Check if a video is already in the playlist"""
        return video_id in self._get_playlist_items()

    def add_to_playlist(self, video_url: str) -> Optional[dict[str, Any]]:
        """Add a video to the playlist if not already present"""
        try:
            video_id = self.extract_video_id(video_url)
            if self.is_video_in_playlist(video_id):
                return None  # Already present

            request = self.youtube.playlistItems().insert(  # type: ignore[attr-defined]
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": self.playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id},
                    }
                },
            )
            return request.execute()

        except HttpError as e:
            self.error_log.append(f"HTTP error {e.resp.status}: {e.content}")
            raise
        except Exception as e:
            self.error_log.append(f"General error adding to playlist: {e}")
            raise


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()

    credentials_path = os.environ["YOUTUBE_CREDENTIALS_PATH"]
    token_path = os.environ["YOUTUBE_TOKEN_PATH"]
    playlist_id = os.environ["YOUTUBE_PLAYLIST_ID"]
    test_video_url = "https://youtu.be/dQw4w9WgXcQ" # Example

    client = YouTubeClient(credentials_path, token_path, playlist_id)
    client.authenticate()

    print("✅ Authenticated with YouTube")

    print("🔍 Testing connection...")
    if client.test_connection():
        print("✅ Connection successful!")
    else:
        print("❌ Connection failed.")
        print(client.error_log)

    print(f"➕ Attempting to add video: {test_video_url}")
    result = client.add_to_playlist(test_video_url)

    if result:
        print("✅ Video added to playlist.")
    else:
        print("ℹ️ Video was already in playlist or skipped.")
