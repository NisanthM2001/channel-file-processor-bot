import os
import re
import asyncio
import time
from pyrogram.client import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from typing import List, Tuple
from bot.config import Config
from bot.filters import get_file_name, should_process_file, rename_file, has_downloadable_media
from bot.thumbnail import get_thumbnail

# Global state
current_status = {
    'status': 'idle',
    'file_name': None,
    'current_size': 0,
    'total_size': 0,
    'current_index': 0,  # Current file being processed (1-based)
    'processed': 0,      # Completed files count
    'total': 0,          # Total files in range
    'download_speed': 0,
    'upload_speed': 0,
    'cancel_all': False,
    'queue': [],
    'skipped': 0,        # Skipped file count
    'premium_count': 0,  # Premium files count (>2GB)
    'to_process': 0,     # Files to process (total - skipped)
}

# Speed tracking
dl_speed_data = {'last_time': 0, 'last_bytes': 0}
ul_speed_data = {'last_time': 0, 'last_bytes': 0}

def format_bytes(bytes_val: int) -> str:
    val = float(bytes_val)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if val < 1024:
            return f"{val:.1f}{unit}"
        val /= 1024
    return f"{val:.1f}TB"

def get_progress_bar(current: int, total: int, width: int = 12) -> str:
    if total == 0:
        return "█" * width
    percentage = current / total
    filled = int(width * percentage)
    bar = "█" * filled + "░" * (width - filled)
    return bar

def get_cancel_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel All", callback_data="cancel_all_now")]
    ])

def extract_language_and_subtitle(file_name: str) -> tuple:
    """Extract language and subtitle from filename - leech bot style"""
    if not file_name:
        return "Unknown", ""
    
    file_lower = file_name.lower()
    
    # Language patterns - ORDERED FROM MOST SPECIFIC
    lang_patterns = [
        (r'\[?english\]?|\[?eng\]?|esub', ('English', 'Esub')),
        (r'\[?hindi\]?|\[?hin\]?|hsub', ('Hindi', 'Hsub')),
        (r'\[?telugu\]?|\[?tel\]?|tesub', ('Telugu', 'Tesub')),
        (r'\[?kannada\]?|\[?kan\]?|ksub', ('Kannada', 'Ksub')),
        (r'\[?tamil\]?|\[?tam\]?|tsub', ('Tamil', 'Tsub')),
        (r'\[?malayalam\]?|\[?mal\]?|msub', ('Malayalam', 'Msub')),
        (r'\[?punjabi\]?|\[?pan\]?|psub', ('Punjabi', 'Psub')),
    ]
    
    for pattern, (lang, sub_abbr) in lang_patterns:
        if re.search(pattern, file_lower):
            subtitle = sub_abbr if re.search(r'esub|hsub|tesub|ksub|tsub|msub|psub|sub', file_lower) else ""
            return lang, subtitle
    
    return "Unknown", ""

def get_status_text() -> str:
    """Real-time progress UI with new design"""
    global current_status
    
    status = current_status['status']
    file_name = current_status.get('file_name', 'Unknown')
    current_index = current_status.get('current_index', 0)  # Which file we're on (1-based)
    processed = current_status.get('processed', 0)  # Completed files
    total = current_status.get('total', 0)
    skipped = current_status.get('skipped', 0)
    premium_count = current_status.get('premium_count', 0)
    to_process = current_status.get('to_process', 0)
    current_sz = current_status.get('current_size', 0)
    total_sz = current_status.get('total_size', 0)
    dl_speed = current_status.get('download_speed', 0)
    ul_speed = current_status.get('upload_speed', 0)
    queue = current_status.get('queue', [])
    
    if status == 'idle':
        return "✅ Ready to process"
    
    # Phase indicator
    if status == 'downloading':
        phase = "📥 DOWNLOADING"
        speed = dl_speed
        current_phase = "Downloading"
    else:
        phase = "📤 UPLOADING"
        speed = ul_speed
        current_phase = "Uploading"
    
    # Progress calculation
    progress_pct = (current_sz / total_sz * 100) if total_sz > 0 else 0
    progress_bar = get_progress_bar(current_sz, total_sz)
    
    # Calculate remaining files to process
    remaining = total - processed - skipped
    
    # Build new UI - show current file index / total
    text = f"<b>{phase}</b> {current_index}/{to_process}\n\n"
    text += f"<b>📄 {file_name}</b>\n\n"
    text += f"{progress_bar} <b>{progress_pct:.0f}%</b>\n"
    text += f"<b>💾</b> {format_bytes(current_sz)} / {format_bytes(total_sz)}\n"
    text += f"<b>🚀</b> {format_bytes(speed)}/s\n"
    
    # Queue display - minimum 5 files
    if queue:
        text += f"\n<b>━━━━━━━━━━━━━━━━━━</b>\n"
        text += f"<b>📋 QUEUE ({len(queue)}+):</b>\n"
        
        for i, q_file in enumerate(queue[:5]):
            q_name = q_file['name']
            skip_reason = q_file.get('skip_reason', None)
            is_premium = q_file.get('premium', False)
            
            # Truncate name
            if len(q_name) > 32:
                name_parts = q_name.rsplit('.', 1)
                if len(name_parts) == 2:
                    base, ext = name_parts
                    q_name = base[:28] + ".." + "." + ext
                else:
                    q_name = q_name[:32] + ".."
            
            # Determine indicator
            if skip_reason:
                indicator = f"✗ {q_name} (Skip - {skip_reason})"
            elif is_premium:
                indicator = f"⭐ {q_name} (Premium)"
            else:
                indicator = f"✓ {q_name}"
            
            text += f"  {i+1}. {indicator}\n"
        
        if len(queue) > 5:
            remaining_queue = len(queue) - 5
            text += f"  <i>+{remaining_queue} more...</i>"
    
    # Progress section with file counts
    text += f"\n<b>━━━━━━━━━━━━━━━━━━</b>\n"
    text += f"<b>📈 PROGRESS:</b>\n"
    text += f"  ✅ Processed: {processed}\n"
    text += f"  ⏳ Currently: {current_phase}\n"
    text += f"  📌 Remaining: {remaining}\n"
    text += f"\n<b>📊 FILE COUNTS:</b>\n"
    text += f"  📥 Total Found: {total}\n"
    text += f"  ✓ To Process: {to_process}\n"
    text += f"  ⭐ Premium (>2GB): {premium_count}\n"
    text += f"  ✗ Skipped: {skipped}"
    
    return text

