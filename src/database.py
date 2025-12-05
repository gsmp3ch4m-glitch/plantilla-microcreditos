import os
import json
import sys

# Determine mode from secrets.json
SECRETS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'secrets.json')
MODE = 'LOCAL' # Default

if os.path.exists(SECRETS_FILE):
    try:
        with open(SECRETS_FILE, 'r') as f:
            secrets = json.load(f)
            MODE = secrets.get('MODE', 'LOCAL')
    except Exception as e:
        print(f"Error reading secrets.json: {e}")

# Import appropriate implementation
if MODE == 'CLOUD':
    print("Loading Cloud Database (PostgreSQL)...")
    try:
        from src.database_postgres import *
    except ImportError:
        from database_postgres import *
else:
    print("Loading Local Database (SQLite)...")
    try:
        from src.database_sqlite import *
    except ImportError:
        # Fallback if running from src directory directly
        from database_sqlite import *

if __name__ == '__main__':
    init_db()
