# Koyeb Deployment Guide

## Prerequisites
- Koyeb account (https://www.koyeb.com)
- GitHub repository with your bot code
- Telegram API credentials (API_ID, API_HASH, BOT_TOKEN, OWNER_ID)
- PostgreSQL database connection string

## Deployment Steps

### 1. Connect GitHub Repository
1. Go to Koyeb Dashboard
2. Click "Create Service"
3. Select "GitHub" as deployment source
4. Authorize Koyeb with GitHub
5. Select your `channel-file-processor-bot` repository
6. Choose `main` branch

### 2. Configure Service
- **Name**: `channel-file-processor-bot`
- **Builder**: Docker
- **Dockerfile path**: `./Dockerfile`
- **Port**: Not needed (bot doesn't expose HTTP)

### 3. Set Environment Variables
In Koyeb, click "Secrets" and add:

```
API_ID=your_api_id
API_HASH=your_api_hash_here
BOT_TOKEN=your_bot_token_here
OWNER_ID=your_owner_id
DATABASE_URL=postgresql://user:password@host/dbname
PGDATABASE=your_db_name
PGHOST=your_db_host
PGPORT=5432
PGUSER=your_db_user
PGPASSWORD=your_db_password
PGUSER=your_db_user
SESSION_SECRET=your_session_secret
```

### 4. Deploy
1. Click "Deploy"
2. Wait for build to complete (usually 2-3 minutes)
3. Monitor logs to verify bot started successfully

### 5. Verify Deployment
- Go to Koyeb Dashboard > Your Service
- Click "Logs" to see bot output
- Confirm message: "Starting bot..."
- Check Telegram to verify bot is responsive

## Troubleshooting

**Bot not starting:**
- Check environment variables are set correctly
- Verify DATABASE_URL format
- Check logs for error messages

**Permission denied errors:**
- Ensure all required environment variables are set
- Check Telegram credentials are correct

**Connection timeout:**
- Verify DATABASE_URL and network connectivity
- Ensure PostgreSQL database is accessible from Koyeb

## Auto-Deployment
Every time you push to `main` branch, Koyeb will:
1. Automatically rebuild the Docker image
2. Deploy the new version
3. Restart the bot service

## Useful Commands

Check logs:
```bash
koyeb logs channel-file-processor-bot
```

Redeploy:
```bash
git push origin main  # Automatic redeploy triggered
```

## Local Testing with Docker

```bash
# Build image
docker build -t channel-file-processor-bot .

# Run with environment variables
docker run --env-file .env channel-file-processor-bot

# Or with docker-compose
docker-compose up
```

---

For more help, visit: https://docs.koyeb.com
