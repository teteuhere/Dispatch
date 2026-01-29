#!/bin/bash

echo "--- DISPATCH: INITIATING DEPLOYMENT SEQUENCE ---"
echo "LOADING CREDENTIALS FROM .ENV..."

if [ ! -f .env ]; then
    echo "ERROR: .env file not found! Deployment aborted."
    exit 1
fi

if [ ! -d "logs" ]; then
    mkdir -p logs
    chmod 777 logs
fi


docker run -d \
  --restart unless-stopped \
  -p 8000:8000 \
  -v /etc/localtime:/etc/localtime:ro \
  -v $(pwd)/config:/app/config:z \
  -v $(pwd)/logs:/app/logs:z \
  --env-file .env \
  --name dispatch-core \
  dispatch
