import sys
sys.path.insert(0, 'src')

from database import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

# Add settings for the new "Préstamos" module
settings_to_add = [
    ('mod_loans_visible', '1'),  # Préstamos module visible by default
    ('label_loans', 'Préstamos')  # Label for Préstamos module
]

for key, value in settings_to_add:
    # Check if setting exists
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    existing = cursor.fetchone()
    
    if existing:
        print(f"✓ Configuración '{key}' ya existe con valor: {existing['value']}")
    else:
        cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))
        print(f"✅ Agregada configuración '{key}' = '{value}'")

conn.commit()
conn.close()

print("\n✅ Configuración del módulo Préstamos completada")
