FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONMALLOC=malloc
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV OPENBLAS_NUM_THREADS=1
ENV PORT=8000

# Install essential Linux graphics & vision dependencies for OpenCV & FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    libsm6 \
    libxext6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install PyTorch CPU (lightweight ~180MB wheel, ideal for cloud containers) and dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy codebase
COPY . .

EXPOSE 8000

CMD ["python", "backend/run_server.py"]

