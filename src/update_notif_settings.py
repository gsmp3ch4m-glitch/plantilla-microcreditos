import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'system.db')

def update_settings():
    print(f"Updating database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    settings_to_add = [
        ('mod_notif_visible', '1', 'Visible Notificaciones'),
        ('label_notif', 'Notificaciones', 'Etiqueta Notificaciones')
    ]
    
    for key, val, desc in settings_to_add:
        try:
            cursor.execute('INSERT INTO settings (key, value, description) VALUES (?, ?, ?)', (key, val, desc))
            print(f"Added setting: {key}")
        except sqlite3.IntegrityError:
            print(f"Setting {key} already exists. Updating value to ensure visibility...")
            cursor.execute('UPDATE settings SET value = ? WHERE key = ?', (val, key))
            
    conn.commit()
    conn.close()
    print("Database updated successfully.")

if __name__ == "__main__":
    update_settings()
