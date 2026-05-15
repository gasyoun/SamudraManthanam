FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if needed (e.g., for SQLite)
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY web/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY web/ .

# Set environment variables
ENV CORPUS_PATH=/corpus
ENV DB_PATH=/app/corpus.db
ENV PYTHONPATH=/app

# Expose the FastAPI port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
