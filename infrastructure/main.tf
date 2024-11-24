terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-2"
}

# Lambda function
resource "aws_lambda_function" "telegram_youtube_bot" {
  filename         = "../lambda_deployment.zip"
  function_name    = "telegram-youtube-bot"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.9"
  timeout         = 180  # 3 minutes
  memory_size     = 256

  environment {
    variables = {
      API_ID                  = var.telegram_api_id
      API_HASH                = var.telegram_api_hash
      TELEGRAM_SESSION        = var.telegram_session
      CHAT_ID                = var.telegram_chat_id
      YOUTUBE_PLAYLIST_ID     = var.youtube_playlist_id
      YOUTUBE_CREDENTIALS_PATH = var.youtube_credentials_path
    }
  }
}

# EventBridge rule to trigger Lambda
resource "aws_cloudwatch_event_rule" "every_hour" {
  name                = "every-hour"
  description         = "Triggers telegram-youtube-bot every hour"
  schedule_expression = "rate(1 hour)"
}

resource "aws_cloudwatch_event_target" "trigger_lambda" {
  rule      = aws_cloudwatch_event_rule.every_hour.name
  target_id = "TelegramYouTubeBot"
  arn       = aws_lambda_function.telegram_youtube_bot.arn
}

# IAM role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "telegram_youtube_bot_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Allow EventBridge to invoke Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.telegram_youtube_bot.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_hour.arn
}
