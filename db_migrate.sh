#!/bin/bash

echo "Running database migrations..."

flask db init || true

flask db migrate -m "Add missing columns"

flask db upgrade

echo "Migration completed successfully"