#!/bin/bash
set -e

# Print debug information about the environment
echo "Verifying network configuration..."
ip addr show
echo "Listening ports:"
netstat -tulpn || ss -tulpn || echo "netstat/ss command not available"

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL connection..."
until PGPASSWORD=$PGPASSWORD psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -c '\q'; do
  echo "PostgreSQL not yet available - waiting..."
  sleep 2
  # Print debug information about the connection attempt
  echo "Trying to connect to $PGHOST:$PGPORT with user $PGUSER and database $PGDATABASE"
done
echo "PostgreSQL available!"

# Initialize database if needed
echo "Initializing database..."
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Compile translations
echo "Compiling translations..."
python compile_translations.py

# Check bind address for Gunicorn
echo "Verifying Gunicorn configuration..."
echo "Parameters: $@"

# Start application
echo "Starting VitaLink application on 0.0.0.0:5000..."
exec "$@"