import sqlite3
import os

# Database path
db_path = os.path.join(os.path.dirname(__file__), 'src', 'database', 'system.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Aplicando migraciones...")

# 1. Add payment_method to installments
try:
    cursor.execute("SELECT payment_method FROM installments LIMIT 1")
    print("✓ payment_method ya existe en installments")
except sqlite3.OperationalError:
    cursor.execute("ALTER TABLE installments ADD COLUMN payment_method TEXT DEFAULT 'efectivo'")
    print("✓ Agregada columna payment_method a installments")

# 2. Add analyst_id to clients
try:
    cursor.execute("SELECT analyst_id FROM clients LIMIT 1")
    print("✓ analyst_id ya existe en clients")
except sqlite3.OperationalError:
    cursor.execute("ALTER TABLE clients ADD COLUMN analyst_id INTEGER")
    print("✓ Agregada columna analyst_id a clients")

# 3. Add analyst_id to loans
try:
    cursor.execute("SELECT analyst_id FROM loans LIMIT 1")
    print("✓ analyst_id ya existe en loans")
except sqlite3.OperationalError:
    cursor.execute("ALTER TABLE loans ADD COLUMN analyst_id INTEGER")
    print("✓ Agregada columna analyst_id a loans")

conn.commit()
conn.close()

print("\n✅ Migraciones completadas exitosamente")
