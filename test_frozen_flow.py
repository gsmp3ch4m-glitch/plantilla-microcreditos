import sqlite3
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime, timedelta
from utils.loan_manager import refinance_rapidiario, freeze_loan, execute_collateral, get_loan_details

DB_PATH = 'database/system.db'

def setup_test_db():
    # Ensure we are using the correct DB
    pass

def test_flow():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Create a test client
    import random
    dni = str(random.randint(10000000, 99999999))
    cursor.execute("INSERT INTO clients (first_name, last_name, dni) VALUES ('Test', 'User', ?)", (dni,))
    client_id = cursor.lastrowid
    
    # 2. Create a Rapidiario loan
    start_date = datetime.now().date()
    due_date = start_date + timedelta(days=30)
    cursor.execute("""
        INSERT INTO loans (client_id, loan_type, amount, interest_rate, start_date, due_date, status, refinance_count)
        VALUES (?, 'rapidiario', 1000, 20, ?, ?, 'active', 0)
    """, (client_id, start_date, due_date))
    loan_id = cursor.lastrowid
    conn.commit()
    print(f"Created Loan #{loan_id}")
    
    # 3. Test Refinance
    print("\nTesting Refinance...")
    success, msg = refinance_rapidiario(loan_id, 1) # user_id 1
    print(f"Refinance Result: {success} - {msg}")
    
    if success:
        # Get new loan id
        cursor.execute("SELECT id FROM loans WHERE parent_loan_id = ?", (loan_id,))
        new_loan = cursor.fetchone()
        new_loan_id = new_loan[0]
        print(f"New Loan ID: {new_loan_id}")
        
        # Verify new loan details
        details = get_loan_details(new_loan_id)
        print(f"New Loan Interest: {details['interest_rate']}% (Expected 8.0)")
        print(f"New Loan Status: {details['status']}")
        print(f"Refinance Count: {details['refinance_count']}")
        
        # 4. Test Freeze on new loan
        print("\nTesting Freeze...")
        success, msg = freeze_loan(new_loan_id, 1)
        print(f"Freeze Result: {success} - {msg}")
        
        details = get_loan_details(new_loan_id)
        print(f"Loan Status: {details['status']}")
        print(f"Frozen Amount: {details['frozen_amount']}")
        
        # 5. Test Liquidate (Simulated on frozen loan)
        print("\nTesting Liquidate...")
        success, msg = execute_collateral(new_loan_id, 1500, 100, 1)
        print(f"Liquidate Result: {success} - {msg}")
        
        details = get_loan_details(new_loan_id)
        print(f"Final Status: {details['status']}")
        
    conn.close()

if __name__ == "__main__":
    test_flow()
