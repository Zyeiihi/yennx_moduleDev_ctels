FROM python:3.10-slim

# Cài đặt curl phục vụ healthcheck và tini để quản lý kill tiến trình lập tức
RUN apt-get update && apt-get install -y curl tini && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# Ép biến môi trường Flask chạy trên host 0.0.0.0 bảo mật toàn bộ các cổng container
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8080

# Sử dụng Tini làm ENTRYPOINT để bắt tín hiệu kill (SIGTERM/SIGINT) ngay lập tức
ENTRYPOINT ["/usr/bin/tini", "--"]

# Lệnh khởi chạy ứng dụng
CMD ["python", "app.py"]