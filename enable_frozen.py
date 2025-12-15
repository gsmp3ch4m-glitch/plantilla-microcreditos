import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'system.db')

def enable_frozen_loans():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Enabling Frozen Loans module...")
    
    # 1. Enable mod_loan4_visible (Frozen Loans)
    cursor.execute("UPDATE settings SET value = '1' WHERE key = 'mod_loan4_visible'")

    # 2. Ensure proper label
    cursor.execute("INSERT OR REPLACE INTO settings (key, value, description) VALUES (?, ?, ?)", 
                   ('label_loan4', 'Préstamos Congelados', 'Etiqueta Préstamo 4 (Congelados)'))

    # 3. Enable Permissions for everyone for testing (or just update the default 'all' permission)
    # The code checks permissions based on 'all' or specific module name.
    # 'Congelado' isn't explicitly in the default permission lists in main_window.py (referenced as "Préstamos" now),
    # but the sub-menu depends on settings mainly.
    
    conn.commit()
    conn.close()
    print("Frozen Loans enabled successfully.")

if __name__ == "__main__":
    enable_frozen_loans()
