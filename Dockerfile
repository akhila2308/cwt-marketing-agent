FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create output and log dirs
RUN mkdir -p output logs samples

# Default: dry run (no posting)
CMD ["python", "main.py"]
