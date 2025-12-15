
import os
import sys
import unittest
import shutil
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.backup_manager import BackupManager
from database import get_db_connection, init_db, DB_PATH

class TestBackupRestore(unittest.TestCase):
    def setUp(self):
        # Use a separate test database file
        import database
        self.original_db_path = database.DB_PATH
        self.test_db_path = os.path.join(os.path.dirname(database.DB_PATH), 'test_system.db')
        database.DB_PATH = self.test_db_path
        
        # Init fresh DB
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except:
                pass # Best effort
                
        init_db()
        
        # Insert some test data
        conn = get_db_connection()
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('test_key', 'test_value')")
        conn.commit()
        conn.close()
        
        self.bm = BackupManager()

    def tearDown(self):
        # Restore original DB path
        import database
        database.DB_PATH = self.original_db_path
        
        # Remove test DB
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except:
                pass

    def test_json_backup_restore(self):
        print("\nTesting JSON Backup & Restore...")
        # Create Backup
        self.bm.create_backup(trigger='test', run_async=False)
        backups = self.bm.get_available_backups()
        json_backups = [b for b in backups if b.endswith('.json') and 'test' in b]
        self.assertTrue(len(json_backups) > 0)
        backup_file = json_backups[0]
        print(f"Created JSON backup: {backup_file}")
        
        # Modify DB
        conn = get_db_connection()
        conn.execute("UPDATE settings SET value = 'modified' WHERE key = 'test_key'")
        conn.commit()
        conn.close()
        
        # Restore
        print(f"Restoring from {backup_file}...")
        success, message = self.bm.restore_database(backup_file)
        print(f"Restore Result: {success}, Message: {message}")
        
        self.assertTrue(success)
        
        # Verify
        conn = get_db_connection()
        row = conn.execute("SELECT value FROM settings WHERE key = 'test_key'").fetchone()
        conn.close()
        self.assertEqual(row['value'], 'test_value')
        print("JSON Restore Verified.")

    def test_excel_backup_restore(self):
        print("\nTesting Excel Backup & Restore...")
        # Create Backup
        backup_path = self.bm.create_excel_backup(trigger='test')
        self.assertIsNotNone(backup_path)
        print(f"Created Excel backup: {backup_path}")
        
        # Modify DB
        conn = get_db_connection()
        conn.execute("UPDATE settings SET value = 'modified_excel' WHERE key = 'test_key'")
        conn.commit()
        conn.close()
        
        # Restore
        print(f"Restoring from {os.path.basename(backup_path)}...")
        success, message = self.bm.restore_database(os.path.basename(backup_path))
        print(f"Restore Result: {success}, Message: {message}")
        
        if not success:
            print(f"Excel restore failed: {message}")
        
        self.assertTrue(success)
        
        # Verify
        conn = get_db_connection()
        row = conn.execute("SELECT value FROM settings WHERE key = 'test_key'").fetchone()
        conn.close()
        self.assertEqual(row['value'], 'test_value')
        print("Excel Restore Verified.")

if __name__ == '__main__':
    with open('results.txt', 'w', encoding='utf-8') as f:
        runner = unittest.TextTestRunner(stream=f, verbosity=2)
        unittest.main(testRunner=runner, exit=False)
