import sys
sys.path.insert(0, 'src')

from database import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()
cursor.execute('SELECT username, password, role FROM users')
users = cursor.fetchall()

print("Usuarios en la base de datos:")
for user in users:
    print(f"Usuario: {user['username']}, Password: {user['password']}, Rol: {user['role']}")

conn.close()
