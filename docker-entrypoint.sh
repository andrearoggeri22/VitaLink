#!/bin/bash
set -e

# Print debug information about the environment
echo "Verifica configurazione di rete..."
ip addr show
echo "Porte in ascolto:"
netstat -tulpn || ss -tulpn || echo "Comando netstat/ss non disponibile"

# Wait for PostgreSQL to be ready
echo "Attesa connessione PostgreSQL..."
until PGPASSWORD=$PGPASSWORD psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -c '\q'; do
  echo "PostgreSQL non ancora disponibile - in attesa..."
  sleep 2
  # Print debug information about the connection attempt
  echo "Tentativo di connessione a $PGHOST:$PGPORT con utente $PGUSER e database $PGDATABASE"
done
echo "PostgreSQL disponibile!"

# Initialize database if needed
echo "Inizializzazione del database..."
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Compile translations
echo "Compilazione delle traduzioni..."
python compile_translations.py

# Check bind address for Gunicorn
echo "Verifica configurazione Gunicorn..."
echo "Parametri: $@"

# Start application
echo "Avvio dell'applicazione VitaLink su 0.0.0.0:5000..."
exec "$@"