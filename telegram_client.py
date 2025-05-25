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

    def __init__(self, api_id: int, api_hash: str, session_string: str, chat_id: int, youtube_client: YouTubeClient):
        # Telegram setup
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_string = session_string
        self.chat_id = chat_id
        self.client = TelegramClient(StringSession(session_string), api_id, api_hash)
        
        # YouTube integration
        self.youtube_client = youtube_client
        
        # Error logging
        self.error_log = []

    async def start(self):
        """Start the bot - authenticate and listen for messages"""
        try:
            # Start Telegram client
            await self.client.start()
            print("✅ Telegram client started")

            # Add event handler for new messages in the chat
            self.client.add_event_handler(self.handle_new_message, events.NewMessage(chats=self.chat_id))

            # Keep the client running until explicitly stopped
            print(f"🎧 Listening for YouTube links in chat: {self.chat_id}")
            await self.client.run_until_disconnected()

        except Exception as e:
            self.error_log.append(f"Failed to start Telegram client: {e}")
            raise

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
                
                # Process each YouTube URL
                for url in youtube_urls:
                    await self.process_youtube_url(url, username)
                
                # Delete the processed message
                try:
                    await message.delete()
                    print("🗑️ Message deleted")
                except Exception as e:
                    print(f"⚠️ Could not delete message: {e}")

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
            r'https?://(?:www\.)?youtube\.com/v/[\w-]+(?:\?[\w=&]*)?'
        ]
        
        urls = []
        for pattern in patterns:
            urls.extend(re.findall(pattern, text, re.IGNORECASE))
        
        return list(set(urls))  # Remove duplicates

    async def process_youtube_url(self, url: str, username: str):
        """Process a single YouTube URL - add to playlist"""
        try:
            print(f"🎵 Processing: {url}")
            
            # Add to YouTube playlist (run in executor since it's synchronous)
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.youtube_client.add_to_playlist, url
            )
            
            if result:
                print(f"✅ Added to playlist: {url}")
                print(f"   └─ Requested by: @{username}")
            else:
                print(f"ℹ️ Video already in playlist: {url}")
                print(f"   └─ Requested by: @{username}")
                
        except Exception as e:
            print(f"❌ Failed to add {url} to playlist: {e}")
            print(f"   └─ Requested by: @{username}")

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

