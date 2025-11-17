# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for psycopg2 and runtime utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# --- FIX FOR entrypoint.sh PERMISSIONS ---
# Copy the entrypoint script and make it executable while still running as root.
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
# -----------------------------------------

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "inventory.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]