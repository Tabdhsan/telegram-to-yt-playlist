# Telegram to YouTube Playlist

Automatically save YouTube links from Telegram chats to a YouTube playlist.

## Features

-   Monitors specified Telegram chats/channels for YouTube links
-   Automatically adds found videos to a designated YouTube playlist
-   Supports both group chats and channels
-   Can be deployed locally or as AWS Lambda function
-   Handles duplicate videos and various error cases

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

3. Create a `.env` file in the project root (see Configuration section)

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

1. Set up Google Cloud Project:

    - Go to [Google Cloud Console](https://console.cloud.google.com/)
    - Create a new project
    - Enable YouTube Data API v3

2. Create OAuth 2.0 credentials:

    - Navigate to APIs & Services > Credentials
    - Create OAuth client ID
    - Choose Desktop Application
    - Download the credentials JSON file
    - Include `http://localhost:8080/` in the "Authorized redirect URIs"
    - Add scope: `https://www.googleapis.com/auth/youtube.force-ssl`
    - Rename it to `telegram-2-yt-bot-creds.json`

3. Get your YouTube playlist ID:
    - Create a playlist on YouTube if you haven't already
    - Open the playlist
    - Copy the ID from the URL (after `?list=`)

### Environment Variables

Create a `.env` file with the following:

```env
TELEGRAM_SESSION="your_session_string"
API_ID=your_api_id
API_HASH="your_api_hash"
CHAT_ID=your_chat_id
YOUTUBE_CREDENTIALS_PATH="telegram-2-yt-bot-creds.json"
YOUTUBE_PLAYLIST_ID="your_playlist_id"
```

## Deployment Options

### Local Deployment

Run the main script:

```bash
python main.py
```

The script will:

1. Connect to Telegram and YouTube
2. Get the last 10 messages from the specified chat
3. Extract YouTube links
4. Add videos to your playlist
5. Delete the processed messages

#### First Run

On first run:

1. The script will open your browser
2. Log in to your Google account
3. Grant the required permissions
4. A token file will be saved for future use

### AWS Lambda Deployment

For automated execution, you can deploy the script to AWS Lambda:

#### 1. Prepare the Deployment Package

```bash
mkdir package
cd package
pip install --target . -r ../requirements.txt
cp ../{main.py,telegram_client.py,youtube_client.py,lambda_function.py} .
cp ../token.pickle .
cp ../telegram-2-yt-bot-creds.json .
zip -r ../lambda_deployment.zip .
```

#### 2. Create Lambda Function

-   Runtime: Python 3.9
-   Handler: lambda_function.lambda_handler
-   Memory: 256 MB (minimum)
-   Timeout: 3 minutes
-   Environment variables:
    -   API_ID
    -   API_HASH
    -   TELEGRAM_SESSION
    -   CHAT_ID
    -   YOUTUBE_PLAYLIST_ID

#### 3. Deploy

-   Upload lambda_deployment.zip to Lambda
-   The lambda_deployment.zip must contain your token.pickle file in advance
-   Add EventBridge (CloudWatch Events) trigger
-   Set schedule (e.g., rate(1 hour))

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

Common linting rules enabled:

-   E/W: pycodestyle errors and warnings
-   F: Pyflakes
-   I: isort
-   N: naming conventions
-   B: bugbear
-   C4: comprehensions
-   UP: pyupgrade
-   RUF: Ruff-specific rules
