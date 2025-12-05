from src.database import get_db_connection

def check_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
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
        
        print("Cloud Database Row Counts:")
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()
                # Handle dictionary row or tuple
                if isinstance(count, dict):
                    val = list(count.values())[0]
                else:
                    val = count[0]
                print(f"{table}: {val}")
            except Exception as e:
                print(f"{table}: Error - {e}")
                
        conn.close()
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    check_data()
