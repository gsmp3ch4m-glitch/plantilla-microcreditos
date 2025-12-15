import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'system.db')

def enable_modules():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Enable Documents module
    print("Enabling Documents module...")
    cursor.execute("UPDATE settings SET value = '1' WHERE key = 'mod_docs_visible'")
    
    # Enable Loan modules (just in case they are hidden or user wants all)
    print("Enabling Loan modules...")
    cursor.execute("UPDATE settings SET value = '1' WHERE key = 'mod_loan1_visible'")
    cursor.execute("UPDATE settings SET value = '1' WHERE key = 'mod_loan2_visible'") # Préstamo Bancario
    cursor.execute("UPDATE settings SET value = '1' WHERE key = 'mod_loan3_visible'") # Rapidiario
    
    # Commit changes
    conn.commit()
    conn.close()
    print("Modules enabled successfully.")

if __name__ == "__main__":
    enable_modules()
