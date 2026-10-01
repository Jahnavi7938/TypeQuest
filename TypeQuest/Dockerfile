
# ==========================================
# TypeQuest - Docker Configuration
# ==========================================

# 1. Use Python base image
FROM python:3.12-slim

# 2. Set working directory inside container
WORKDIR /app

# 3. Python environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 4. Copy requirements file
COPY requirements.txt .

# 5. Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copy application files
COPY . .

# 7. Expose Flask application port
EXPOSE 5000

# 8. Start Flask using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]