import asyncio
from dotenv import load_dotenv
import os
from telegram_client import TelegramYoutubeClient
from youtube_client import YouTubeClient


async def main():
    # Load environment variables
    load_dotenv()

    # Initialize Telegram client
    telegram_client = TelegramYoutubeClient(
        api_id=int(os.getenv("API_ID")),
        api_hash=os.getenv("API_HASH"),
        session_string=os.getenv("TELEGRAM_SESSION"),
        chat_id=int(os.getenv("CHAT_ID")),
    )

    # Initialize YouTube client
    youtube_client = YouTubeClient(
        credentials_path=os.getenv("YOUTUBE_CREDENTIALS_PATH"),
        token_path="token.pickle",
        playlist_id=os.getenv("YOUTUBE_PLAYLIST_ID"),
    )

    try:
        # Connect to Telegram
        await telegram_client.connect()

        # Authenticate with YouTube
        youtube_client.authenticate()

        # Test YouTube connection
        if not youtube_client.test_connection():
            raise Exception("Failed to connect to YouTube API")

        print("\n1. Getting last 10 messages from Telegram...")
        # Get messages first (store them before deletion)
        messages = await telegram_client.client.get_messages(
            telegram_client.chat_id, limit=10
        )
        print(f"Found {len(messages)} messages")

        print("\n2. Extracting YouTube links...")
        # Get YouTube messages from stored messages
        youtube_messages = await telegram_client.get_youtube_messages(limit=10)

        if not youtube_messages:
            print("No YouTube links found in recent messages")
            return

        print("\n3. Adding videos to YouTube playlist...")
        # Process each YouTube message
        for message in youtube_messages:
            print(f"\nProcessing message from: {message['username']}")
            print(f"Date: {message['date']}")
            print(f"Message: {message['text']}")

            try:
                # Add video to YouTube playlist
                result = youtube_client.add_to_playlist(message["text"])
                if result:
                    print("✓ Successfully added to playlist")
                else:
                    print("⚠ Video was already in playlist or couldn't be added")
            except Exception as e:
                print(f"✗ Error adding video to playlist: {e}")

        print("\n4. Clearing Telegram chat...")
        # Delete the messages
        for i, message in enumerate(messages, 1):
            await message.delete()
            print(f"Deleted message {i}/{len(messages)}")

        print("\nAll operations completed successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Always disconnect Telegram client
        await telegram_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
