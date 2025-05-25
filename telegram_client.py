from telethon import TelegramClient, events
from telethon.sessions import StringSession
import asyncio


class TelegramYoutubeClient:
    """
    Async Telegram client using Telethon with event-driven new message handling.
    Listens to a specific chat for messages containing YouTube links.
    """

    def __init__(self, api_id: int, api_hash: str, session_string: str, chat_id: int):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_string = session_string
        self.chat_id = chat_id
        self.client = TelegramClient(StringSession(session_string), api_id, api_hash)
        self.error_log = []

    async def start(self):
        """Start the Telegram client and add event handlers"""
        try:
            await self.client.start()
            print("Telegram client started.")

            # Add event handler for new messages in the chat
            self.client.add_event_handler(self.new_message_handler, events.NewMessage(chats=self.chat_id))

            # Keep the client running until explicitly stopped
            print(f"Listening for new messages in chat: {self.chat_id} ...")
            await self.client.run_until_disconnected()

        except Exception as e:
            self.error_log.append(f"Failed to start Telegram client: {e}")
            raise

    async def new_message_handler(self, event: events.NewMessage.Event):
        """Handle new incoming messages with YouTube links"""
        try:
            message = event.message
            text = message.text or ""
            if "youtube.com" in text.lower() or "youtu.be" in text.lower():
                sender = await message.get_sender()
                username = sender.username if sender and sender.username else "Unknown"

                print(f"New YouTube link from @{username}: {text}")

                # Here you can call your YouTubeClient logic to add video
                # e.g. await self.process_youtube_link(text)

                # For now, just send a confirmation message back to chat
                await self.client.send_message(
                    self.chat_id, f"✅ Received and processing YouTube link from @{username}"
                )

        except Exception as e:
            error_msg = f"Error in new_message_handler: {e}"
            self.error_log.append(error_msg)
            print(error_msg)

    async def stop(self):
        """Stop the Telegram client"""
        await self.client.disconnect()
        print("Telegram client stopped.")


# To test independently:
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    # Load environment variables from .env file
    load_dotenv()

    api_id = int(os.environ["TELEGRAM_API_ID"])  # throws KeyError if not set
    api_hash = os.environ["TELEGRAM_API_HASH"]
    session_string = os.environ["TELEGRAM_SESSION_STRING"]
    chat_id = int(os.environ["TELEGRAM_CHAT_ID"])


    client = TelegramYoutubeClient(api_id, api_hash, session_string, chat_id)

    asyncio.run(client.start())

