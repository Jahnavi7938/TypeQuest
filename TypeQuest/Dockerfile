
# ==========================================
# TypeQuest - Docker Configuration
# ==========================================

# 1. Python base image
FROM python:3.12-slim

# 2. Set working directory
WORKDIR /app

# 3. Python environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 4. Copy requirements
COPY requirements.txt .

# 5. Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copy project files
COPY . .

# 7. Create instance directory
RUN mkdir -p /app/instance

# 8. Expose Flask port
EXPOSE 5000

# 9. Start application using Gunicorn
# Preload loads the application before starting workers.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--preload", "--timeout", "120", "app:app"]