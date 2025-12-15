
import sqlite3
import os
from datetime import datetime, timedelta, date

# Database path (adjust if needed)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'system.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def seed_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("Seeding data... Starting from June 1st, 2025")
    
    # Base start date
    base_date = date(2025, 6, 1)
    
    # --- HELPER FUNCTIONS ---
    def create_client(i, name, last_name):
        dni = f"TEST{i:04d}"
        cursor.execute(
            "INSERT INTO clients (dni, first_name, last_name, address, phone, analyst_id) VALUES (?, ?, ?, ?, ?, ?)",
            (dni, name, last_name, "Av. Test 123", "555-0000", 1)
        )
        return cursor.lastrowid

    def create_loan(client_id, ltype, amount, rate, start, duration_days, status='active'):
        due = start + timedelta(days=duration_days)
        cursor.execute(
            """INSERT INTO loans (client_id, loan_type, amount, interest_rate, start_date, due_date, status, analyst_id) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (client_id, ltype, amount, rate, start.isoformat(), due.isoformat(), status, 1)
        )
        return cursor.lastrowid
        
    def create_installment(loan_id, number, due_date, amount, status='pending', paid=0, pay_date=None):
        cursor.execute(
            """INSERT INTO installments (loan_id, number, due_date, amount, status, paid_amount, payment_date) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (loan_id, number, due_date.isoformat(), amount, status, paid, pay_date)
        )

    def create_manual(client_name, concept, modality, lent, interest, paid, balance, status):
        total = lent + interest
        cursor.execute(
            """INSERT INTO manual_receivables (client_name, concept, modality, amount_lent, interest, total_debt, paid_amount, balance, status, loan_date, due_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (client_name, concept, modality, lent, interest, total, paid, balance, status, base_date.isoformat(), base_date.isoformat())
        )

    # --- 1. RAPIDIARIO (5 Clients) ---
    # Daily payments, 8% interest
    print("Creating Rapidiario Clients...")
    # C1: Punctual (Paid 5/10 installments)
    cid1 = create_client(1, "Juan", "Puntual (R)")
    lid1 = create_loan(cid1, 'rapidiario', 1000, 8, base_date, 24, 'active') # 1000 + 80 = 1080. 24 days. 45/day.
    for i in range(1, 25):
        d = base_date + timedelta(days=i)
        status = 'paid' if i <= 10 else 'pending'
        paid = 45 if i <= 10 else 0
        pdate = d.isoformat() if i <= 10 else None
        create_installment(lid1, i, d, 45, status, paid, pdate)

    # C2: Overdue (Paid 2, missed rest, now late)
    cid2 = create_client(2, "Pedro", "Moroso (R)")
    lid2 = create_loan(cid2, 'rapidiario', 500, 8, base_date, 24, 'overdue')
    for i in range(1, 25):
        d = base_date + timedelta(days=i)
        status = 'paid' if i <= 2 else 'overdue' # Assuming today is far future
        paid = 22.5 if i <= 2 else 0 # 500+40=540 / 24 = 22.5
        create_installment(lid2, i, d, 22.5, status, paid)

    # C3: Partial Payer
    cid3 = create_client(3, "Maria", "Parcial (R)")
    lid3 = create_loan(cid3, 'rapidiario', 2000, 8, base_date, 20, 'active')
    # 2000 + 160 = 2160 / 20 = 108
    for i in range(1, 21):
        d = base_date + timedelta(days=i)
        # Pays half
        create_installment(lid3, i, d, 108, 'partial', 54, d.isoformat())

    # C4: No Payment
    cid4 = create_client(4, "Luis", "Nopaga (R)")
    lid4 = create_loan(cid4, 'rapidiario', 1000, 8, base_date, 10, 'overdue')
    for i in range(1, 11):
        d = base_date + timedelta(days=i)
        create_installment(lid4, i, d, 108, 'overdue', 0, None)

    # C5: Fully Paid
    cid5 = create_client(5, "Ana", "Pagado (R)")
    lid5 = create_loan(cid5, 'rapidiario', 500, 8, base_date, 10, 'paid')
    for i in range(1, 11):
        d = base_date + timedelta(days=i)
        create_installment(lid5, i, d, 54, 'paid', 54, d.isoformat())


    # --- 2. CASA DE EMPEÑO (5 Clients) ---
    print("Creating Pawn Clients...")
    # C6: Active Punctual
    cid6 = create_client(6, "Carlos", "Empeño (Activo)")
    lid6 = create_loan(cid6, 'empeno', 200, 10, base_date, 30, 'active')
    # Add Item
    cursor.execute("INSERT INTO pawn_details (loan_id, item_type, brand, characteristics, market_value) VALUES (?, ?, ?, ?, ?)", 
                   (lid6, "Joya", "Oro", "Anillo 18k", 300))
    # 1 Installment (end of month)
    create_installment(lid6, 1, base_date + timedelta(days=30), 220, 'pending', 0)

    # C7: Paid/Retirado
    cid7 = create_client(7, "Sofia", "Empeño (Retirado)")
    lid7 = create_loan(cid7, 'empeno', 500, 10, base_date, 30, 'paid')
    cursor.execute("INSERT INTO pawn_details (loan_id, item_type, brand, characteristics, market_value) VALUES (?, ?, ?, ?, ?)", 
                   (lid7, "Electro", "Samsung", "TV 50in", 800))
    create_installment(lid7, 1, base_date + timedelta(days=30), 550, 'paid', 550, (base_date + timedelta(days=29)).isoformat())

    # C8: Overdue (Lost item risk)
    cid8 = create_client(8, "Miguel", "Empeño (Vencido)")
    lid8 = create_loan(cid8, 'empeno', 100, 10, base_date, 30, 'overdue')
    cursor.execute("INSERT INTO pawn_details (loan_id, item_type, brand, characteristics, market_value) VALUES (?, ?, ?, ?, ?)", 
                   (lid8, "Herramienta", "Bosch", "Taladro", 150))
    create_installment(lid8, 1, base_date + timedelta(days=30), 110, 'overdue', 0)

    # C9: Renegotiated/Partial (Interest paid only) - Sim as active
    cid9 = create_client(9, "Elena", "Empeño (Solo Interes)")
    lid9 = create_loan(cid9, 'empeno', 1000, 10, base_date, 30, 'active')
    cursor.execute("INSERT INTO pawn_details (loan_id, item_type, market_value) VALUES (?, ?, ?)", (lid9, "Moto", 2000))
    create_installment(lid9, 1, base_date + timedelta(days=30), 1100, 'pending', 100, (base_date + timedelta(days=30)).isoformat()) # Paid interest 100

    # C10: New
    cid10 = create_client(10, "Jose", "Empeño (Nuevo)")
    lid10 = create_loan(cid10, 'empeno', 300, 10, date.today(), 30, 'active') # Starts today
    cursor.execute("INSERT INTO pawn_details (loan_id, item_type, market_value) VALUES (?, ?, ?)", (lid10, "Laptop", 500))
    create_installment(lid10, 1, date.today() + timedelta(days=30), 330, 'pending', 0)


    # --- 3. BANCARIO (5 Clients) ---
    print("Creating Bank Clients...")
    # C11-C15: Testing Cash/Analysis
    for i in range(11, 16):
        status_map = {11: 'paid', 12: 'active', 13: 'overdue', 14: 'pending', 15: 'active'}
        name_map = {11: "Pagado", 12: "Activo", 13: "Moroso", 14: "Pendiente", 15: "Reciente"}
        
        cid = create_client(i, f"Banco {i}", f"{name_map[i]}")
        lid = create_loan(cid, 'bancario', 5000, 5, base_date, 180, status_map[i]) # 6 months
        
        amt = 5000 * 1.05
        monthly = amt / 6
        
        for m in range(1, 7):
            d = base_date + timedelta(days=m*30)
            
            st = 'pending'
            pd = 0
            pdate = None
            
            if i == 11: # Paid
                st = 'paid'; pd = monthly; pdate = d.isoformat()
            elif i == 12: # Active (paid first 3)
                if m <= 3: st = 'paid'; pd = monthly; pdate = d.isoformat()
            elif i == 13: # Overdue (paid none)
                st = 'overdue'
            
            create_installment(lid, m, d, monthly, st, pd, pdate)


    # --- 4. MANUAL / FROZEN (5 Clients) ---
    print("Creating Manual/Frozen Clients...")
    # C16-C20 added to Manual Receivables
    
    # C16: Rapidiario Viejo (Vencido)
    create_manual("Cliente Viejo 1", "Prestamo Antiguo", "Rapidiario", 1000, 200, 0, 1200, "overdue")
    
    # C17: Frozen (Congelado)
    create_manual("Cliente Congelado", "Congelado por Falta Pago", "Congelado", 2000, 500, 500, 2000, "pending")
    
    # C18: Bancarizado Externo
    create_manual("Cliente Banco Ext", "Deuda Banco X", "Bancarizado", 5000, 1000, 1000, 5000, "pending")
    
    # C19: Empeño Perdido
    create_manual("Cliente Joya", "Joya Perdida", "Casa de Empeño", 500, 50, 0, 550, "overdue")
    
    # C20: Reciente
    create_manual("Cliente Nuevo Man", "Prestamo Ayer", "Rapidiario", 100, 20, 0, 120, "pending")

    conn.commit()
    conn.close()
    print("Seeding Complete. 20 Clients Created.")

if __name__ == "__main__":
    seed_data()
