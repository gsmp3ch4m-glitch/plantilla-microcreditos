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
        Creates a backup of the database (JSON dump for Postgres and Excel for users).
        trigger: 'manual', 'auto', 'close'
        """
        def _backup_thread():
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename_json = f"backup_{trigger}_{timestamp}.json"
                
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
                
                conn.close()
                
                # Save to JSON
                import json
                local_path_json = os.path.join(self.local_backup_dir, filename_json)
                with open(local_path_json, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)
                
                print(f"Local JSON backup created: {local_path_json}")
                
                # Cloud Backup JSON
                cloud_path_json = os.path.join(self.cloud_backup_dir, filename_json)
                shutil.copy2(local_path_json, cloud_path_json)
                print(f"Cloud JSON backup created: {cloud_path_json}")

                # --- EXCEL BACKUP ---
                # Generate Excel Backup (Synchronously within this thread)
                # create_excel_backup usually returns the path
                local_path_excel = self.create_excel_backup(trigger=trigger)
                
                if local_path_excel and os.path.exists(local_path_excel):
                    filename_excel = os.path.basename(local_path_excel)
                    cloud_path_excel = os.path.join(self.cloud_backup_dir, filename_excel)
                    shutil.copy2(local_path_excel, cloud_path_excel)
                    print(f"Cloud Excel backup created: {cloud_path_excel}")
                
                # Update last backup time
                self._update_last_backup_time()
                
                # Cleanup old backups (keep last 30)
                self._cleanup_old_backups(self.local_backup_dir, extension='.json')
                self._cleanup_old_backups(self.cloud_backup_dir, extension='.json')
                self._cleanup_old_backups(self.local_backup_dir, extension='.xlsx')
                self._cleanup_old_backups(self.cloud_backup_dir, extension='.xlsx')
                
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
        Returns: (success, message)
        """
        try:
            if os.path.isabs(backup_filename):
                source_path = backup_filename
            else:
                source_path = os.path.join(self.local_backup_dir, backup_filename)
            
            if not os.path.exists(source_path):
                return False, f"Archivo no encontrado: {source_path}"

            if source_path.endswith('.json'):
                return self.restore_from_json(source_path)
            elif source_path.endswith('.xlsx'):
                return self.restore_from_excel(source_path)
            else:
                # Default .db restore
                shutil.copy2(source_path, DB_PATH)
                print(f"Database restored from: {source_path}")
                return True, "Restauración exitosa desde DB."
        except Exception as e:
            print(f"Error restoring database: {e}")
            return False, str(e)

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
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
                rows = data[table]
                
                if not rows: continue
                
                cols = rows[0].keys()
                placeholders = ', '.join(['?'] * len(cols))
                col_names = ', '.join(cols)
                
                query = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
                
                values = []
                for row in rows:
                    values.append([row[c] for c in cols])
                    
                cursor.executemany(query, values)
                
            conn.commit()
            cursor.execute("PRAGMA foreign_keys = ON")
            conn.close()
            print(f"Restored from JSON: {json_path}")
            return True, "Restauración exitosa desde JSON."
        except Exception as e:
            print(f"JSON Restore Error: {e}")
            return False, f"Error JSON: {str(e)}"

    def create_excel_backup(self, trigger='manual'):
        import pandas as pd
        from database import get_db_connection
        
        try:
            # Format: Copia de Seguridad El Canguro v2.1 [YYYY-MM-DD] [HH-MM-SS].xlsx
            version = "v2.1"
            date_str = datetime.now().strftime("[%Y-%m-%d] [%H-%M-%S]")
            filename = f"Copia de Seguridad El Canguro {version} {date_str}.xlsx"
            local_path = os.path.join(self.local_backup_dir, filename)
            
            conn = get_db_connection()
            
            # Spanish Translations
            table_map = {
                'clients': 'Clientes',
                'loans': 'Préstamos',
                'installments': 'Cuotas',
                'transactions': 'Transacciones',
                'calc_history': 'Historial Calculadora', # if exists
                'cash_sessions': 'Sesiones de Caja',
                'pawn_details': 'Detalles de Empeño',
                'users': 'Usuarios',
                'settings': 'Configuración',
                'audit_logs': 'Registros Auditoría',
                'manual_receivables': 'Deudas Manuales',
                'notifications': 'Notificaciones'
            }
            
            col_map = {
                'id': 'ID',
                'dni': 'DNI',
                'first_name': 'Nombres',
                'last_name': 'Apellidos',
                'phone': 'Teléfono',
                'address': 'Dirección',
                'email': 'Email',
                'client_id': 'ID Cliente',
                'loan_type': 'Tipo Préstamo',
                'amount': 'Monto',
                'interest_rate': 'Tasa Interés',
                'start_date': 'Fecha Inicio',
                'due_date': 'Fecha Vencimiento',
                'status': 'Estado',
                'loan_id': 'ID Préstamo',
                'number': 'Número Cuota',
                'paid_amount': 'Monto Pagado',
                'payment_date': 'Fecha Pago',
                'type': 'Tipo',
                'category': 'Categoría',
                'description': 'Descripción',
                'user_id': 'ID Usuario',
                'username': 'Usuario',
                'full_name': 'Nombre Completo',
                'role': 'Rol',
                'key': 'Clave',
                'value': 'Valor',
                'action': 'Acción',
                'details': 'Detalles',
                'timestamp': 'Fecha/Hora',
                'item_type': 'Tipo Bien',
                'brand': 'Marca',
                'market_value': 'Valor Mercado',
                'condition': 'Condición',
                'characteristics': 'Características',
                'opening_balance': 'Saldo Inicial',
                'closing_balance': 'Saldo Final',
                'opening_date': 'Fecha Apertura',
                'closing_date': 'Fecha Cierre'
            }
            
            # Get all tables
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cursor.fetchall() if r[0] not in ('sqlite_sequence',)]
            
            with pd.ExcelWriter(local_path, engine='openpyxl') as writer:
                for table in tables:
                    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                    
                    # Rename Columns
                    df.rename(columns=col_map, inplace=True)
                    
                    # Rename Sheet
                    sheet_name = table_map.get(table, table)
                    
                    # Truncate sheet name to 31 chars (Excel limit)
                    sheet_name = sheet_name[:31]
                    
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
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
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Read all sheets first
            dfs = pd.read_excel(excel_path, sheet_name=None)
            
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            # Custom method for INSERT OR REPLACE
            def insert_on_conflict_replace(table, conn, keys, data_iter):
                # table is a pandas.io.sql.SQLTable
                # conn is the sqlite3 connection
                columns = ', '.join(f'"{k}"' for k in keys)
                placeholders = ', '.join('?' for _ in keys)
                sql = f'INSERT OR REPLACE INTO "{table.name}" ({columns}) VALUES ({placeholders})'
                conn.executemany(sql, data_iter)

            for table_name, df in dfs.items():
                # Clean table
                cursor.execute(f"DELETE FROM {table_name}")
                
                # Check if dataframe is empty
                if df.empty:
                    continue

                # Insert data using custom method
                df.to_sql(table_name, conn, if_exists='append', index=False, method=insert_on_conflict_replace)
            
            conn.commit()
            cursor.execute("PRAGMA foreign_keys = ON")
            conn.close()
            
            print(f"Restored from Excel: {excel_path}")
            return True, "Restauración exitosa desde Excel."
            
        except Exception as e:
            conn.rollback() # Rollback changes if any error occurs
            conn.close()
            print(f"Excel Restore Error: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Error Excel: {str(e)}"

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
