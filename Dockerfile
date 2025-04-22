FROM python:3.11-slim

WORKDIR /app

# Install the system's needed dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    postgresql-client \
    iproute2 \
    net-tools \
    curl \
    && rm -rf /var/lib/apt/lists/*

# First copy only the requirements.txt to exploit Docker cache
COPY docker-requirements.txt /app/

# Install python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r docker-requirements.txt

# Copy the remaining code of the application
COPY . /app/

# Creating the uploads directory if it doesn't exists
RUN mkdir -p /app/uploads && chmod 777 /app/uploads

# Make entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Expose the port on which the app will be listening
EXPOSE 5000

# Default environment variables (can be overwritten)
ENV FLASK_APP=main.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Configure the entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Note: curl already installed before

# Startup command
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "debug", "main:app"]