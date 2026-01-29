# Base Image: Python 3.10 Slim (Tactical Light Gear)
FROM python:3.10-slim

# Set working directory inside the tank
WORKDIR /app

# Copy the arsenal
# We copy requirements first for caching (even if empty for now)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and config
COPY src/ ./src/
COPY config/ ./config/

# Environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Expose the Web Port
EXPOSE 8000

# Run the Server instead of the script
CMD ["python", "src/teamsintegration/server.py"]
