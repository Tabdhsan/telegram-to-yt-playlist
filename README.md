# Telegram to YouTube Playlist Bot

Automatically save YouTube links from Telegram chats to a YouTube playlist with seamless authentication via Telegram.

## ✨ Features

- 🎵 **Automatic YouTube Link Detection**: Monitors Telegram chats for YouTube links
- 📱 **Mobile URL Support**: Handles all YouTube URL formats including mobile (`m.youtube.com`)
- 🔐 **Telegram-Based Authentication**: No need to access Docker containers - authenticate via Telegram messages
- 🚫 **Duplicate Prevention**: Automatically skips videos already in the playlist
- 🗑️ **Message Cleanup**: Removes processed messages to keep chats clean
- 🔄 **Auto Token Refresh**: Handles YouTube API token expiration automatically
- 🐳 **Docker Ready**: Easy deployment with Docker containers

## 📋 Prerequisites

- Python 3.9+
- Docker (for containerized deployment)
- Telegram API credentials
- YouTube API credentials (Desktop Application type)
- A YouTube playlist to add videos to

## 🚀 Quick Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd telegram-to-yt-playlist
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Telegram Setup

#### Get API Credentials
1. Visit [https://my.telegram.org/apps](https://my.telegram.org/apps)
2. Create a new application
3. Note down the `api_id` and `api_hash`

#### Generate Session String
```bash
python get_telegram_session.py
```
- Enter your phone number and verification code
- Save the generated session string

#### Get Chat ID
1. Open the target chat in Telegram Web
2. The chat ID is in the URL (e.g., `-4685810350` for groups)
3. For private chats, use your user ID

### 4. YouTube API Setup

#### Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Enable **YouTube Data API v3**

#### Create Desktop Application Credentials ⚠️ **Important**
1. Go to **APIs & Services > Credentials**
2. Click **"+ CREATE CREDENTIALS"** > **"OAuth client ID"**
3. **Choose "Desktop application"** (NOT Web application)
4. Give it a name (e.g., "Telegram YouTube Bot")
5. Download the JSON file as `telegram-2-yt-bot-creds.json`

#### Get Playlist ID
1. Create or open your YouTube playlist
2. Copy the playlist ID from the URL: `https://youtube.com/playlist?list=PLAYLIST_ID_HERE`

### 5. Environment Configuration

Create a `.env` file:

```env
# Telegram Configuration
TELEGRAM_API_ID=your_telegram_api_id
TELEGRAM_API_HASH=your_telegram_api_hash
TELEGRAM_SESSION_STRING=your_telegram_session_string
TELEGRAM_CHAT_ID=your_chat_id_to_monitor

# YouTube Configuration
YOUTUBE_CREDENTIALS_PATH=telegram-2-yt-bot-creds.json
YOUTUBE_TOKEN_PATH=token.pickle
YOUTUBE_PLAYLIST_ID=your_youtube_playlist_id

# Optional: Separate chat for auth messages
# OWNER_CHAT_ID=your_personal_chat_id
```

## 🔐 Authentication Flow

### First Time Setup
1. **Run the bot**: `python main.py` or `docker compose up`
2. **Automatic auth request**: Bot sends you a Telegram message with OAuth URL
3. **Complete authorization**: Click the link and authorize the app
4. **Send auth code**: Copy the code and reply to the bot
5. **Done**: Bot completes authentication and starts monitoring

### When Tokens Expire
- Bot automatically detects expired tokens
- Sends you a new auth URL via Telegram
- Same process as first-time setup
- No need to restart or access containers

### Optional: Separate Auth Chat
- Set `OWNER_CHAT_ID` to receive auth messages in a different chat
- Useful for keeping auth separate from monitored chat
- If not set, uses the same chat as `TELEGRAM_CHAT_ID`

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and start
./deploy-docker.sh

# Or manually
docker compose up -d
```

### Check Status
```bash
# View logs
docker logs -f telegram-youtube-bot

# Check in Portainer (if installed)
# Navigate to your Portainer instance
```

### Environment Variables in Docker
- Place your `.env` file in the project root
- Docker Compose automatically loads it
- Ensure `telegram-2-yt-bot-creds.json` is in the project directory

## 📱 Supported YouTube URL Formats

The bot handles all YouTube URL formats:

- `https://youtube.com/watch?v=VIDEO_ID`
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://m.youtube.com/watch?v=VIDEO_ID` (mobile)
- `https://youtu.be/VIDEO_ID`
- `https://youtube.com/embed/VIDEO_ID`
- URLs with additional parameters (si=, feature=, etc.)

## 🔧 Troubleshooting

### "redirect_uri_mismatch" Error
- **Cause**: Using Web Application credentials instead of Desktop Application
- **Solution**: Create new Desktop Application credentials in Google Cloud Console

### Bot Not Detecting Messages
- **Check chat ID**: Ensure `TELEGRAM_CHAT_ID` matches the actual chat
- **Verify permissions**: Bot needs access to read messages in the chat
- **Test with simple YouTube URL**: Try `https://youtu.be/dQw4w9WgXcQ`

### Authentication Issues
- **Check credentials file**: Ensure `telegram-2-yt-bot-creds.json` is valid
- **Verify API enabled**: YouTube Data API v3 must be enabled in Google Cloud
- **Desktop app type**: Must use Desktop Application, not Web Application

### Docker Issues
- **File permissions**: Ensure `.env` and credentials files are readable
- **Port conflicts**: Default setup doesn't expose ports, should work anywhere
- **Logs**: Check `docker logs telegram-youtube-bot` for errors

## 📁 Project Structure

```
telegram-to-yt-playlist/
├── main.py                         # Main application entry point
├── telegram_client.py              # Telegram bot implementation
├── youtube_client.py               # YouTube API client
├── get_telegram_session.py         # Session string generator
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker container definition
├── docker-compose.yml             # Docker Compose configuration
├── deploy-docker.sh               # Deployment script
├── .env                           # Environment variables (create this)
├── telegram-2-yt-bot-creds.json  # Google credentials (download this)
└── token.pickle                   # YouTube tokens (auto-generated)
```

## 🔒 Security Notes

- **Never commit sensitive files**: `.env`, `telegram-2-yt-bot-creds.json`, `token.pickle`
- **Keep session strings private**: They provide full access to your Telegram account
- **Rotate credentials periodically**: Especially if compromised
- **Use separate bot account**: Consider using a dedicated Telegram account for the bot

## 🛠️ Development

### Local Testing
```bash
python main.py
```

### Code Quality
- **Linting**: `ruff check .`
- **Auto-fix**: `ruff check --fix .`
- **Pre-commit hooks**: Configured for automatic formatting

### Adding Features
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## ⚡ Quick Start Summary

1. **Get Telegram credentials** → [my.telegram.org/apps](https://my.telegram.org/apps)
2. **Generate session string** → `python get_telegram_session.py`
3. **Create Google Cloud project** → Enable YouTube Data API v3
4. **Create Desktop Application credentials** → Download JSON file
5. **Get YouTube playlist ID** → From playlist URL
6. **Create `.env` file** → With all credentials
7. **Run bot** → `python main.py` or `docker compose up`
8. **Authenticate via Telegram** → Click link, send auth code
9. **Start sharing YouTube links** → Bot automatically adds them to playlist!

🎉 **That's it! Your bot is now ready to automatically save YouTube links to your playlist!**
