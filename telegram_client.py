from telethon import TelegramClient, events
from telethon.sessions import StringSession
import asyncio
import re
from youtube_client import YouTubeClient


class TelegramToYouTubeBot:
    """
    Complete Telegram to YouTube bot.
    Listens to a Telegram chat and automatically adds YouTube links to a playlist.
    """

    def __init__(self, api_id: int, api_hash: str, session_string: str, chat_id: int, youtube_client: YouTubeClient, owner_chat_id: int = None):
        # Telegram setup
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_string = session_string
        self.chat_id = chat_id
        self.owner_chat_id = owner_chat_id or chat_id  # Default to main chat if not specified
        self.client = TelegramClient(StringSession(session_string), api_id, api_hash)
        
        # YouTube integration
        self.youtube_client = youtube_client
        
        # Error logging
        self.error_log = []

    async def setup_handlers(self):
        """Set up event handlers for the bot"""
        # Add event handler for new messages in the monitored chat
        self.client.add_event_handler(self.handle_new_message, events.NewMessage(chats=self.chat_id))
        
        # Add event handler for owner messages (for auth codes)
        if self.owner_chat_id != self.chat_id:
            self.client.add_event_handler(self.handle_owner_message, events.NewMessage(chats=self.owner_chat_id))
        else:
            # If owner and monitored chat are the same, use a single handler
            self.client.add_event_handler(self.handle_combined_message, events.NewMessage(chats=self.chat_id))
            # Remove the previous handler to avoid duplication
            self.client.remove_event_handler(self.handle_new_message)

        print(f"🎧 Listening for YouTube links in chat: {self.chat_id}")
        if self.owner_chat_id != self.chat_id:
            print(f"🔐 Listening for auth codes from owner: {self.owner_chat_id}")

    async def start(self):
        """Start the bot - authenticate and listen for messages"""
        try:
            # Start Telegram client
            await self.client.start()
            print("✅ Telegram client started")

            # Set up event handlers
            await self.setup_handlers()

            # Keep the client running until explicitly stopped
            await self.client.run_until_disconnected()

        except Exception as e:
            self.error_log.append(f"Failed to start Telegram client: {e}")
            raise

    async def handle_combined_message(self, event: events.NewMessage.Event):
        """Handle messages when owner and monitored chat are the same"""
        # First check if it's an auth code
        if await self.handle_auth_code_message(event):
            return
        
        # Otherwise handle as regular YouTube link message
        await self.handle_new_message(event)

    async def handle_owner_message(self, event: events.NewMessage.Event):
        """Handle messages from owner (for auth codes)"""
        await self.handle_auth_code_message(event)

    async def handle_auth_code_message(self, event: events.NewMessage.Event) -> bool:
        """Handle potential authorization code messages"""
        try:
            message = event.message
            text = message.text or ""
            
            # Check if this looks like an authorization code (alphanumeric, reasonable length)
            # YouTube auth codes are typically 4/... format or long alphanumeric strings
            if (text.startswith('4/') or (len(text) > 20 and text.replace('-', '').replace('_', '').isalnum())):
                print(f"🔑 Received potential auth code: {text[:10]}...")
                self.youtube_client.handle_auth_code(text)
                
                # Delete the auth code message for security
                try:
                    await message.delete()
                    print("🗑️ Auth code message deleted for security")
                except Exception as e:
                    print(f"⚠️ Could not delete auth code message: {e}")
                
                return True
            
            return False
            
        except Exception as e:
            error_msg = f"Error handling auth code message: {e}"
            self.error_log.append(error_msg)
            print(f"❌ {error_msg}")
            return False

    async def handle_new_message(self, event: events.NewMessage.Event):
        """Handle new incoming messages - process YouTube links"""
        try:
            message = event.message
            text = message.text or ""
            
            # Extract YouTube URLs from the message
            youtube_urls = self.extract_youtube_urls(text)
            
            if youtube_urls:
                sender = await message.get_sender()
                username = sender.username if sender and sender.username else "Unknown"
                
                print(f"📨 New message from @{username} with {len(youtube_urls)} YouTube link(s)")
                
                # Process each YouTube URL and track success
                successful_urls = 0
                failed_urls = 0
                
                for url in youtube_urls:
                    success = await self.process_youtube_url(url, username)
                    if success:
                        successful_urls += 1
                    else:
                        failed_urls += 1
                
                # Only delete the message if ALL URLs were processed successfully
                if failed_urls == 0:
                    try:
                        await message.delete()
                        print("🗑️ Message deleted - all URLs processed successfully")
                    except Exception as e:
                        print(f"⚠️ Could not delete message: {e}")
                else:
                    print(f"⚠️ Keeping message - {failed_urls} URL(s) failed, {successful_urls} succeeded")
                    print("   └─ User can retry the failed URLs later")

        except Exception as e:
            error_msg = f"Error handling message: {e}"
            self.error_log.append(error_msg)
            print(f"❌ {error_msg}")

    def extract_youtube_urls(self, text: str) -> list[str]:
        """Extract all YouTube URLs from text using regex"""
        patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+(?:&[\w=&]*)?',
            r'https?://youtu\.be/[\w-]+(?:\?[\w=&]*)?',
            r'https?://(?:www\.)?youtube\.com/embed/[\w-]+(?:\?[\w=&]*)?',
            r'https?://(?:www\.)?youtube\.com/v/[\w-]+(?:\?[\w=&]*)?',
            r'https?://(?:www\.)?youtube\.com/shorts/[\w-]+(?:\?[\w=&]*)?'
        ]
        
        urls = []
        for pattern in patterns:
            urls.extend(re.findall(pattern, text, re.IGNORECASE))
        
        return list(set(urls))  # Remove duplicates

    async def process_youtube_url(self, url: str, username: str) -> bool:
        """Process a single YouTube URL - add to playlist. Returns True if successful."""
        try:
            print(f"🎵 Processing: {url}")
            
            # Add to YouTube playlist (run in executor since it's synchronous)
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.youtube_client.add_to_playlist, url
            )
            
            if result:
                print(f"✅ Added to playlist: {url}")
                print(f"   └─ Requested by: @{username}")
                return True
            else:
                print(f"ℹ️ Video already in playlist: {url}")
                print(f"   └─ Requested by: @{username}")
                return True  # Already in playlist counts as success
                
        except Exception as e:
            print(f"❌ Failed to add {url} to playlist: {e}")
            print(f"   └─ Requested by: @{username}")
            return False

    async def stop(self):
        """Stop the bot gracefully"""
        await self.client.disconnect()
        print("✅ Telegram client stopped")


# For testing independently
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Telegram credentials
    api_id = int(os.environ["TELEGRAM_API_ID"])
    api_hash = os.environ["TELEGRAM_API_HASH"]
    session_string = os.environ["TELEGRAM_SESSION_STRING"]
    chat_id = int(os.environ["TELEGRAM_CHAT_ID"])

    # Create YouTube client
    youtube_client = YouTubeClient(
        credentials_path=os.environ["YOUTUBE_CREDENTIALS_PATH"],
        token_path=os.environ["YOUTUBE_TOKEN_PATH"],
        playlist_id=os.environ["YOUTUBE_PLAYLIST_ID"]
    )
    
    # Authenticate YouTube
    youtube_client.authenticate()
    print("✅ YouTube authenticated")

    # Create and start bot
    bot = TelegramToYouTubeBot(api_id, api_hash, session_string, chat_id, youtube_client)
    asyncio.run(bot.start())

