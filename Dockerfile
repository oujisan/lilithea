# Gunakan image Python resmi yang ringan
FROM python:3.11-slim

# Set environment variables agar output Python tidak di-buffer (berguna untuk log Docker)
ENV PYTHONUNBUFFERED=1

# Set working directory di dalam container
WORKDIR /app

# Salin file requirements.txt
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh file proyek
COPY . .

# Command untuk menjalankan bot
CMD ["python", "lilithea.py"]
