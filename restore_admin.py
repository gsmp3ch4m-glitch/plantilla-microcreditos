import sys
sys.path.insert(0, 'src')

from database import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

# Restore admin password to admin123
cursor.execute("UPDATE users SET password = ? WHERE username = ?", ('admin123', 'admin'))
conn.commit()

print("✅ Contraseña del usuario 'admin' restaurada a 'admin123'")

# Verify all users
cursor.execute('SELECT id, username, password FROM users ORDER BY id')
users = cursor.fetchall()

print("\n=== USUARIOS ACTUALIZADOS ===")
for user in users:
    print(f"ID: {user['id']}, Usuario: {user['username']}, Password: {user['password']}")

conn.close()
