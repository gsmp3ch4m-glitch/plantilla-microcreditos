import sys
sys.path.insert(0, 'src')

from database import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

# Update admin password to admin123
cursor.execute("UPDATE users SET password = ? WHERE username = ?", ('admin123', 'admin'))
conn.commit()

print("Contraseña del usuario 'admin' actualizada a 'admin123'")

# Verify
cursor.execute('SELECT username, password FROM users WHERE username = "admin"')
user = cursor.fetchone()
print(f"Verificación - Usuario: {user['username']}, Password: {user['password']}")

conn.close()
