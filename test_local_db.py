import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from src.database import init_db
    print("Attempting to initialize local database...")
    init_db()
    print("SUCCESS: Local database initialized correctly.")
except Exception as e:
    print(f"FAILURE: Could not initialize local database. Error: {e}")
    import traceback
    traceback.print_exc()
