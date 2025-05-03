#!/bin/bash
set -e

echo "Environment: CLOUD_RUN_ENVIRONMENT=${CLOUD_RUN_ENVIRONMENT}"
echo "Verifying network configuration..."
ip addr show
echo "Listening ports:"
netstat -tulpn || ss -tulpn || echo "netstat/ss command not available"

# Only perform database check if not in Cloud Run environment
if [ "${CLOUD_RUN_ENVIRONMENT}" != "true" ]; then
  echo "Running in local/development environment, checking PostgreSQL connection..."
  
  # Maximum retries for database connection
  MAX_RETRIES=30
  RETRY_COUNT=0
  
  echo "Waiting for PostgreSQL connection at ${PGHOST}:${PGPORT}..."
  until PGPASSWORD=$PGPASSWORD psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -c '\q' || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
    echo "PostgreSQL not yet available - retry ${RETRY_COUNT}/${MAX_RETRIES}..."
    RETRY_COUNT=$((RETRY_COUNT+1))
    sleep 2
    echo "Trying to connect to $PGHOST:$PGPORT with user $PGUSER and database $PGDATABASE"
  done
  
  if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
    echo "PostgreSQL available!"
  else
    echo "WARNING: Could not connect to PostgreSQL after ${MAX_RETRIES} attempts"
    echo "Application will try to connect during runtime"
  fi
else
  echo "Running in Cloud Run environment, skipping local PostgreSQL check"
fi

echo "Initializing database..."
python - <<'PY'
import logging
logging.basicConfig(level=logging.INFO)
try:
    from app import app, db
    with app.app_context():
        db.create_all()
        run_migration()
    print("Database initialization completed successfully")
except Exception as e:
    print(f"Error initializing database: {e}")
    print("The application will attempt to initialize on startup")
PY

echo "Verifying Gunicorn configuration..."
echo "Parameters: $@"

echo "Starting VitaLink application on $HOST:$PORT..."
exec "$@"
