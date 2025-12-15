
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'src'))
from utils.backup_manager import BackupManager

bm = BackupManager()
print("Generating manual backup...")
path = bm.create_excel_backup(trigger='manual')
if path:
    print(f"SUCCESS: Created {os.path.basename(path)}")
else:
    print("FAILURE")
