FROM python:3.11-slim

WORKDIR /app

# Installa le dipendenze di sistema necessarie
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copia prima solo il file dei requisiti per sfruttare la cache Docker
COPY docker-requirements.txt /app/

# Installa le dipendenze Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r docker-requirements.txt

# Copia il resto del codice dell'applicazione
COPY . /app/

# Creazione della directory uploads se non esiste
RUN mkdir -p /app/uploads && chmod 777 /app/uploads

# Rendi eseguibile lo script di entrypoint
RUN chmod +x /app/docker-entrypoint.sh

# Esponi la porta su cui sarà in ascolto l'app
EXPOSE 5000

# Variabili d'ambiente predefinite (possono essere sovrascritte)
ENV FLASK_APP=main.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Configura l'entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Installa curl per health check
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Comando di avvio
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "debug", "main:app"]