# Use an official Python slim image for a smaller footprint
FROM python:3.12-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/app

# Set work directory
WORKDIR $HOME

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt $HOME/requirements.txt
RUN pip install --no-cache-dir -r $HOME/requirements.txt
RUN pip install --no-cache-dir daphne

# Copy project files
COPY . $HOME

# Create a non-root user and change ownership
RUN useradd -m appuser && chown -R appuser:appuser $HOME
USER appuser

# Healthcheck to ensure the container is running
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Make entrypoint executable
RUN chmod +x $HOME/entrypoint.sh

# Use entrypoint script
ENTRYPOINT ["/home/app/entrypoint.sh"]

# Corrected CMD for the vendor project
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "vendor.asgi:application"]
