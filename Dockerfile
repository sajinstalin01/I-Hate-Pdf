FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MAX_UPLOAD_MB=40
RUN apt-get update && apt-get install -y --no-install-recommends \
    ghostscript libreoffice-writer libreoffice-calc libreoffice-impress \
    tesseract-ocr tesseract-ocr-eng libpango-1.0-0 libpangoft2-1.0-0 \
    libharfbuzz0b libffi-dev shared-mime-info fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--workers", "2", "--timeout", "180", "--bind", "0.0.0.0:5000", "server:app"]
