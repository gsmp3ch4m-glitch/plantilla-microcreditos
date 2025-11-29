import sys
sys.path.insert(0, 'src')

from database import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

print("=== USUARIOS EN LA BASE DE DATOS ===")
cursor.execute('SELECT id, username, password, role FROM users ORDER BY id')
users = cursor.fetchall()

for user in users:
    print(f"ID: {user['id']}, Usuario: {user['username']}, Password: {user['password']}, Rol: {user['role']}")

conn.close()
