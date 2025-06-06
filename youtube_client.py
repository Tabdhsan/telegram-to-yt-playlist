import os
import pickle
import asyncio
from typing import Any, Optional, cast
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError


class YouTubeClient:
    """Client for interacting with YouTube API"""

    SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

    def __init__(self, credentials_path: str, token_path: str, playlist_id: str, telegram_client=None, owner_chat_id: int = None):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.playlist_id = playlist_id
        self.youtube: Optional[Resource] = None
        self.error_log = []
        self.telegram_client = telegram_client
        self.owner_chat_id = owner_chat_id
        self._auth_code_future = None

    def authenticate(self) -> None:
        """Authenticate with YouTube API using OAuth2"""
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # We're in an async context, but we need to handle this carefully
            # Create a new task for the async authentication
            task = loop.create_task(self._authenticate_async())
            # This is a bit of a hack, but we need to wait for it
            # In practice, this should be called from an async context
            credentials = loop.run_until_complete(task)
        except RuntimeError:
            # No running event loop, we can use asyncio.run
            credentials = asyncio.run(self._authenticate_async())
        
        self.youtube = cast(Resource, build("youtube", "v3", credentials=credentials))

    async def authenticate_async(self) -> None:
        """Async version of authenticate"""
        credentials = await self._authenticate_async()
        self.youtube = cast(Resource, build("youtube", "v3", credentials=credentials))

    async def _authenticate_async(self) -> Credentials:
        """Internal async authentication method"""
        credentials = await self._load_or_refresh_credentials_async()
        return credentials

    def _load_credentials_from_file(self) -> Optional[Credentials]:
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, "rb") as token:
                    loaded_creds = pickle.load(token)
                    
                    # Check if it's the correct type (Google Credentials)
                    if isinstance(loaded_creds, Credentials):
                        return loaded_creds
                    else:
                        # Old format or wrong type, delete and start fresh
                        print("🔄 Found old credential format, will re-authenticate...")
                        os.remove(self.token_path)
                        return None
                        
            except (pickle.UnpicklingError, EOFError) as e:
                self.error_log.append(f"Error loading credentials: {e}")
                # Delete corrupted file
                try:
                    os.remove(self.token_path)
                except:
                    pass
        return None

    async def _load_or_refresh_credentials_async(self) -> Credentials:
        """Load credentials from file, refresh if expired, or run full OAuth flow"""
        credentials = self._load_credentials_from_file()

        if credentials and hasattr(credentials, 'expired') and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
            except Exception as e:
                self.error_log.append(f"Error refreshing credentials: {e}")
                credentials = None

        if not credentials or not (hasattr(credentials, 'valid') and credentials.valid):
            credentials = await self._run_auth_flow_async()

        return credentials

    async def _run_auth_flow_async(self) -> Credentials:
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, self.SCOPES
            )
            
            # Set redirect URI for out-of-band flow
            flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
            
            # Check if we have an auth code provided via environment variable (fallback)
            auth_code = os.environ.get("YOUTUBE_AUTH_CODE")
            
            if auth_code:
                # Use the provided auth code directly
                print("🔑 Using provided authorization code from environment...")
                flow.fetch_token(code=auth_code.strip())
                credentials = flow.credentials
            elif self.telegram_client and self.owner_chat_id:
                # Use Telegram-based authentication
                print("🔑 Using Telegram-based authentication...")
                auth_code = await self._get_auth_code_via_telegram(flow)
                flow.fetch_token(code=auth_code.strip())
                credentials = flow.credentials
            else:
                # Fallback to console output
                auth_url, _ = flow.authorization_url(prompt='consent')
                print("\n" + "="*60)
                print("🔐 YOUTUBE AUTHENTICATION REQUIRED")
                print("="*60)
                print("1. Open this URL in your browser:")
                print(f"   {auth_url}")
                print("\n2. Complete the authorization process")
                print("3. Copy the authorization code from the final page")
                print("4. Set the authorization code as environment variable:")
                print("   YOUTUBE_AUTH_CODE=<your_code_here>")
                print("5. Restart the container")
                print("="*60)
                
                # Log the error and raise exception to stop execution
                error_msg = "Authorization required. Please set YOUTUBE_AUTH_CODE environment variable."
                self.error_log.append(error_msg)
                raise Exception(error_msg)
            
            # Save credentials for future use
            with open(self.token_path, "wb") as token:
                pickle.dump(credentials, token)
            return credentials
            
        except Exception as e:
            self.error_log.append(f"Authorization error: {e}")
            raise

    async def _get_auth_code_via_telegram(self, flow) -> str:
        """Get authorization code via Telegram"""
        try:
            # Generate authorization URL
            auth_url, _ = flow.authorization_url(prompt='consent')
            
            # Send auth URL to owner via Telegram
            message = (
                "🔐 **YouTube Authentication Required**\n\n"
                "Please complete the following steps:\n\n"
                "1️⃣ Click this link to authorize:\n"
                f"{auth_url}\n\n"
                "2️⃣ Complete the authorization process\n\n"
                "3️⃣ Copy the authorization code from the final page\n\n"
                "4️⃣ Reply to this message with just the authorization code"
            )
            
            await self.telegram_client.send_message(self.owner_chat_id, message)
            print("📱 Auth URL sent to Telegram. Waiting for authorization code...")
            
            # Set up future to wait for auth code
            self._auth_code_future = asyncio.Future()
            
            # Set up temporary event handler for auth codes
            from telethon import events
            
            async def temp_auth_handler(event):
                """Temporary handler for auth code messages"""
                try:
                    message = event.message
                    text = message.text or ""
                    
                    # Check if this looks like an authorization code
                    if (text.startswith('4/') or (len(text) > 20 and text.replace('-', '').replace('_', '').isalnum())):
                        print(f"🔑 Received auth code: {text[:10]}...")
                        
                        # Set the result
                        if not self._auth_code_future.done():
                            self._auth_code_future.set_result(text)
                        
                        # Delete the auth code message for security
                        try:
                            await message.delete()
                            print("🗑️ Auth code message deleted for security")
                        except Exception as e:
                            print(f"⚠️ Could not delete auth code message: {e}")
                            
                except Exception as e:
                    print(f"❌ Error in temp auth handler: {e}")
            
            # Add the temporary event handler
            self.telegram_client.add_event_handler(
                temp_auth_handler, 
                events.NewMessage(chats=self.owner_chat_id)
            )
            
            try:
                # Wait for auth code (with timeout)
                auth_code = await asyncio.wait_for(self._auth_code_future, timeout=300)  # 5 minute timeout
                await self.telegram_client.send_message(self.owner_chat_id, "✅ Authorization code received! Completing authentication...")
                return auth_code
            except asyncio.TimeoutError:
                await self.telegram_client.send_message(self.owner_chat_id, "❌ Authentication timed out. Please restart the bot and try again.")
                raise Exception("Authentication timeout")
            finally:
                # Remove the temporary event handler
                self.telegram_client.remove_event_handler(temp_auth_handler)
                
        except Exception as e:
            if self.telegram_client and self.owner_chat_id:
                await self.telegram_client.send_message(self.owner_chat_id, f"❌ Authentication error: {e}")
            raise

    def handle_auth_code(self, auth_code: str):
        """Handle received authorization code from Telegram"""
        if self._auth_code_future and not self._auth_code_future.done():
            self._auth_code_future.set_result(auth_code)

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
        # Handle youtu.be short URLs
        if "youtu.be" in url:
            # Extract ID from path, ignore query parameters
            match = re.search(r'youtu\.be/([a-zA-Z0-9_-]+)', url)
            if match:
                return match.group(1)
        
        # Handle all youtube.com formats (www, m, or no subdomain)
        # Look for v= parameter in any position
        match = re.search(r'[?&]v=([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)
        
        # Fallback: try to extract from embed or /v/ URLs
        match = re.search(r'(?:embed/|/v/)([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)
        
        # If all else fails, raise an error
        raise ValueError(f"Could not extract video ID from URL: {url}")

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
