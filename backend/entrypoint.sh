#!/bin/sh
set -e # Exit immediately if a command exits with a non-zero status.

# Change to the /app directory where your backend package and alembic.ini are expected to reside
cd /app

# Extract DB_HOST (e.g., emm_postgres_db)
DB_HOST=$(echo "$DATABASE_URL" | sed -e 's|.*@||g' -e 's|:.*||g' -e 's|/.*||g')

# Extract DB_PORT (e.g., 5432). Default to 5432 if not explicitly in URL
DB_PORT=$(echo "$DATABASE_URL" | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
if [ -z "$DB_PORT" ]; then
    DB_PORT="5432" # Default PostgreSQL port
fi

# Extract DB_USER (e.g., user)
DB_USER=$(echo "$DATABASE_URL" | sed -e 's|postgresql://||g' -e 's|:.*||g')

# Extract DB_NAME (e.g., backend_db)
DB_NAME=$(echo "$DATABASE_URL" | sed -e 's|.*/||g')

echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT (User: $DB_USER, DB: $DB_NAME)..."

# Loop until pg_isready reports success
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 1
done

echo "PostgreSQL is up - executing migrations"

# Run Alembic migrations
echo "Running Alembic migrations..."
python -m alembic upgrade head
echo "Alembic migrations completed."

# Start the application
echo "Starting application with Gunicorn..."
exec gunicorn -b 0.0.0.0:8000 "app.main:app"