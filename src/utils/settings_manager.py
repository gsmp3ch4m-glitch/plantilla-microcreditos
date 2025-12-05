from database import get_db_connection

def get_setting(key):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row['value'] if row else None

def get_all_settings():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM settings")
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_setting(key, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if key exists
    cursor.execute("SELECT 1 FROM settings WHERE key = ?", (key,))
    exists = cursor.fetchone()
    
    if exists:
        cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))
    else:
        cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))
        
    conn.commit()
    conn.close()
