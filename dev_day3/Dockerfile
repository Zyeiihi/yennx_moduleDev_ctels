FROM python:3.10-slim

WORKDIR /app

# Cài đặt curl để thực hiện kiểm định sức khỏe Docker Healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "app.py"]