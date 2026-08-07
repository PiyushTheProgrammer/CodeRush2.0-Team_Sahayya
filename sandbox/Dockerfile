# Secure, lightweight execution sandbox for AE-02 Autonomous Research Agent
FROM python:3.11-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    NO_PROXY=1 \
    PLAYWRIGHT_BROWSERS_PATH=/home/sandboxuser/.cache/ms-playwright

# Install system dependencies required for Playwright and PyMuPDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    libglib2.0-0 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root sandbox user
RUN groupadd -g 1000 sandboxgroup && \
    useradd -u 1000 -g sandboxgroup -m -s /bin/bash sandboxuser

WORKDIR /app/sandbox

# Install Python packages: playwright, pymupdf (fitz), pandas, requests
RUN pip install --no-cache-dir \
    playwright==1.42.0 \
    pymupdf==1.23.26 \
    pandas==2.2.1 \
    requests==2.31.0

# Install Playwright Chromium browser binary without root dependency issues
RUN playwright install chromium

# Restrict permissions to sandboxuser
RUN chown -R sandboxuser:sandboxgroup /app/sandbox /home/sandboxuser

# Switch to unprivileged non-root user
USER sandboxuser

# Default command for sandbox container
CMD ["python", "-c", "print('AE-02 Execution Sandbox Ready. User:', __import__('getpass').getuser())"]
