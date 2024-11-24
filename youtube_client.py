import os
import pickle
from typing import Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class YouTubeClient:
    """Client for interacting with YouTube API"""

    def __init__(self, credentials_path: str, token_path: str, playlist_id: str):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.playlist_id = playlist_id
        self.youtube = None
        self.SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

    def authenticate(self) -> None:
        """Authenticate with YouTube API using OAuth2"""
        credentials = self._get_credentials()
        self.youtube = build("youtube", "v3", credentials=credentials)

    def _get_credentials(self) -> Credentials:
        """Get valid user credentials from storage or generate new ones"""
        credentials = None

        # Load existing credentials
        if os.path.exists(self.token_path):
            print("Loading credentials from file...")
            with open(self.token_path, "rb") as token:
                credentials = pickle.load(token)

        # Refresh expired credentials
        if credentials and credentials.expired and credentials.refresh_token:
            print("Refreshing expired credentials...")
            try:
                credentials.refresh(Request())
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                credentials = None

        # Generate new credentials if needed
        if not credentials or not credentials.valid:
            print("Generating new credentials...")
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
                print("Saving credentials to file...")
                with open(self.token_path, "wb") as token:
                    pickle.dump(credentials, token)

            except Exception as e:
                print(f"Error during authorization: {e}")
                raise

        return credentials

    def test_connection(self) -> bool:
        """Test if the YouTube API connection is working"""
        try:
            # type: ignore
            request = self.youtube.channels().list(part="snippet", mine=True)
            response = request.execute()
            channel_name = response["items"][0]["snippet"]["title"]
            print(f"Successfully connected to YouTube API! Channel: {channel_name}")
            return True
        except Exception as e:
            print(f"Failed to connect to YouTube API: {e}")
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
            request = self.youtube.playlistItems().list(
                part="contentDetails", playlistId=self.playlist_id, maxResults=50
            )

            while request:
                response = request.execute()
                video_ids.extend(
                    item["contentDetails"]["videoId"]
                    for item in response.get("items", [])
                )

                # Get next page of results
                # type: ignore
                request = self.youtube.playlistItems().list_next(request, response)

            return video_ids

        except Exception as e:
            print(f"Error getting playlist items: {e}")
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
                print(f"Video already exists in playlist: {video_url}")
                return None

            request = self.youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": self.playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id},
                    }
                },
            )
            response = request.execute()
            print(f"Successfully added video to playlist: {video_url}")
            return response

        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred: {e.content}")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")
            raise
