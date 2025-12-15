import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'system.db')

def fix_module_settings():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Fixing module settings...")
    
    # fix 1: mod_loans_visible (used in main_window.py but missing in db defaults)
    cursor.execute("INSERT OR REPLACE INTO settings (key, value, description) VALUES (?, ?, ?)", 
                   ('mod_loans_visible', '1', 'Visible Módulo Préstamos Unificado'))
    
    # fix 2: ensure Documents is visible (already done, but good to double check)
    cursor.execute("UPDATE settings SET value = '1' WHERE key = 'mod_docs_visible'")

    # Extra: Ensure label exists if needed
    cursor.execute("INSERT OR IGNORE INTO settings (key, value, description) VALUES (?, ?, ?)", 
                   ('label_loans', 'Préstamos', 'Etiqueta Módulo Préstamos'))

    conn.commit()
    conn.close()
    print("Settings fixed successfully.")

if __name__ == "__main__":
    fix_module_settings()
