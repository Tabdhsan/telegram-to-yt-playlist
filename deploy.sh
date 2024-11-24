#!/bin/bash

echo "🚀 Starting deployment..."

# Move to project root (if not already there)
cd "$(dirname "$0")"

# First destroy existing resources
echo "🧹 Destroying existing resources..."
cd infrastructure || exit
terraform destroy -auto-approve
cd ..

# Clean up
echo "🧹 Cleaning up old files..."
rm -rf package lambda_deployment.zip

# Create package
echo "📦 Creating deployment package..."
mkdir package
cd package || exit
pip install --target . -r ../requirements.txt
cp ../{main.py,telegram_client.py,youtube_client.py,lambda_function.py} .
cp ../token.pickle .
cp ../telegram-2-yt-bot-creds.json .

# Use PowerShell to create zip
echo "📦 Creating zip file..."
powershell -Command "Compress-Archive -Path * -DestinationPath ../lambda_deployment.zip -Force"

# Move back to root
cd ..

# Verify zip exists
if [ ! -f "lambda_deployment.zip" ]; then
    echo "❌ Failed to create lambda_deployment.zip"
    exit 1
fi

cd infrastructure || exit

# Deploy
echo "🚀 Deploying with Terraform..."
terraform apply -auto-approve

echo "✅ Deployment complete!"
