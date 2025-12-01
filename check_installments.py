import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from database import get_db_connection

def check_installments():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("Checking Loans...")
        cursor.execute("SELECT id, client_id, amount, date(start_date) FROM loans ORDER BY id DESC LIMIT 5")
        loans = cursor.fetchall()
        for loan in loans:
            print(f"Loan ID: {loan['id']}, Amount: {loan['amount']}, Date: {loan[3]}")
            
            # Check installments for this loan
            cursor.execute("SELECT count(*) FROM installments WHERE loan_id = ?", (loan['id'],))
            count = cursor.fetchone()[0]
            print(f"  -> Installments count: {count}")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_installments()
