FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libpq-dev postgresql-client iproute2 net-tools curl dos2unix \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir .

RUN mkdir -p /app/uploads && chmod 777 /app/uploads

RUN dos2unix /app/docker-entrypoint.sh \
 && chmod +x /app/docker-entrypoint.sh \
 && dos2unix /app/db_migrate.sh \
 && chmod +x /app/db_migrate.sh

EXPOSE $PORT

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["sh", "-c", "/app/db_migrate.sh && gunicorn --bind $HOST:$PORT --workers 3 --access-logfile - --error-logfile - --log-level $(echo ${LOG_LEVEL} | tr '[:upper:]' '[:lower:]') $FLASK_APP"]