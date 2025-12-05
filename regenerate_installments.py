import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from database import get_db_connection
from utils.loan_calculator import obtener_info_prestamo
from datetime import datetime

def regenerate_installments():
    conn = get_db_connection()
    conn.row_factory = True # Enable dict-like access
    cursor = conn.cursor()
    
    print("Checking for loans without installments...")
    
    # Get loans that have 0 installments
    cursor.execute("""
        SELECT l.id, l.loan_type, l.amount, l.interest_rate, l.start_date
        FROM loans l
        LEFT JOIN installments i ON l.id = i.loan_id
        GROUP BY l.id
        HAVING count(i.id) = 0
    """)
    
    loans_to_fix = cursor.fetchall()
    print(f"Found {len(loans_to_fix)} loans to fix.")
    
    for loan in loans_to_fix:
        try:
            print(f"Fixing Loan #{loan['id']} ({loan['loan_type']})...")
            
            # Prepare arguments for calculator
            kwargs = {}
            if loan['loan_type'] == 'rapidiario':
                kwargs['frecuencia'] = 'Diario' # Default fallback
            elif loan['loan_type'] == 'bancario':
                kwargs['meses'] = 3 # Default fallback
            
            # Calculate
            start_date = loan['start_date']
            if start_date is None:
                print(f"  -> Warning: Loan {loan['id']} has no start_date. Defaulting to today.")
                start_date = datetime.now().date()
            elif isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            
            loan_info = obtener_info_prestamo(
                loan['loan_type'],
                loan['amount'] or 0.0,
                loan['interest_rate'] or 0.0,
                start_date,
                **kwargs
            )
            
            # Insert installments
            count = 0
            for num, due, amt in loan_info['cuotas']:
                cursor.execute("""
                    INSERT INTO installments (loan_id, number, due_date, amount, status)
                    VALUES (%s, %s, %s, %s, 'pending')
                """, (loan['id'], num, due, amt))
                count += 1
                
            print(f"  -> Generated {count} installments.")
            conn.commit() # Commit per loan
            
        except Exception as e:
            print(f"  -> Error fixing loan {loan['id']}: {e}")
            conn.rollback()
            
    conn.commit()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    regenerate_installments()
