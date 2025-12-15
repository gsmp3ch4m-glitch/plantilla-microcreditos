import shutil
import os
from datetime import datetime
import threading
from database import DB_PATH

class BackupManager:
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.local_backup_dir = os.path.join(self.project_root, 'backups', 'local')
        # Default cloud path (OneDrive) - Try to detect or use a standard path
        # User path: c:\Users\pecha\OneDrive\Escritorio\google antigravity\plantilla casa de empeño y microcreditos
        # We can try to find a "Backups" folder in the project root if it's already in OneDrive
        self.cloud_backup_dir = os.path.join(self.project_root, 'backups', 'cloud') 
        
        self._ensure_dirs()

    def _ensure_dirs(self):
        os.makedirs(self.local_backup_dir, exist_ok=True)
        os.makedirs(self.cloud_backup_dir, exist_ok=True)

    def create_backup(self, trigger='manual', run_async=True):
        """
        Creates a backup of the database (JSON dump for Postgres).
        trigger: 'manual', 'auto', 'close'
        """
        def _backup_thread():
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"backup_{trigger}_{timestamp}.json"
                
                # Fetch all data
                from database import get_db_connection
                conn = get_db_connection()
                # conn.row_factory is already set in get_db_connection
                cursor = conn.cursor()
                
                tables = ['users', 'clients', 'loans', 'pawn_details', 'transactions', 'cash_sessions', 'installments', 'settings', 'audit_logs']
                backup_data = {}
                
                for table in tables:
                    try:
                        cursor.execute(f"SELECT * FROM {table}")
                        rows = cursor.fetchall()
                        # Convert rows to list of dicts (already dicts due to row_factory)
                        # Handle datetime serialization
                        serialized_rows = []
                        for row in rows:
                            new_row = {}
                            # Convert sqlite3.Row to dict to use .items()
                            row_dict = dict(row)
                            for k, v in row_dict.items():
                                if isinstance(v, datetime):
                                    new_row[k] = v.isoformat()
                                elif hasattr(v, 'isoformat'): # date
                                    new_row[k] = v.isoformat()
                                else:
                                    new_row[k] = v
                            serialized_rows.append(new_row)
                        backup_data[table] = serialized_rows
                    except Exception as e:
                        print(f"Error backing up table {table}: {e}")
                        with open("restore_debug.log", "a", encoding="utf-8") as dlog:
                            dlog.write(f"ERROR: Error backing up table {table}: {e}\n")
                
                conn.close()
                
                # Save to JSON
                import json
                local_path = os.path.join(self.local_backup_dir, filename)
                with open(local_path, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)
                
                print(f"Local backup created: {local_path}")
                
                # Cloud Backup (Copy to cloud folder)
                cloud_path = os.path.join(self.cloud_backup_dir, filename)
                shutil.copy2(local_path, cloud_path)
                print(f"Cloud backup created: {cloud_path}")
                
                # Update last backup time
                self._update_last_backup_time()
                
                # Cleanup old backups (keep last 30)
                self._cleanup_old_backups(self.local_backup_dir, extension='.json')
                self._cleanup_old_backups(self.cloud_backup_dir, extension='.json')
                
            except Exception as e:
                print(f"Error creating backup: {e}")
                import traceback
                traceback.print_exc()

        if run_async:
            # Run in separate thread to not block UI
            threading.Thread(target=_backup_thread, daemon=True).start()
        else:
            _backup_thread()

    def _update_last_backup_time(self):
        try:
            log_path = os.path.join(self.local_backup_dir, 'last_backup.txt')
            with open(log_path, 'w') as f:
                f.write(datetime.now().isoformat())
        except Exception as e:
            print(f"Error updating last backup time: {e}")

    def check_and_run_auto_backup(self):
        """Checks if backup is needed (every 3 days) and runs it."""
        try:
            log_path = os.path.join(self.local_backup_dir, 'last_backup.txt')
            if not os.path.exists(log_path):
                # First run or no backup yet
                self.create_backup(trigger='auto')
                return

            with open(log_path, 'r') as f:
                last_backup_str = f.read().strip()
            
            last_backup = datetime.fromisoformat(last_backup_str)
            days_diff = (datetime.now() - last_backup).days
            
            if days_diff >= 3:
                print(f"Last backup was {days_diff} days ago. Running auto backup...")
                self.create_backup(trigger='auto')
            else:
                print(f"Last backup was {days_diff} days ago. Skipping.")
                
        except Exception as e:
            print(f"Error checking auto backup: {e}")
            # Fallback: try to backup if check fails
            self.create_backup(trigger='auto')

    def get_available_backups(self):
        """Returns a list of available backup files in the local backup directory."""
        try:
            files = sorted(
                [f for f in os.listdir(self.local_backup_dir) if f.endswith('.db') or f.endswith('.json') or f.endswith('.xlsx')],
                key=lambda x: os.path.getmtime(os.path.join(self.local_backup_dir, x)),
                reverse=True
            )
            return files
        except Exception as e:
            print(f"Error listing backups: {e}")
            return []

    def restore_database(self, backup_filename):
        """
        Restores the database from a backup file (.db, .json, or .xlsx).
        """
        try:
            if os.path.isabs(backup_filename):
                source_path = backup_filename
            else:
                source_path = os.path.join(self.local_backup_dir, backup_filename)
            
            if not os.path.exists(source_path):
                raise FileNotFoundError(f"Backup file not found: {source_path}")

            if source_path.endswith('.json'):
                return self.restore_from_json(source_path)
            elif source_path.endswith('.xlsx'):
                return self.restore_from_excel(source_path)
            else:
                # Default .db restore
                shutil.copy2(source_path, DB_PATH)
                print(f"Database restored from: {source_path}")
                return True
        except Exception as e:
            print(f"Error restoring database: {e}")
            return False

    def restore_from_json(self, json_path):
        import json
        from database import get_db_connection
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Disable FKs
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            # Wipe and Load
            tables = data.keys()
            print(f"DEBUG: Restoring tables: {list(tables)}") 
            for table in tables:
                with open("restore_debug.log", "a", encoding="utf-8") as dlog:
                    dlog.write(f"DEBUG: Processing table {table}\n")
                
                cursor.execute(f"DELETE FROM {table}")
                rows = data[table]
                
                with open("restore_debug.log", "a", encoding="utf-8") as dlog:
                    dlog.write(f"DEBUG: Table {table} has {len(rows)} rows to insert\n")
                
                if not rows: continue
                
                cols = rows[0].keys()
                placeholders = ', '.join(['?'] * len(cols))
                col_names = ', '.join(cols)
                
                query = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
                
                values = []
                for row in rows:
                    values.append([row[c] for c in cols])
                    
                cursor.executemany(query, values)
                
                with open("restore_debug.log", "a", encoding="utf-8") as dlog:
                    dlog.write(f"DEBUG: Inserted {len(values)} rows into {table}\n")

                
            conn.commit()
            cursor.execute("PRAGMA foreign_keys = ON")
            conn.close()
            print(f"Restored from JSON: {json_path}")
            return True
        except Exception as e:
            print(f"JSON Restore Error: {e}")
            return False

    def create_excel_backup(self, trigger='manual'):
        import pandas as pd
        from database import get_db_connection
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"backup_{trigger}_{timestamp}.xlsx"
            local_path = os.path.join(self.local_backup_dir, filename)
            
            conn = get_db_connection()
            
            # Get all tables
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cursor.fetchall() if r[0] not in ('sqlite_sequence',)]
            
            with pd.ExcelWriter(local_path, engine='openpyxl') as writer:
                for table in tables:
                    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                    df.to_excel(writer, sheet_name=table, index=False)
            
            conn.close()
            print(f"Excel backup created: {local_path}")
            
            self._update_last_backup_time()
            self._cleanup_old_backups(self.local_backup_dir, extension='.xlsx')
            return local_path
        except Exception as e:
            print(f"Excel Backup Error: {e}")
            import traceback
            error_msg = traceback.format_exc()
            traceback.print_exc()
            
            # Log to file for debugging
            try:
                with open(os.path.join(self.local_backup_dir, "backup_error.log"), "w") as f:
                    f.write(f"Timestamp: {datetime.now()}\n")
                    f.write(error_msg)
            except:
                pass
                
            return None

    def restore_from_excel(self, excel_path):
        import pandas as pd
        from database import get_db_connection
        
        try:
            # Read all sheets
            dfs = pd.read_excel(excel_path, sheet_name=None)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            for table_name, df in dfs.items():
                try:
                    # Clean table
                    cursor.execute(f"DELETE FROM {table_name}")
                    
                    # Insert data
                    # df.to_sql is easier but might fail on schema mismatch or if table missing.
                    # We assume tables exist.
                    # Standard pandas to_sql append:
                    df.to_sql(table_name, conn, if_exists='append', index=False)
                    
                except Exception as table_err:
                    print(f"Error restoring table {table_name}: {table_err}")
            
            conn.commit()
            cursor.execute("PRAGMA foreign_keys = ON")
            conn.close()
            print(f"Restored from Excel: {excel_path}")
            return True
        except Exception as e:
            print(f"Excel Restore Error: {e}")
            return False

    def reset_database(self):
        """
        Resets the database by deleting the file and re-initializing it.
        """
        try:
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
                print(f"Database file deleted: {DB_PATH}")
            
            # Re-initialize
            from database import init_db
            init_db()
            print("Database re-initialized.")
            return True
        except Exception as e:
            print(f"Error resetting database: {e}")
            return False

    def _cleanup_old_backups(self, directory, keep=30, extension='.db'):
        try:
            files = sorted(
                [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(extension) or f.endswith('.json')],
                key=os.path.getmtime
            )
            if len(files) > keep:
                for f in files[:-keep]:
                    os.remove(f)
                    print(f"Removed old backup: {f}")
        except Exception as e:
            print(f"Error cleaning up backups: {e}")
