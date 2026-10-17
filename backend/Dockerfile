FROM python:3.11-slim

# RapidOCR / OpenCV need these native libraries at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libgl1-mesa-glx \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Single worker keeps the in-memory session store consistent across requests.
# Threads allow concurrent requests (e.g. a slow OCR upload + a question).
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-5000} -t 300 -w 1 --threads 4 app:app"]
