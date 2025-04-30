#!/bin/bash
set -e

echo "Verifying network configuration..."
ip addr show
echo "Listening ports:"
netstat -tulpn || ss -tulpn || echo "netstat/ss command not available"

echo "Waiting for PostgreSQL connection..."
until PGPASSWORD=$PGPASSWORD psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -c '\q'; do
  echo "PostgreSQL not yet available - waiting..."
  sleep 2
  echo "Trying to connect to $PGHOST:$PGPORT with user $PGUSER and database $PGDATABASE"
done
echo "PostgreSQL available!"

echo "Initializing database..."
python - <<'PY'
from app import app, db
with app.app_context():
    db.create_all()
PY

echo "Compiling translations..."
python -m app.compile_translations

echo "Verifying Gunicorn configuration..."
echo "Parameters: $@"

echo "Starting VitaLink application on $HOST:$PORT..."
exec "$@"
