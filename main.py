import asyncio
import os
from typing import Optional

from dotenv import load_dotenv

from telegram_client import TelegramYoutubeClient
from youtube_client import YouTubeClient


async def process_youtube_links(
    telegram_client: TelegramYoutubeClient, youtube_client: YouTubeClient
) -> None:
    """Process YouTube links from Telegram messages"""
    try:
        # Get messages containing YouTube links
        messages = await telegram_client.get_youtube_messages()

        # Process each message
        for message in messages:
            try:
                # Extract YouTube URL from message
                text = message["text"]
                if "youtube.com" in text or "youtu.be" in text:
                    # Add video to playlist
                    response = youtube_client.add_to_playlist(text)
                    if response:
                        await telegram_client.send_error_message(
                            f"✅ Added video from {message['username']} to playlist"
                        )

            except Exception as e:
                await telegram_client.send_error_message(
                    f"❌ Failed to process message from {message['username']}: {e}"
                )

    except Exception as e:
        await telegram_client.send_error_message(f"❌ Failed to process messages: {e}")


async def main() -> None:
    """Main function to run the bot"""
    # Load environment variables
    load_dotenv()

    # Initialize clients
    telegram_client = TelegramYoutubeClient(
        api_id=int(os.getenv("API_ID", "0")),
        api_hash=os.getenv("API_HASH", ""),
        session_string=os.getenv("TELEGRAM_SESSION", ""),
        chat_id=int(os.getenv("CHAT_ID", "0")),
    )

    youtube_client = YouTubeClient(
        credentials_path=os.getenv("YOUTUBE_CREDENTIALS_PATH", ""),
        token_path="token.pickle",
        playlist_id=os.getenv("YOUTUBE_PLAYLIST_ID", ""),
    )

    try:
        # Connect to Telegram
        await telegram_client.connect()

        # Authenticate with YouTube
        youtube_client.authenticate()

        # Test YouTube connection
        if not youtube_client.test_connection():
            await telegram_client.send_error_message(
                "❌ Failed to connect to YouTube API\n"
                + "\n".join(youtube_client.error_log)
            )
            return

        # Process YouTube links
        await process_youtube_links(telegram_client, youtube_client)

        # Check for any accumulated errors
        if youtube_client.error_log:
            await telegram_client.send_error_message(
                "⚠️ YouTube Client Errors:\n" + "\n".join(youtube_client.error_log)
            )

        if telegram_client.error_log:
            await telegram_client.send_error_message(
                "⚠️ Telegram Client Errors:\n" + "\n".join(telegram_client.error_log)
            )

    except Exception as e:
        await telegram_client.send_error_message(f"❌ Critical error: {e}")

    finally:
        # Always disconnect from Telegram
        await telegram_client.disconnect()


def lambda_handler(event: dict, context: Optional[dict] = None) -> dict:
    """AWS Lambda handler"""
    try:
        asyncio.run(main())
        return {"statusCode": 200, "body": "Success"}
    except Exception as e:
        return {"statusCode": 500, "body": f"Error: {e!s}"}


if __name__ == "__main__":
    asyncio.run(main())
