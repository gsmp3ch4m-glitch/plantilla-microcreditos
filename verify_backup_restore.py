
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
        # Backup existing DB
        if os.path.exists(DB_PATH):
            shutil.copy2(DB_PATH, DB_PATH + ".bak_test")
        
        # Init fresh DB
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()
        
        # Insert some test data
        conn = get_db_connection()
        conn.execute("INSERT INTO settings (key, value) VALUES ('test_key', 'test_value')")
        conn.commit()
        conn.close()
        
        self.bm = BackupManager()

    def tearDown(self):
        # Restore original DB
        if os.path.exists(DB_PATH + ".bak_test"):
            shutil.copy2(DB_PATH + ".bak_test", DB_PATH)
            os.remove(DB_PATH + ".bak_test")

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
        success = self.bm.restore_database(backup_file)
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
        success = self.bm.restore_database(os.path.basename(backup_path))
        
        if not success:
            print("Excel restore failed. Checking possible reasons...")
            # Check if pandas supports sqlite3 connection
            try:
                import pandas as pd
                print(f"Pandas version: {pd.__version__}")
            except ImportError:
                print("Pandas not installed.")
        
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

