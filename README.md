# Telegram to YouTube Playlist Bot

Automatically save YouTube links from Telegram chats to a YouTube playlist.

## Features

-   Monitors specified Telegram chats/channels for YouTube links
-   Automatically adds found videos to a designated YouTube playlist
-   Prevents duplicate video additions
-   Cleans up processed messages
-   Reports errors directly to Telegram chat
-   Runs on AWS Lambda with hourly checks

## Prerequisites

-   Python 3.9+
-   AWS Account
-   Terraform installed
-   Git Bash (for Windows)
-   Telegram API credentials
-   YouTube API credentials

## Installation

1. Clone the repository:

```bash
git clone [repository-url]
cd telegram-to-yt-playlist
```

2. Install required packages:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file using `.env.example` as template

## Configuration

### Telegram Setup

1. Get your Telegram API credentials:

    - Visit https://my.telegram.org/apps
    - Create a new application
    - Note down the `api_id` and `api_hash`

2. Generate a session string:

    - Run `python get_session.py`
    - Enter your phone number and the verification code
    - Save the generated session string

3. Get the chat ID:
    - Open the chat in the web client for Telegram
    - The chat ID is shown in the URL bar as a number
    - Note the negative number (for groups) or username (for channels)

### YouTube Setup

1. Create project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable YouTube Data API v3
3. Create OAuth credentials and download as `telegram-2-yt-bot-creds.json`
4. Create/select YouTube playlist and copy its ID

### AWS Deployment

1. Configure AWS credentials:

```bash
aws configure
```

2. Deploy using provided script:

```env
TELEGRAM_SESSION="your_session_string"
API_ID=your_api_id
API_HASH="your_api_hash"
CHAT_ID=your_chat_id
YOUTUBE_CREDENTIALS_PATH="telegram-2-yt-bot-creds.json"
YOUTUBE_PLAYLIST_ID="your_playlist_id"
```

This will:

-   Create deployment package
-   Set up AWS Lambda function
-   Configure hourly EventBridge trigger
-   Set up necessary IAM roles

## Development

### Local Testing

```bash
python main.py
```

### Code Style

-   Uses Ruff for linting and formatting
-   Pre-commit hooks configured
-   Run `ruff check .` to lint
-   Run `ruff check --fix .` to auto-fix

### Error Handling

-   All errors are logged to Telegram chat
-   Duplicate videos are silently skipped
-   Failed operations leave messages in chat

## Infrastructure

-   AWS Lambda (Python 3.9 runtime)
-   EventBridge for scheduling
-   Terraform for infrastructure management
-   Deployment script handles packaging and updates

## Security Notes

-   Never commit sensitive files (.env, credentials)
-   Use terraform.tfvars for deployment configuration
-   Keep your session string private
-   Rotate API keys periodically

## Project Structure

```
project/
├── main.py                         # Main script
├── telegram_client.py              # Telegram client class
├── youtube_client.py               # YouTube client class
├── .env                           # Environment variables
├── .gitignore                     # Git ignore rules
├── README.md                      # Documentation
├── requirements.txt               # Python dependencies
├── telegram-2-yt-bot-creds.json  # (not in git)
└── token.pickle                   # (not in git)
```

## Error Handling

The script handles various errors:

-   Invalid YouTube links
-   Duplicate videos
-   Connection issues
-   Authentication failures
-   The errors are logged to the Telegram chat

## Security Notes

-   Never commit your `.env` file
-   Keep your `telegram-2-yt-bot-creds.json` private
-   Don't share your session string
-   Add all sensitive files to `.gitignore`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Development

### Code Style and Linting

This project uses Ruff for linting and code formatting. Ruff is configured in `pyproject.toml`.

To run the linter:

```bash
ruff check .
```

To automatically fix issues:

```bash
ruff check --fix .
```

Enabled rules:

-   `E`: pycodestyle errors
-   `F`: Pyflakes
-   `I`: isort
-   `N`: naming conventions
-   `W`: pycodestyle warnings
-   `B`: bugbear
-   `C4`: comprehensions
-   `UP`: pyupgrade
-   `RUF`: Ruff-specific rules

Ignored rules:

-   `D100`: Missing docstring in public module
-   `D104`: Missing docstring in public package

The project uses:

-   Line length: 88 characters (same as Black)
-   Python target version: 3.9
-   McCabe complexity: maximum of 10
