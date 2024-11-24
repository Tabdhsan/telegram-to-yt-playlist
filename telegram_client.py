from telethon import TelegramClient
from telethon.sessions import StringSession


class TelegramYoutubeClient:
    """
    A client for interacting with Telegram to fetch YouTube links from messages.

    Attributes:
        api_id: Telegram API ID
        api_hash: Telegram API hash
        session_string: Telegram session string for authentication
        chat_id: ID of the chat to monitor
    """

    def __init__(self, api_id: int, api_hash: str, session_string: str, chat_id: int):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_string = session_string
        self.chat_id = chat_id
        self.client = None
        self.error_log = []

    async def connect(self) -> None:
        """Initialize and connect the Telegram client"""
        try:
            self.client = TelegramClient(
                StringSession(self.session_string), self.api_id, self.api_hash
            )
            await self.client.connect()
        except Exception as e:
            self.error_log.append(f"Failed to connect to Telegram: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect the client"""
        if self.client:
            try:
                await self.client.disconnect()
            except Exception as e:
                self.error_log.append(f"Error disconnecting from Telegram: {e}")
                raise

    async def get_youtube_messages(self, limit: int = 10) -> list[dict]:
        """
        Get messages containing YouTube links
        Returns a list of dictionaries containing message details, sorted by date
        """
        try:
            # Get more messages than needed to ensure we find enough YouTube links
            messages = await self.client.get_messages(self.chat_id, limit=100)
            youtube_messages = []

            for message in messages:
                if message.text and (
                    "youtube" in message.text.lower()
                    or "youtu.be" in message.text.lower()
                ):
                    sender = await message.get_sender()
                    youtube_messages.append(
                        {
                            "username": (
                                sender.username
                                if sender and sender.username
                                else "Unknown"
                            ),
                            "text": message.text,
                            "date": message.date,
                        }
                    )

                    # Break if we have enough messages
                    if len(youtube_messages) >= limit:
                        break

            # Sort messages by date, newest first
            youtube_messages.sort(key=lambda x: x["date"], reverse=True)

            # Return only the requested number of messages
            return youtube_messages[:limit]

        except Exception as e:
            self.error_log.append(f"Error fetching YouTube messages: {e}")
            self.error_log.append(f"Error type: {type(e)}")
            return []

    async def send_error_message(self, error_message: str) -> None:
        """Send an error message to the Telegram chat"""
        try:
            if self.client and self.client.is_connected():
                await self.client.send_message(
                    self.chat_id,
                    f"🚨 Bot Error:\n{error_message}",
                )
        except Exception as e:
            # If we can't send the error message, we'll have to log it somewhere else
            self.error_log.append(f"Failed to send error message: {e}")
