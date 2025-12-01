"""
Script para actualizar préstamos antiguos con el analyst_id del cliente
"""
import sqlite3
import os

# Get database path
db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'database.db')

def update_loans_with_analyst():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all loans without analyst_id
    cursor.execute("SELECT id, client_id FROM loans WHERE analyst_id IS NULL")
    loans = cursor.fetchall()
    
    updated_count = 0
    for loan in loans:
        # Get analyst_id from client
        cursor.execute("SELECT analyst_id FROM clients WHERE id = ?", (loan['client_id'],))
        client = cursor.fetchone()
        
        if client and client['analyst_id']:
            # Update loan with client's analyst_id
            cursor.execute("UPDATE loans SET analyst_id = ? WHERE id = ?", 
                          (client['analyst_id'], loan['id']))
            updated_count += 1
            print(f"✓ Préstamo #{loan['id']} actualizado con analista ID {client['analyst_id']}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Total de préstamos actualizados: {updated_count}")
    if updated_count == 0:
        print("ℹ️ No hay préstamos antiguos para actualizar")

if __name__ == "__main__":
    print("Actualizando préstamos antiguos con información de analista...\n")
    update_loans_with_analyst()
    print("\n¡Listo! Ahora los cronogramas mostrarán la información del analista.")
