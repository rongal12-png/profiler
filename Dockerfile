FROM python:3.11-slim

WORKDIR /app

# Set environment variables to prevent buffering
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies (including WeasyPrint deps for PDF generation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libcairo2 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install in smaller batches to avoid I/O errors in Docker Desktop
RUN pip install --no-cache-dir fastapi uvicorn[standard] sqlalchemy psycopg2-binary celery[redis] gevent
RUN pip install --no-cache-dir python-dotenv requests pydantic pydantic-settings Jinja2 markdown2 click python-multipart
RUN pip install --no-cache-dir web3
RUN pip install --no-cache-dir solana solders
RUN pip install --no-cache-dir pandas matplotlib numpy
RUN pip install --no-cache-dir weasyprint

COPY . .

# The entrypoint will be provided by docker-compose commands
