from pyrogram.client import Client
from bot.config import Config

app = Client(
    "bot_session",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workdir="."
)

user_client = None
if Config.SESSION_STRING:
    user_client = Client(
        "user_session",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        session_string=Config.SESSION_STRING,
        workdir="."
    )
