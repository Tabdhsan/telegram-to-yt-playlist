from telethon import TelegramClient
from telethon.sessions import StringSession
from typing import List, Dict


class TelegramYoutubeClient:
    def __init__(self, api_id: int, api_hash: str, session_string: str, chat_id: int):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_string = session_string
        self.chat_id = chat_id
        self.client = None

    async def connect(self):
        """Initialize and connect the Telegram client"""
        self.client = TelegramClient(
            StringSession(self.session_string), self.api_id, self.api_hash
        )
        await self.client.connect()

    async def disconnect(self):
        """Disconnect the client"""
        if self.client:
            await self.client.disconnect()

    async def get_youtube_messages(self, limit: int = 10) -> List[Dict]:
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
            print(f"An error occurred: {e}")
            print(f"Error type: {type(e)}")
            return []
