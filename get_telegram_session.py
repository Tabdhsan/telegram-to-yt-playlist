from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import os
from dotenv import load_dotenv

load_dotenv()

api_id = os.environ["TELEGRAM_API_ID"]
api_hash = os.environ["TELEGRAM_API_HASH"]

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("Your session string:")
    print(client.session.save())
