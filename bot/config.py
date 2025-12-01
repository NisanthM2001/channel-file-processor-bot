import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Read-only from env (API credentials)
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    SESSION_STRING = os.getenv("SESSION_STRING", "")
    LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID", "")
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    
    # Persistent settings (loaded from storage, not env)
    SOURCE_CHANNEL_IDS = []
    DESTINATION_CHANNEL_IDS = []
    WHITELIST_WORDS = []
    BLACKLIST_WORDS = []
    REMOVED_WORDS = []  # Words to remove from filename (case-sensitive exact match)
    FILE_PREFIX = ""
    FILE_SUFFIX = ""
    REMOVE_USERNAME = False
    CUSTOM_CAPTION = ""
    START_LINK = None
    END_LINK = None
    PROCESS_ABOVE_2GB = False  # Telegram Premium restriction
    
    DOWNLOAD_DIR = "downloads"
    THUMBNAIL_DIR = "thumbnails"
    
    @classmethod
    def is_configured(cls):
        return all([cls.API_ID, cls.API_HASH, cls.BOT_TOKEN, cls.OWNER_ID])
    
    @classmethod
    def get_info(cls):
        return {
            "api_configured": bool(cls.API_ID and cls.API_HASH),
            "bot_token_set": bool(cls.BOT_TOKEN),
            "source_channels": len(cls.SOURCE_CHANNEL_IDS),
            "destination_channels": len(cls.DESTINATION_CHANNEL_IDS),
            "log_channel_set": bool(cls.LOG_CHANNEL_ID),
            "whitelist_words": cls.WHITELIST_WORDS,
            "blacklist_words": cls.BLACKLIST_WORDS,
        }
