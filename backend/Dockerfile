# Use Python 3.11 slim image as base (minimal Debian-based image)
FROM python:3.11-slim

# Set working directory for the application
WORKDIR /app

# Install system dependencies + Rust (required by sudachipy)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libsndfile1 \
    espeak-ng \
    mecab \
    libmecab-dev \
    curl \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Add Rust to PATH
ENV PATH="/root/.cargo/bin:$PATH"

# Install Poetry for dependency management
RUN pip install --no-cache-dir poetry

# Install gcc
RUN apt-get update && apt-get install -y gcc build-essential && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Configure poetry and install dependencies (including dev for testing)
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-root --no-interaction --no-ansi && \
    # Install production WSGI server
    /app/.venv/bin/pip install --no-cache-dir gunicorn && \
    # Install PyTorch (CPU) explicitly as TTS requires it
    /app/.venv/bin/pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    # Install Japanese dictionary for MeCab
    /app/.venv/bin/pip install --no-cache-dir unidic-lite && \
    # Pre-download the XTTS v2 multilingual model (supports 17 languages)
    # Set COQUI_TOS_AGREED to accept terms non-interactively
    COQUI_TOS_AGREED=1 /app/.venv/bin/python -c "from TTS.api import TTS; TTS('tts_models/multilingual/multi-dataset/xtts_v2')" && \
    # Clean up Poetry cache and pip cache
    poetry cache clear pypi --all -n && \
    rm -rf /root/.cache

# Create MeCab config directory and write config file
RUN mkdir -p /usr/local/etc && \
    # Point to the unidic-lite dictionary
    echo "dicdir = $(/app/.venv/bin/python -c 'import unidic_lite; print(unidic_lite.DICDIR)')" > /usr/local/etc/mecabrc

# Copy application source code including tests
COPY src/ ./src/

# Set environment variables
# PATH: Add virtual environment to PATH
# PYTHONUNBUFFERED: Ensure Python output is sent straight to terminal
# FLASK_APP: Specify Flask application entry point
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=src.main:app

# Run application with Gunicorn on all network interfaces
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "300", "--access-logfile", "-", "--error-logfile", "-", "src.main:app"]