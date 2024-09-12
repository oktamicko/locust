# Gunakan image Python sebagai base image
FROM python:3.12-slim

# Set lingkungan kerja di dalam container
WORKDIR /app

# Salin file requirements.txt ke dalam container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Salin semua file dari direktori lokal ke dalam container
COPY . .

# Expose port 8089 untuk Locust web interface
EXPOSE 8089

# Perintah default untuk menjalankan Locust
ENTRYPOINT ["locust", "-f", "locustfile.py"]
