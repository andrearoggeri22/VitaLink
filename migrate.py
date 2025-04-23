import os
from flask_migrate import Migrate, current
from app import app, db

def run_migration():
    """
    Run database migration to add new columns to the Patient model
    and create the new HealthPlatformLink table
    """
    # Create migrations directory if it doesn't exist
    if not os.path.exists('migrations'):
        print("Initializing migrations directory...")
        with app.app_context():
            # Initialize migrations directory
            os.system("flask db init")
    
    with app.app_context():
        # Create a migration
        print("Creating migration...")
        os.system("flask db migrate -m 'Add health platform integration'")
        
        # Apply the migration
        print("Applying migration...")
        os.system("flask db upgrade")
        
        print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration()