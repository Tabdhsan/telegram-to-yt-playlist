#!/bin/bash

# Stop and remove existing containers
sudo docker compose down

# Rebuild images and start containers
sudo docker compose up --build -d
