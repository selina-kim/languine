# Use Python 3.11 slim image as base (minimal Debian-based image)
FROM python:3.11-slim

# Set working directory for the application
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libsndfile1 \
    espeak-ng \
    mecab \
    libmecab-dev \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry for dependency management
RUN pip install poetry

# Install gcc
RUN apt-get update && apt-get install -y gcc build-essential && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml poetry.lock* ./
# Install Python dependencies in virtual environment
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-root && \
    # Install Japanese dictionary for MeCab (used by TTS Japanese phonemizer)
    /app/.venv/bin/pip install unidic-lite && \
    # Create MeCab config directory
    mkdir -p /usr/local/etc && \
    # Write MeCab config file pointing to unidic-lite dictionary location
    echo "dicdir = $(/app/.venv/bin/python -c 'import unidic_lite; print(unidic_lite.DICDIR)')" > /usr/local/etc/mecabrc

# Copy application source code
COPY . .

# Set environment variables
# PATH: Add virtual environment to PATH
# PYTHONUNBUFFERED: Ensure Python output is sent straight to terminal
# FLASK_APP: Specify Flask application entry point
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=src.main:app

# Run Flask development server on all network interfaces
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
