#!/bin/bash
echo "Starting VendorBridge Backend..."
echo "PORT: ${PORT:-8000}"
echo "DATABASE_URL is set: $(if [ -n "$DATABASE_URL" ]; then echo yes; else echo NO; fi)"

# Create database tables
python -c "
from app.db.base import Base
from app.db.session import engine
from app.models import *
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
" || echo "Warning: Table creation failed (tables may already exist)"

# Start the server
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
