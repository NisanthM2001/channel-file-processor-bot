from bot.config import Config

def get_file_name(message):
    if message.document:
        return message.document.file_name or ""
    elif message.video:
        return message.video.file_name or ""
    elif message.audio:
        return message.audio.file_name or ""
    elif message.photo:
        return f"photo_{message.id}.jpg"
    elif message.caption:
        return message.caption
    return ""

def should_process_file(file_name: str) -> tuple[bool, str]:
    if not file_name:
        return False, "No file name found"
    
    name_lower = file_name.lower()
    
    if Config.BLACKLIST_WORDS:
        for word in Config.BLACKLIST_WORDS:
            if word in name_lower:
                return False, f"Blacklisted word: {word}"
    
    if Config.WHITELIST_WORDS:
        found = False
        for word in Config.WHITELIST_WORDS:
            if word in name_lower:
                found = True
                break
        if not found:
            return False, "No whitelist word found"
    
    return True, "OK"

def rename_file(original_name: str) -> str:
    import re
    
    if not original_name:
        return original_name
    
    name_parts = original_name.rsplit('.', 1)
    
    if len(name_parts) == 2:
        base_name, extension = name_parts
    else:
        base_name = original_name
        extension = None
    
    # Step 1: Remove ALL underscores first (replace with space to preserve word boundaries)
    base_name = base_name.replace('_', ' ')
    
    # Step 2: Remove @username patterns from ANYWHERE in filename if enabled
    if Config.REMOVE_USERNAME:
        base_name = re.sub(r'@\w+', '', base_name)  # Fixed: \S+ was too greedy
    
    # Step 3: Remove www.1tamilmv.* patterns (where * is dynamic)
    base_name = re.sub(r'www\.1tamilmv\.\S+\s*', '', base_name)
    
    # Step 4: Remove specified words (case-sensitive exact match)
    if Config.REMOVED_WORDS:
        for word in Config.REMOVED_WORDS:
            base_name = base_name.replace(word, '')
    
    # Step 5: Clean up extra spaces (multiple spaces to single space)
    base_name = re.sub(r'\s+', ' ', base_name)
    base_name = base_name.strip()
    
    # Step 6: Add prefix and suffix
    if base_name:  # Only add prefix/suffix if there's actual content left
        new_name = f"{Config.FILE_PREFIX}{base_name}{Config.FILE_SUFFIX}"
    else:
        new_name = original_name  # Fallback to original if everything was removed
    
    # Step 7: Add extension back if it existed
    if extension:
        new_name = f"{new_name}.{extension}"
    
    return new_name

def has_downloadable_media(message) -> bool:
    return any([
        message.document,
        message.video,
        message.audio,
        message.photo
    ])
