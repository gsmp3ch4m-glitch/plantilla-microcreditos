import os
from dotenv import load_dotenv

load_dotenv()

import json

# Load secrets from local file if exists
SECRETS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'secrets.json')

if os.path.exists(SECRETS_FILE):
    with open(SECRETS_FILE, 'r') as f:
        secrets = json.load(f)
    SUPABASE_URL = secrets.get('SUPABASE_URL')
    SUPABASE_KEY = secrets.get('SUPABASE_KEY')
    DB_URI = secrets.get('DB_URI')
else:
    # Fallback or Environment Variables
    SUPABASE_URL = os.getenv("SUPABASE_URL", "https://jgmqmvfdetyxibzeleuz.supabase.co")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpnbXFtdmZkZXR5eGliemVsZXV6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ2NjY5NDQsImV4cCI6MjA4MDI0Mjk0NH0.3PsEEOgl4oOWZyG--GWE1mW9pPAkddW37Vzt2nQSqyM")
    DB_URI = os.getenv("DB_URI", "postgresql://postgres:X03T25mqUB9ZmL8Q@db.jgmqmvfdetyxibzeleuz.supabase.co:5432/postgres")

# Image Compression Settings
MAX_IMAGE_SIZE = (1024, 1024)  # Max width/height
IMAGE_QUALITY = 80             # JPEG Quality
