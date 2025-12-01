# Channel File Processor Bot

A Telegram bot that downloads files from source channels, applies filters, renames them, and uploads to destination channels.

## Features

- Download files from a range of messages in source channels
- Whitelist/blacklist word filtering for file names
- File renaming with prefix/suffix
- Custom thumbnail support for uploads
- Logging to console and optional log channel
- Multiple source and destination channels support

## Setup

### 1. Get Telegram API Credentials

1. Go to [https://my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Go to "API development tools"
4. Create a new application
5. Note down your `API_ID` and `API_HASH`

### 2. Create a Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the instructions
3. Note down the `BOT_TOKEN`

### 3. Get Your User ID

1. Search for [@userinfobot](https://t.me/userinfobot) on Telegram
2. Start the bot
3. It will show your user ID - note this as `OWNER_ID`

### 4. Get Channel IDs

For private channels:
1. Forward a message from the channel to [@userinfobot](https://t.me/userinfobot)
2. Note the channel ID (it will be negative, like `-1001234567890`)

For public channels:
- You can use the username (e.g., `@mychannel`)

### 5. Environment Variables

Set the following environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `API_ID` | Yes | Telegram API ID |
| `API_HASH` | Yes | Telegram API Hash |
| `BOT_TOKEN` | Yes | Bot token from BotFather |
| `OWNER_ID` | Yes | Your Telegram user ID |
| `SOURCE_CHANNEL_IDS` | No | Comma-separated source channel IDs |
| `DESTINATION_CHANNEL_IDS` | No | Comma-separated destination channel IDs |
| `LOG_CHANNEL_ID` | No | Channel ID for logging |
| `WHITELIST_WORDS` | No | Comma-separated words to include |
| `BLACKLIST_WORDS` | No | Comma-separated words to exclude |
| `FILE_PREFIX` | No | Prefix to add to file names |
| `FILE_SUFFIX` | No | Suffix to add to file names |
| `SESSION_STRING` | No | User session string for advanced features |

### 6. Add Bot to Channels

1. Add the bot as an admin to your source channels (with read access)
2. Add the bot as an admin to your destination channels (with post permissions)

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Show welcome message and status |
| `/help` | Show detailed help |
| `/status` | Show current configuration |
| `/setrange <start_link> <end_link>` | Set message range to process |
| `/process` | Start processing files |
| `/setthumb` | Reply to a photo to set as thumbnail |
| `/delthumb` | Delete the current thumbnail |
| `/setwhitelist word1, word2` | Set whitelist words (session only) |
| `/setblacklist word1, word2` | Set blacklist words (session only) |

## Usage Example

1. Start the bot: `/start`

2. Set the message range:
   ```
   /setrange https://t.me/c/1234567890/1 https://t.me/c/1234567890/100
   ```

3. Start processing:
   ```
   /process
   ```

The bot will:
- Fetch all messages from ID 1 to 100
- Filter based on whitelist/blacklist
- Download each file
- Rename if prefix/suffix is set
- Upload to destination channel(s)
- Show progress and final statistics

## Filter Logic

### Whitelist
If whitelist words are set, only files containing at least one whitelist word in the filename will be processed.

### Blacklist
If blacklist words are set, files containing any blacklist word in the filename will be skipped.

### Priority
Blacklist is checked first. If a file matches a blacklist word, it's skipped even if it matches a whitelist word.

## Project Structure

```
.
├── main.py              # Entry point
├── bot/
│   ├── __init__.py
│   ├── client.py        # Pyrogram client setup
│   ├── config.py        # Environment configuration
│   ├── filters.py       # Whitelist/blacklist logic
│   ├── handlers.py      # Bot command handlers
│   ├── processor.py     # File processing logic
│   └── thumbnail.py     # Thumbnail management
├── downloads/           # Temporary download folder
├── thumbnails/          # Thumbnail storage
└── README.md
```

## Running the Bot

```bash
python main.py
```

## Deployment on Replit

1. Fork this project on Replit
2. Add your environment variables in the Secrets tab
3. Click Run

## Notes

- The bot must be an admin in both source and destination channels
- Processing large ranges may take time due to Telegram rate limits
- Files are temporarily downloaded and deleted after upload
- Session whitelist/blacklist changes are not persistent (use env vars for permanent settings)
