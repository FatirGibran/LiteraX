FROM python:3.12-slim-bookworm

WORKDIR /app

# Install essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Install local package
RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "literax.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
