import os
from PIL import Image
from bot.config import Config

THUMBNAIL_PATH = os.path.join(Config.THUMBNAIL_DIR, "default_thumb.jpg")

def save_thumbnail(photo_path: str) -> bool:
    try:
        os.makedirs(Config.THUMBNAIL_DIR, exist_ok=True)
        
        with Image.open(photo_path) as img:
            img = img.convert("RGB")
            img.thumbnail((320, 320))
            img.save(THUMBNAIL_PATH, "JPEG", quality=85)
        
        return True
    except Exception as e:
        print(f"Error saving thumbnail: {e}")
        return False

def get_thumbnail() -> str | None:
    if os.path.exists(THUMBNAIL_PATH):
        return THUMBNAIL_PATH
    return None

def delete_thumbnail() -> bool:
    try:
        if os.path.exists(THUMBNAIL_PATH):
            os.remove(THUMBNAIL_PATH)
            return True
        return False
    except Exception as e:
        print(f"Error deleting thumbnail: {e}")
        return False

def has_thumbnail() -> bool:
    return os.path.exists(THUMBNAIL_PATH)
