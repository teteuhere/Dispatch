# Base Image
FROM python:3.10-slim

# Set Working Directory
WORKDIR /app

# Install System Dependencies (for pywebview/GTK if needed in container, usually headless)
# Kept minimal for server mode
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libgirepository1.0-dev \
    libcairo2-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Source Code
COPY . .

# Expose Port
EXPOSE 8000

CMD ["python", "src/dispatch/server.py"]
