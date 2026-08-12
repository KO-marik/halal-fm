FROM python:3.10-slim

# Установка компиляторов и системных зависимостей для сборки C-расширений
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir --use-deprecated=legacy-resolver -r requirements.txt || pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]