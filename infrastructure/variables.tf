variable "telegram_api_id" {
  description = "Telegram API ID"
  type        = string
  sensitive   = true
}

variable "telegram_api_hash" {
  description = "Telegram API Hash"
  type        = string
  sensitive   = true
}

variable "telegram_session" {
  description = "Telegram Session String"
  type        = string
  sensitive   = true
}

variable "telegram_chat_id" {
  description = "Telegram Chat ID"
  type        = string
  sensitive   = true
}

variable "youtube_playlist_id" {
  description = "YouTube Playlist ID"
  type        = string
  sensitive   = true
}

variable "youtube_credentials_path" {
  description = "Path to YouTube credentials file"
  type        = string
  default     = "telegram-2-yt-bot-creds.json"
}
