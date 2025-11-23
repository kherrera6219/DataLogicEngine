#!/bin/bash
set -e

echo "Starting UKG System..."

# Wait for database to be ready
until PGPASSWORD=$PGPASSWORD psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -c '\q' 2>/dev/null; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

echo "Database is ready!"

# Run database migrations
echo "Running database migrations..."
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Start backend in background
echo "Starting Flask backend..."
python app.py &

# Start frontend
echo "Starting Next.js frontend..."
npm start
