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
        # Create and authenticate YouTube client
        print("🔐 Authenticating with YouTube...")
        youtube_client = YouTubeClient(
            credentials_path=os.environ["YOUTUBE_CREDENTIALS_PATH"],
            token_path=os.environ["YOUTUBE_TOKEN_PATH"],
            playlist_id=os.environ["YOUTUBE_PLAYLIST_ID"]
        )
        youtube_client.authenticate()
        
        # Test YouTube connection
        if youtube_client.test_connection():
            print("✅ YouTube API connection verified")
        else:
            print("❌ YouTube API connection failed")
            print("Errors:", youtube_client.error_log)
            return
        
        # Create Telegram bot with YouTube integration
        print("🚀 Starting Telegram bot...")
        bot = TelegramToYouTubeBot(
            api_id=int(os.environ["TELEGRAM_API_ID"]),
            api_hash=os.environ["TELEGRAM_API_HASH"],
            session_string=os.environ["TELEGRAM_SESSION_STRING"],
            chat_id=int(os.environ["TELEGRAM_CHAT_ID"]),
            youtube_client=youtube_client
        )
        
        # Start the bot (runs indefinitely)
        await bot.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal - stopping bot...")
    except Exception as e:
        print(f"❌ Bot crashed: {e}")
    finally:
        print("✅ Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
