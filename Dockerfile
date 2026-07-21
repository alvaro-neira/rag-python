FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY .env .env

# Create data directory for Chroma
RUN mkdir -p ./data

# Set default port and expose it
ENV PORT=8000
EXPOSE ${PORT}

# Run the application
CMD ["python", "-m", "app.main"]