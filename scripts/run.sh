#!/bin/bash

echo "--- DISPATCH: INITIATING DEPLOYMENT SEQUENCE ---"

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
  --name dispatch-core \
  dispatch
