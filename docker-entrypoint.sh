#!/bin/bash
set -e

# Attende che il database sia pronto
echo "Attesa connessione PostgreSQL..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -c '\q'; do
  echo "PostgreSQL non ancora disponibile - in attesa..."
  sleep 2
done
echo "PostgreSQL disponibile!"

# Inizializza il database se necessario
echo "Inizializzazione del database..."
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Compila le traduzioni
echo "Compilazione delle traduzioni..."
python compile_translations.py

# Avvia l'applicazione
echo "Avvio dell'applicazione VitaLink..."
exec "$@"