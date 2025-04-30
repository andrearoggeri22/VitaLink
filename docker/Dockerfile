FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libpq-dev postgresql-client iproute2 net-tools curl dos2unix \
    && rm -rf /var/lib/apt/lists/*


# Copiamo tutto il contenuto del progetto
COPY . /app/

# Installa le dipendenze da requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/uploads && chmod 777 /app/uploads

RUN dos2unix /app/docker/docker-entrypoint.sh \
 && chmod +x  /app/docker/docker-entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["/app/docker/docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", \
     "--access-logfile", "-", "--error-logfile", "-", "--log-level", "debug", "app:app"]