async def process_range(client: Client, start_link: str, end_link: str, status_message: Message):
    """Main processor with dynamic captions and proper cancel handling"""
    global current_status, dl_speed_data, ul_speed_data
    
    current_status['cancel_all'] = False
    current_status['status'] = 'fetching'
    current_status['skipped'] = 0
    
    try:
        # Parse links
        if '/c/' in start_link:
            channel_id_str = start_link.split('/c/')[1].split('/')[0]
            start_id = int(start_link.split('/')[-1])
            source_channel = int('-100' + channel_id_str)
        else:
            parts = start_link.split('/')
            start_id = int(parts[-1])
            source_id = int(parts[-2])
            source_channel = int('-100' + str(source_id))
        
        if '/c/' in end_link:
            end_id = int(end_link.split('/')[-1])
        else:
            end_id = int(end_link.split('/')[-1])
        
        # Fetch all messages
        all_msgs = []
        for msg_id in range(start_id, end_id + 1):
            if current_status['cancel_all']:
                break
            try:
                msg = await client.get_messages(source_channel, msg_id)
                if msg and has_downloadable_media(msg):
                    all_msgs.append((msg_id, msg))
            except:
                pass
        
        if not all_msgs:
            return None, "❌ No files found in range"
        
        # Build queue with skip reasons
        queue_list = []
        skipped_count = 0
        
        for msg_id, msg in all_msgs:
            file_name = get_file_name(msg)
            should_process, reason = should_process_file(file_name)
            
            processed_name = rename_file(file_name)
            
            file_size = 0
            if msg.document:
                file_size = msg.document.file_size
            elif msg.video:
                file_size = msg.video.file_size
            elif msg.audio:
                file_size = msg.audio.file_size
            
            SIZE_2GB = 2 * 1024 * 1024 * 1024
            is_premium = file_size > SIZE_2GB
            
            skip_reason = None
            
            if not should_process:
                skip_reason = reason
                skipped_count += 1
            elif is_premium and not Config.PROCESS_ABOVE_2GB:
                skip_reason = "Premium"
                skipped_count += 1
            
            # Add all files to queue (both processable and skip-marked)
            queue_list.append({
                'msg_id': msg_id,
                'msg': msg,
                'name': processed_name,
                'premium': is_premium,
                'file_size': file_size,
                'original_name': file_name,
                'skip_reason': skip_reason,
            })
        
        if not queue_list:
            return None, "❌ No files found in range"
        
        # Count premium files
        premium_count = sum(1 for item in queue_list if item.get('premium', False))
        to_process_count = len(queue_list) - skipped_count
        
        # Initialize
        current_status['total'] = len(queue_list)
        current_status['processed'] = 0
        current_status['skipped'] = skipped_count
        current_status['premium_count'] = premium_count
        current_status['to_process'] = to_process_count
        current_status['queue'] = queue_list[1:] if len(queue_list) > 1 else []
        
        processed_count = 0
        failed_count = 0
        
        # Update UI task
        update_running = True
        last_update_text = ""
        
        async def update_ui():
            nonlocal update_running, last_update_text
            first_update = True
            
            while update_running:
                try:
                    new_text = get_status_text()
                    
                    if first_update or new_text != last_update_text:
                        await status_message.edit_text(
                            new_text,
                            reply_markup=get_cancel_button(),
                            parse_mode=ParseMode.HTML
                        )
                        last_update_text = new_text
                        first_update = False
                except:
                    pass
                
                if not update_running or current_status['cancel_all']:
                    break
                
                await asyncio.sleep(3)
        
        update_task = asyncio.create_task(update_ui())
        
        # Process files
        completed_count = 0
        current_file_index = 0  # Track current file position
        for idx, queue_item in enumerate(queue_list):
            if current_status['cancel_all']:
                break
            
            msg_id = queue_item['msg_id']
            msg = queue_item['msg']
            file_name = queue_item['name']
            original_name = queue_item['original_name']
            skip_reason = queue_item.get('skip_reason')
            
            # Update queue display (show remaining files)
            current_status['queue'] = queue_list[idx+1:] if idx+1 < len(queue_list) else []
            
            # Skip files that should not be processed
            if skip_reason:
                continue
            
            # Increment file index when starting to process a file
            current_file_index += 1
            current_status['current_index'] = current_file_index
            
            download_path = os.path.join(Config.DOWNLOAD_DIR, file_name)
            
            try:
                # DOWNLOAD
                current_status['status'] = 'downloading'
                current_status['file_name'] = file_name
                current_status['current_size'] = 0
                current_status['total_size'] = queue_item['file_size']
                current_status['download_speed'] = 0
                
                dl_speed_data['last_time'] = time.time()
                dl_speed_data['last_bytes'] = 0
                
                def download_progress(current, total):
                    if current_status['cancel_all']:
                        return
                    global dl_speed_data
                    current_status['current_size'] = current
                    current_status['total_size'] = total
                    
                    now = time.time()
                    elapsed = now - dl_speed_data['last_time']
                    
                    if elapsed > 0.5 and elapsed > 0:
                        bytes_in_period = current - dl_speed_data['last_bytes']
                        current_status['download_speed'] = bytes_in_period / elapsed
                        dl_speed_data['last_bytes'] = current
                        dl_speed_data['last_time'] = now
                
                try:
                    await client.download_media(msg, file_name=download_path, progress=download_progress)
                except Exception as e:
                    if current_status['cancel_all']:
                        try:
                            os.remove(download_path)
                        except:
                            pass
                        break
                    raise
                
                if current_status['cancel_all']:
                    try:
                        os.remove(download_path)
                    except:
                        pass
                    break
                
                # UPLOAD
                current_status['status'] = 'uploading'
                current_status['current_size'] = 0
                current_status['upload_speed'] = 0
                
                actual_size = os.path.getsize(download_path) if os.path.exists(download_path) else 0
                current_status['total_size'] = actual_size
                
                ul_speed_data['last_time'] = time.time()
                ul_speed_data['last_bytes'] = 0
                
                # Extract language and subtitle
                language, subtitle = extract_language_and_subtitle(original_name)
                
                # Build caption with variables
                caption_template = Config.CUSTOM_CAPTION or "{filename} | {language} {subtitle}"
                caption = caption_template.format(
                    filename=file_name,
                    filesize=format_bytes(actual_size),
                    language=language,
                    subtitle=subtitle,
                    filecaption=msg.caption or ""
                )
                
                thumbnail = get_thumbnail()
                
                def upload_progress(current, total):
                    if current_status['cancel_all']:
                        return
                    global ul_speed_data
                    current_status['current_size'] = current
                    current_status['total_size'] = total if total > 0 else actual_size
                    
                    now = time.time()
                    elapsed = now - ul_speed_data['last_time']
                    
                    if elapsed > 0.5 and elapsed > 0:
                        bytes_in_period = current - ul_speed_data['last_bytes']
                        current_status['upload_speed'] = bytes_in_period / elapsed
                        ul_speed_data['last_bytes'] = current
                        ul_speed_data['last_time'] = now
                
                # Upload to destinations
                for dest_channel in Config.DESTINATION_CHANNEL_IDS:
                    if current_status['cancel_all']:
                        break
                    
                    try:
                        current_status['current_size'] = 0
                        ul_speed_data['last_time'] = time.time()
                        ul_speed_data['last_bytes'] = 0
                        
                        await client.send_document(
                            dest_channel,
                            download_path,
                            caption=caption,
                            thumb=thumbnail,
                            progress=upload_progress
                        )
                    except Exception as e:
                        if current_status['cancel_all']:
                            break
                        continue
                
                if current_status['cancel_all']:
                    try:
                        os.remove(download_path)
                    except:
                        pass
                    break
                
                # Cleanup
                try:
                    os.remove(download_path)
                except:
                    pass
                
                # Only increment after SUCCESSFUL processing
                completed_count += 1
                current_status['processed'] = completed_count
                
            except Exception as e:
                print(f"Error: {e}")
                failed_count += 1
                try:
                    if os.path.exists(download_path):
                        os.remove(download_path)
                except:
                    pass
                if current_status['cancel_all']:
                    break
        
        # Stop update
        update_running = False
        
        current_status['status'] = 'idle'
        current_status['queue'] = []
        
        summary = f"✅ <b>Complete!</b>\n\n📊 <b>Results:</b>\n✅ Processed: {completed_count}\n⏭️ Skipped: {current_status['skipped']}\n❌ Failed: {failed_count}"
        return None, summary
        
    except Exception as e:
        current_status['status'] = 'idle'
        return None, f"❌ Error: {str(e)[:100]}"
