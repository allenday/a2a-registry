# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Skip system dependencies for now - we'll use a simpler approach
# The application should work without gcc for basic functionality

# Copy requirements first for better caching
COPY pyproject.toml ./
COPY README.md ./

# Copy application code first so version can be read
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[dev]"

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check - using Python instead of curl
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["python", "-m", "a2a_registry.server"] 