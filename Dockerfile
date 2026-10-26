FROM python:3.11-slim\n\n# Set working directory\nWORKDIR /app\n\n# Install system dependencies (if any) and clean up\nRUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*\n\n# Copy only requirements first for caching\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\n\n# Copy application code\nCOPY src/ ./src/\nCOPY specs/ ./specs/\nCOPY tests/ ./tests/\n\n# Default command runs the test suite\nCMD ["python", "-m", "pytest", "-q"]
