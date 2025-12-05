import sqlite3
import os
from src.database import get_db_connection
import sys

# Path to local SQLite DB
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, 'database', 'system.db')

def migrate_loans():
    print(f"Connecting to local DB: {SQLITE_DB_PATH}")
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_cursor = sqlite_conn.cursor()

    print("Connecting to Cloud DB...")
    try:
        pg_conn = get_db_connection()
    except Exception as e:
        print(f"Failed to connect to Cloud DB: {e}")
        return

    table_name = 'installments'
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

    columns = [description[0] for description in sqlite_cursor.description]
    print(f"Columns: {columns}")
    print(f"Num Columns: {len(columns)}")
    
    # Debug: Try all columns EXCEPT collateral
    all_cols = [description[0] for description in sqlite_cursor.description]
    target_cols = [c for c in all_cols if 'collateral' not in c]
    
    # Map indices
    col_indices = [all_cols.index(c) for c in target_cols]
    
    quoted_columns = [f'"{col}"' for col in target_cols]
    cols_str = ", ".join(quoted_columns)
    placeholders = ", ".join(["%s"] * len(target_cols))
    query = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"
    
    pg_cursor = pg_conn.cursor()
    count = 0
    for row in rows:
        values = list(row)
        
        # Clean values
        cleaned_values = []
        for val in values:
            if isinstance(val, str) and val.strip() == '':
                cleaned_values.append(None)
            else:
                cleaned_values.append(val)
        values = cleaned_values
        
        # Filter values
        subset_values = [values[i] for i in col_indices]
        
        try:
            conflict_query = f"{query} ON CONFLICT (id) DO NOTHING"
            print(f"Query: {conflict_query}")
            print(f"Values: {subset_values}")
            pg_cursor.execute(conflict_query, subset_values)
            
            pg_conn.commit()
            count += 1
            print(f"Migrated row {subset_values[0]}")
        except Exception as e:
            pg_conn.rollback()
            print(f"Error inserting row {subset_values}: {e}")
            break
            
            pg_conn.commit()
            count += 1
            print(f"Migrated row {values[0]}") # Print ID
        except Exception as e:
            pg_conn.rollback()
            print(f"Error inserting row {values}: {e}")
            # Break on first error to see it
            break
    
    print(f"Migrated {count} rows to {table_name}.")
    sqlite_conn.close()
    pg_conn.close()

if __name__ == "__main__":
    migrate_loans()
