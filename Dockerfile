FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy all project files
COPY . .

# Make sure the startup script is executable
RUN chmod +x ./START_SERVER.sh

# Expose FastAPI port
EXPOSE 8000

# Run the startup script
CMD ["./START_SERVER.sh"]

