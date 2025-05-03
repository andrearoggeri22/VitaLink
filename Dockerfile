FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libpq-dev postgresql-client iproute2 net-tools curl dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Copiamo tutto il contenuto del progetto
COPY . /app/

# Installiamo i requisiti da requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir .

RUN mkdir -p /app/uploads && chmod 777 /app/uploads

# Prepariamo lo script di entrypoint
RUN dos2unix /app/docker-entrypoint.sh \
 && chmod +x /app/docker-entrypoint.sh

 RUN echo '#!/bin/bash\n\
echo "Running database migrations..."\n\
export FLASK_APP=app\n\
flask db init || true\n\
flask db migrate -m "Add missing columns"\n\
flask db upgrade\n\
echo "Migration completed"\n\
' > /app/run_migrations.sh \
 && chmod +x /app/run_migrations.sh

EXPOSE $PORT

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["sh", "-c", "gunicorn --bind $HOST:$PORT --workers 3 --access-logfile - --error-logfile - --log-level debug app:app"]
CMD ["sh", "-c", "/app/run_migrations.sh && gunicorn --bind $HOST:$PORT --workers 3 --access-logfile - --error-logfile - --log-level debug app:app"]
