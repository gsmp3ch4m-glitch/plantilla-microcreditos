import sqlite3
import os
from src.database import get_db_connection
import sys

# Path to local SQLite DB
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, 'database', 'system.db')

def migrate_table(sqlite_cursor, pg_conn, table_name, columns=None):
    print(f"Migrating table: {table_name}...")
    
    # Get data from SQLite
    try:
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"Skipping {table_name}: {e}")
        return

    if not rows:
        print(f"No data in {table_name}.")
        return

    # Get column names if not provided
    if not columns:
        columns = [description[0] for description in sqlite_cursor.description]
    
    # Prepare Postgres Insert
    quoted_columns = [f'"{col}"' for col in columns]
    cols_str = ", ".join(quoted_columns)
    placeholders = ", ".join(["%s"] * len(columns))
    query = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"
    
    # Execute Inserts
    pg_cursor = pg_conn.cursor()
    count = 0
    for row in rows:
        # Convert row to list/tuple
        values = list(row)
        
        # Handle potential data type mismatches
        # Convert empty strings to None for Date/Numeric columns
        # Convert numeric strings to float/int
        cleaned_values = []
        for i, val in enumerate(values):
            if i >= len(columns):
                # Should not happen, but just in case
                cleaned_values.append(val)
                continue
                
            col_name = columns[i]
            if isinstance(val, str) and val.strip() == '':
                cleaned_values.append(None)
                continue
            
            # Numeric conversion
            if val is not None:
                if col_name in ['amount', 'interest_rate', 'original_amount', 'collateral_sale_price', 'frozen_amount', 'admin_fee', 'sales_expense', 'sale_price', 'market_value', 'weight']:
                    try:
                        cleaned_values.append(float(val))
                        continue
                    except:
                        pass
                elif col_name in ['id', 'client_id', 'refinance_count', 'parent_loan_id', 'analyst_id', 'loan_id', 'user_id', 'cash_session_id', 'number']:
                    try:
                        cleaned_values.append(int(val))
                        continue
                    except:
                        pass
            
            cleaned_values.append(val)
        
        values = cleaned_values
        
        try:
            # Use ON CONFLICT DO NOTHING to avoid duplicates if re-running
            # Note: This requires a unique constraint/primary key. 
            # Most tables have 'id' as PK.
            # We'll try simple insert and catch errors or use ON CONFLICT if supported by table
            
            # Construct query with ON CONFLICT for ID
            if 'id' in columns:
                conflict_query = f"{query} ON CONFLICT (id) DO NOTHING"
                pg_cursor.execute(conflict_query, values)
            elif table_name == 'settings':
                 conflict_query = f"{query} ON CONFLICT (key) DO NOTHING"
                 pg_cursor.execute(conflict_query, values)
            else:
                pg_cursor.execute(query, values)
            
            pg_conn.commit()
            count += 1
        except Exception as e:
            pg_conn.rollback()
            print(f"Error inserting row into {table_name}: {e}")
            # import traceback
            # traceback.print_exc()
    
    print(f"Migrated {count} rows to {table_name}.")

    
    # Reset Sequence for ID columns
    if 'id' in columns:
        try:
            pg_cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), COALESCE(MAX(id), 1)) FROM {table_name}")
            pg_conn.commit()
            print(f"Reset sequence for {table_name}.")
        except Exception as e:
            print(f"Could not reset sequence for {table_name}: {e}")

def main():
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"Local database not found at {SQLITE_DB_PATH}")
        return

    print(f"Connecting to local DB: {SQLITE_DB_PATH}")
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_cursor = sqlite_conn.cursor()

    print("Connecting to Cloud DB...")
    try:
        pg_conn = get_db_connection()
    except Exception as e:
        print(f"Failed to connect to Cloud DB: {e}")
        return

    # Order matters due to Foreign Keys
    tables = [
        'users',
        'clients',
        'loans',
        'pawn_details',
        'cash_sessions',
        'transactions',
        'installments',
        'settings',
        'audit_logs'
    ]

    for table in tables:
        print(f"Processing {table}...")
        # Get columns from SQLite
        try:
            sqlite_cursor.execute(f"SELECT * FROM {table} LIMIT 0")
            all_cols = [description[0] for description in sqlite_cursor.description]
        except Exception as e:
            print(f"Error getting columns for {table}: {e}")
            continue

        # Filter columns
        if table == 'loans':
            exclude = ['collateral', 'collateral_sale_price']
            target_cols = [c for c in all_cols if c not in exclude]
        else:
            target_cols = all_cols
            
        # Select ONLY target columns
        # Quote all columns to be safe
        quoted_target_cols_select = [f'"{c}"' for c in target_cols]
        cols_select = ", ".join(quoted_target_cols_select)
        
        try:
            sqlite_cursor.execute(f"SELECT {cols_select} FROM {table}")
        except Exception as e:
            print(f"Error selecting data from {table}: {e}")
            continue

        # Migrate
        migrate_table(sqlite_cursor, pg_conn, table, columns=target_cols)
        
        # Post-migration updates
        if table == 'loans':
             # Update collateral separately if columns exist
            if 'collateral' in all_cols and 'collateral_sale_price' in all_cols:
                print("Updating collateral for loans...")
                sqlite_cursor.execute(f"SELECT id, collateral, collateral_sale_price FROM {table}")
                rows = sqlite_cursor.fetchall()
                pg_cursor = pg_conn.cursor()
                for row in rows:
                    try:
                        # Clean values
                        collateral = row[1]
                        sale_price = row[2]
                        if isinstance(collateral, str) and collateral.strip() == '': collateral = None
                        if isinstance(sale_price, str) and sale_price == '': sale_price = None
                        
                        pg_cursor.execute('UPDATE loans SET "collateral" = %s, "collateral_sale_price" = %s WHERE id = %s', (collateral, sale_price, row[0]))
                        pg_conn.commit()
                    except Exception as e:
                        print(f"Error updating collateral for loan {row[0]}: {e}")

    sqlite_conn.close()
    pg_conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    main()
