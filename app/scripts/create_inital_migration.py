#!/bin/bash

# Create Initial Migration for Crisis Simulator
# This script creates an Alembic migration with all tables

echo "🔨 Creating initial Alembic migration..."

# Make sure we're in the project root
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Create the migration
alembic revision --autogenerate -m "Initial migration with all tables including crisis simulator"

echo "✅ Migration created!"
echo "📝 Check the alembic/versions/ directory for the new migration file"
echo "🚀 Next step: Run 'alembic upgrade head' to apply the migration"