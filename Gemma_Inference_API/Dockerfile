FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    make \
    python3-dev \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /inference_service

# Copy requirements
COPY inference_requirments.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r inference_requirments.txt

# Install PyTorch
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126

# Copy code + model
COPY . .

# Optional: enable Flask dev mode
ENV FLASK_ENV=development

# Expose the port
EXPOSE 8081

# Run dev server (with Flask's built-in server)
CMD ["python", "run.py"]
