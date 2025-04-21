#!/bin/bash
set -e

# Stampa informazioni di debug sul networking
echo "Verifica configurazione di rete..."
ip addr show
echo "Porte in ascolto:"
netstat -tulpn || ss -tulpn || echo "Comando netstat/ss non disponibile"

# Attende che il database sia pronto
echo "Attesa connessione PostgreSQL..."
until PGPASSWORD=$PGPASSWORD psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -c '\q'; do
  echo "PostgreSQL non ancora disponibile - in attesa..."
  sleep 2
  # Stampa informazioni di debug sui tentativi di connessione
  echo "Tentativo di connessione a $PGHOST:$PGPORT con utente $PGUSER e database $PGDATABASE"
done
echo "PostgreSQL disponibile!"

# Inizializza il database se necessario
echo "Inizializzazione del database..."
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Compila le traduzioni
echo "Compilazione delle traduzioni..."
python compile_translations.py

# Verifica bind address per Gunicorn
echo "Verifica configurazione Gunicorn..."
echo "Parametri: $@"

# Avvia l'applicazione
echo "Avvio dell'applicazione VitaLink su 0.0.0.0:5000..."
exec "$@"