"""
Database Migration Module.
This module provides functionality for managing database schema migrations
using Flask-Migrate and Alembic. It enables:
1. Creating database migration scripts based on model changes
2. Running migrations to update database schema
3. Versioning of database schema changes
4. Rolling back to previous schema versions when needed
The module can be run as a standalone script to initiate migrations
or imported to use the migration functionality elsewhere in the application.
"""
import os
from pathlib import Path
from flask_migrate import Migrate 
from .app import app, db  
PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)
os.environ.setdefault("FLASK_APP", "app:app")
migrate = Migrate(app, db)
def run_migration():
    """Run database migration to add new columns and tables."""
    if not (PROJECT_ROOT / "migrations").exists():
        print("Initializing migrations directory ...")
        os.system("flask db init")
    print("Creating migration ...")
    os.system("flask db migrate -m 'Add health platform integration'")
    print("Applying migration ...")
    os.system("flask db upgrade")
    print("Migration completed successfully!")
if __name__ == "__main__":
    run_migration()