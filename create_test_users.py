"""
Script para crear usuarios de prueba con diferentes roles
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import get_db_connection

def create_test_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Usuarios de prueba
    test_users = [
        ('admin', 'admin123', 'admin', 'Administrador del Sistema'),
        ('cajero', 'caja123', 'caja', 'Usuario Cajero'),
        ('analista', 'analista123', 'analista', 'Usuario Analista'),
    ]
    
    for username, password, role, full_name in test_users:
        try:
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            existing = cursor.fetchone()
            
            if existing:
                # Update role and permissions
                cursor.execute("""
                    UPDATE users 
                    SET role = ?, full_name = ?, permissions = ?
                    WHERE username = ?
                """, (role, full_name, 'all' if role == 'admin' else role, username))
                print(f"✓ Usuario actualizado: {username} (rol: {role})")
            else:
                # Create new user
                cursor.execute("""
                    INSERT INTO users (username, password, role, full_name, permissions)
                    VALUES (?, ?, ?, ?, ?)
                """, (username, password, role, full_name, 'all' if role == 'admin' else role))
                print(f"✓ Usuario creado: {username} (rol: {role})")
        except Exception as e:
            print(f"✗ Error con {username}: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*60)
    print("USUARIOS DE PRUEBA CONFIGURADOS")
    print("="*60)
    print("\n1. ADMIN (Acceso Total)")
    print("   Usuario: admin")
    print("   Contraseña: admin123")
    print("   Permisos: Todos los módulos")
    
    print("\n2. CAJERO (Rol: caja)")
    print("   Usuario: cajero")
    print("   Contraseña: caja123")
    print("   Permisos: Caja, Clientes, Calculadora, Documentos")
    
    print("\n3. ANALISTA (Rol: analista)")
    print("   Usuario: analista")
    print("   Contraseña: analista123")
    print("   Permisos: Préstamos, Clientes, Calculadora, Documentos")
    print("="*60)

if __name__ == '__main__':
    create_test_users()
