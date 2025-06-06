import os
import asyncio
from dotenv import load_dotenv
from telegram_client import TelegramToYouTubeBot
from youtube_client import YouTubeClient


async def main():
    """Main entry point for the Telegram to YouTube Bot"""
    print("🤖 Telegram to YouTube Playlist Bot")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Get owner chat ID (optional, defaults to main chat)
        owner_chat_id = os.environ.get("OWNER_CHAT_ID")
        if owner_chat_id:
            owner_chat_id = int(owner_chat_id)
        else:
            owner_chat_id = int(os.environ["TELEGRAM_CHAT_ID"])
        
        # Create Telegram bot first (we need the client for YouTube auth)
        print("🚀 Initializing Telegram bot...")
        bot = TelegramToYouTubeBot(
            api_id=int(os.environ["TELEGRAM_API_ID"]),
            api_hash=os.environ["TELEGRAM_API_HASH"],
            session_string=os.environ["TELEGRAM_SESSION_STRING"],
            chat_id=int(os.environ["TELEGRAM_CHAT_ID"]),
            youtube_client=None,  # Will be set after YouTube client creation
            owner_chat_id=owner_chat_id
        )
        
        # Start Telegram client for authentication purposes
        await bot.client.start()
        print("✅ Telegram client ready for authentication")
        
        # Create and authenticate YouTube client with Telegram integration
        print("🔐 Authenticating with YouTube...")
        youtube_client = YouTubeClient(
            credentials_path=os.environ["YOUTUBE_CREDENTIALS_PATH"],
            token_path=os.environ["YOUTUBE_TOKEN_PATH"],
            playlist_id=os.environ["YOUTUBE_PLAYLIST_ID"],
            telegram_client=bot.client,
            owner_chat_id=owner_chat_id
        )
        
        # Authenticate asynchronously
        await youtube_client.authenticate_async()
        
        # Set the YouTube client in the bot
        bot.youtube_client = youtube_client
        
        # Test YouTube connection
        if youtube_client.test_connection():
            print("✅ YouTube API connection verified")
        else:
            print("❌ YouTube API connection failed")
            print("Errors:", youtube_client.error_log)
            return
        
        # Set up event handlers and start listening
        print("🎧 Setting up message handlers...")
        await bot.setup_handlers()
        
        # Keep the bot running
        print("✅ Bot is now running and listening for YouTube links!")
        await bot.client.run_until_disconnected()
        
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal - stopping bot...")
    except Exception as e:
        print(f"❌ Bot crashed: {e}")
    finally:
        print("✅ Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
