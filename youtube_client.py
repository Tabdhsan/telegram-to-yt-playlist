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

    def __init__(self, credentials_path: str, token_path: str, playlist_id: str):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.playlist_id = playlist_id
        self.youtube: Optional[Resource] = None
        self.SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
        self.error_log = []

    def authenticate(self) -> None:
        """Authenticate with YouTube API using OAuth2"""
        credentials = self._get_credentials()
        self.youtube = cast(Resource, build("youtube", "v3", credentials=credentials))

    def _get_credentials(self) -> Credentials:
        """Get valid user credentials from storage or generate new ones"""
        credentials = None
        error_messages = []

        # Load existing credentials
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, "rb") as token:
                    credentials = pickle.load(token)
            except (pickle.UnpicklingError, EOFError) as e:
                error_messages.append(f"Error loading credentials: {e}")
                credentials = None

        # Refresh expired credentials
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
            except Exception as e:
                error_messages.append(f"Error refreshing credentials: {e}")
                credentials = None

        # Generate new credentials if needed
        if not credentials or not credentials.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, self.SCOPES
            )
            try:
                credentials = flow.run_local_server(
                    port=8080,
                    prompt="consent",
                    success_message=(
                        "The auth flow completed! You may close this window."
                    ),
                    open_browser=True,
                )

                # Save the credentials for future use
                with open(self.token_path, "wb") as token:
                    pickle.dump(credentials, token)

            except Exception as e:
                error_messages.append(f"Error during authorization: {e}")
                raise

        if error_messages:
            self.error_log = error_messages

        return credentials

    def test_connection(self) -> bool:
        """Test if the YouTube API connection is working"""
        try:
            request = self.youtube.channels().list(  # type: ignore[attr-defined]
                part="snippet", mine=True
            )
            response = request.execute()
            channel_name = response["items"][0]["snippet"]["title"]
            return True
        except Exception as e:
            self.error_log.append(f"Failed to connect to YouTube API: {e}")
            return False

    def extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL"""
        if "youtu.be" in url:
            return url.split("/")[-1]
        return url.split("v=")[1].split("&")[0]

    def _get_playlist_items(self) -> list[str]:
        """Get all video IDs currently in the playlist"""
        try:
            video_ids = []
            request = self.youtube.playlistItems().list(  # type: ignore[attr-defined]
                part="contentDetails", playlistId=self.playlist_id, maxResults=50
            )

            while request:
                response = request.execute()
                video_ids.extend(
                    item["contentDetails"]["videoId"]
                    for item in response.get("items", [])
                )

                # Get next page of results
                request = self.youtube.playlistItems().list_next(  # type: ignore[attr-defined]
                    request, response
                )

            return video_ids

        except Exception as e:
            self.error_log.append(f"Error getting playlist items: {e}")
            return []

    def is_video_in_playlist(self, video_id: str) -> bool:
        """Check if a video is already in the playlist"""
        return video_id in self._get_playlist_items()

    def add_to_playlist(self, video_url: str) -> Optional[dict[str, Any]]:
        """Add a video to the specified playlist if it's not already there"""
        try:
            video_id = self.extract_video_id(video_url)

            # Check if video is already in playlist
            if self.is_video_in_playlist(video_id):
                self.error_log.append(f"Video already exists in playlist: {video_url}")
                return None

            request = self.youtube.playlistItems().insert(  # type: ignore[attr-defined]
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": self.playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id},
                    }
                },
            )
            response = request.execute()
            return response

        except HttpError as e:
            self.error_log.append(
                f"An HTTP error {e.resp.status} occurred: {e.content}"
            )
            raise
        except Exception as e:
            self.error_log.append(f"An error occurred: {e}")
            raise
