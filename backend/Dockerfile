FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install Python packages with verbose output and specific order
RUN pip install --no-cache-dir numpy && \
    pip install --no-cache-dir -v moviepy && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge

# Create non-root user first
RUN useradd -m -u 1001 appuser


RUN mkdir -p /home/Bastian/development/uploads && \
    chown -R appuser:appuser /home/Bastian/development/uploads && \
    chmod -R 755 /home/Bastian/development/uploads

# Copy all application files
COPY . .

# Verify installation and fail early if something is wrong
RUN python -c "from moviepy.editor import VideoFileClip" && \
    python -c "import nltk; nltk.download('punkt')" && \
    python -c "import nltk; nltk.download('averaged_perceptron_tagger')" && \
    python -c "import nltk; nltk.download('vader_lexicon')"

# Switch to non-root user
USER appuser

# Set default environment variables that match docker-compose.yml
ENV FLASK_ENV=production \
    FLASK_DEBUG=false \
    FLASK_APP=app.py \
    UPLOAD_FOLDER=/home/Bastian/development/uploads \
    APP_HOST="0.0.0.0" \
    APP_PORT="5000" \
    ALLOWED_EXTENSIONS="mp4,avi,mov" \
    FRONTEND_URL="https://sensiwithme.my.id"

EXPOSE 5000

CMD ["python", "app.py"]