FROM ubuntu:22.04

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Clone repository
RUN git clone https://github.com/manjunathaacharya3/test-analytics-portal.git .

# Checkout branch
RUN git checkout develop

# Create virtual environment
RUN python3 -m venv venv

# Install dependencies using venv pip
RUN ./venv/bin/pip install --upgrade pip setuptools wheel
RUN ./venv/bin/pip install -r requirements.txt

EXPOSE 8050

# Run app (adjust if needed)
CMD ["./venv/bin/python", "python -m uvicorn service.main:app --reload --host 0.0.0.0 --port 8000", "ui/dashboard.py"]
