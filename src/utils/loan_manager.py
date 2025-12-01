import sqlite3
from datetime import datetime, timedelta
from database import get_db_connection, log_action

def get_loan_details(loan_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM loans WHERE id = ?", (loan_id,))
    loan = cursor.fetchone()
    conn.close()
    return loan

def calculate_total_debt(loan_id):
    """Calcula la deuda total actual (Capital + Interés - Pagado)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get loan info
    cursor.execute("SELECT amount, interest_rate FROM loans WHERE id = ?", (loan_id,))
    loan = cursor.fetchone()
    
    if not loan:
        conn.close()
        return 0
        
    # Calculate expected total payment (Capital + Interest)
    # Simple interest calculation for now, assuming monthly or fixed term
    # TODO: Refine based on specific loan type calculation rules if needed
    total_expected = loan['amount'] * (1 + loan['interest_rate'] / 100)
    
    # Get total paid
    cursor.execute("SELECT SUM(amount) as paid FROM installments WHERE loan_id = ? AND status = 'paid'", (loan_id,))
    paid_row = cursor.fetchone()
    total_paid = paid_row['paid'] if paid_row and paid_row['paid'] else 0
    
    conn.close()
    
    return max(0, total_expected - total_paid)

def can_refinance_rapidiario(loan_id):
    """Verifica si un préstamo Rapidiario puede ser refinanciado"""
    loan = get_loan_details(loan_id)
    if not loan:
        return False, "Préstamo no encontrado"
        
    if loan['loan_type'] != 'rapidiario':
        return False, "Solo se pueden refinanciar préstamos Rapidiario"
        
    if loan['status'] not in ['active', 'overdue']:
        return False, "El préstamo debe estar activo o vencido"
        
    # Check refinance count (max 3)
    refinance_count = loan['refinance_count'] if loan['refinance_count'] is not None else 0
    if refinance_count >= 3:
        return False, "Ya se ha alcanzado el límite de 3 refinanciamientos"
        
    return True, ""

def refinance_rapidiario(loan_id, user_id):
    """
    Refinancia un préstamo Rapidiario:
    1. Cierra el actual como 'refinanced'
    2. Crea uno nuevo con la deuda total como capital, 8% interés, 30 días
    """
    can, msg = can_refinance_rapidiario(loan_id)
    if not can:
        return False, msg
        
    loan = get_loan_details(loan_id)
    total_debt = calculate_total_debt(loan_id)
    
    if total_debt <= 0:
        return False, "No hay deuda pendiente para refinanciar"
        
    conn = get_db_connection()
    try:
        # 1. Update old loan status
        conn.execute("UPDATE loans SET status = 'refinanced' WHERE id = ?", (loan_id,))
        
        # 2. Create new loan
        new_interest = 8.0
        start_date = datetime.now().date()
        due_date = start_date + timedelta(days=30)
        new_count = (loan['refinance_count'] or 0) + 1
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO loans (
                client_id, loan_type, amount, interest_rate, 
                start_date, due_date, status, 
                analyst_id, parent_loan_id, refinance_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            loan['client_id'], 'rapidiario', total_debt, new_interest,
            start_date, due_date, 'active',
            loan['analyst_id'], loan_id, new_count
        ))
        
        new_loan_id = cursor.lastrowid
        
        # 3. Create single installment for the new loan (30 days)
        # New total = Debt * 1.08
        new_total_amount = total_debt * (1 + new_interest/100)
        
        cursor.execute("""
            INSERT INTO installments (loan_id, number, due_date, amount, status)
            VALUES (?, ?, ?, ?, ?)
        """, (new_loan_id, 1, due_date, new_total_amount, 'pending'))
        
        conn.commit()
        log_action(user_id, "Refinanciar", f"Préstamo #{loan_id} refinanciado a #{new_loan_id}")
        return True, f"Préstamo refinanciado exitosamente. Nuevo ID: {new_loan_id}"
        
    except Exception as e:
        conn.rollback()
        return False, f"Error al refinanciar: {str(e)}"
    finally:
        conn.close()

def freeze_loan(loan_id, user_id):
    """
    Congela un préstamo:
    - Rapidiario: Deuda + 5% gastos admin
    - Otros: Deuda total
    """
    loan = get_loan_details(loan_id)
    if not loan:
        return False, "Préstamo no encontrado"
        
    total_debt = calculate_total_debt(loan_id)
    
    admin_fee = 0
    if loan['loan_type'] == 'rapidiario':
        admin_fee = total_debt * 0.05
        
    frozen_amount = total_debt + admin_fee
    
    conn = get_db_connection()
    try:
        conn.execute("""
            UPDATE loans 
            SET status = 'frozen', 
                frozen_amount = ?, 
                admin_fee = ?, 
                frozen_date = ? 
            WHERE id = ?
        """, (frozen_amount, admin_fee, datetime.now().date(), loan_id))
        
        conn.commit()
        log_action(user_id, "Congelar", f"Préstamo #{loan_id} congelado. Monto: {frozen_amount:.2f}")
        return True, "Préstamo congelado exitosamente"
        
    except Exception as e:
        conn.rollback()
        return False, f"Error al congelar: {str(e)}"
    finally:
        conn.close()

def check_and_freeze_loans(user_id):
    """
    Revisa todos los préstamos activos/vencidos y los congela si cumplen las condiciones:
    - Rapidiario: 3 refinanciamientos y vencido
    - Empeño: > 75 días desde inicio (60 + 15)
    - Bancario: > 105 días desde inicio (90 + 15)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get candidates
    cursor.execute("SELECT * FROM loans WHERE status IN ('active', 'overdue')")
    loans = cursor.fetchall()
    conn.close()
    
    frozen_count = 0
    today = datetime.now().date()
    
    for loan in loans:
        should_freeze = False
        
        # Parse dates safely
        try:
            start_date = datetime.strptime(loan['start_date'], '%Y-%m-%d').date()
        except:
            continue # Skip invalid dates
            
        days_since_start = (today - start_date).days
        
        if loan['loan_type'] == 'rapidiario':
            # Freeze if max refinances reached AND overdue
            try:
                due_date = datetime.strptime(loan['due_date'], '%Y-%m-%d').date()
                if (loan['refinance_count'] or 0) >= 3 and today > due_date:
                    should_freeze = True
            except:
                pass
                
        elif loan['loan_type'] == 'empeno':
            # Freeze after 75 days (60 days term + 15 days grace)
            if days_since_start > 75:
                should_freeze = True
                
        elif loan['loan_type'] == 'bancario':
            # Freeze after 105 days (90 days term + 15 days grace)
            if days_since_start > 105:
                should_freeze = True
                
        if should_freeze:
            success, msg = freeze_loan(loan['id'], user_id)
            if success:
                frozen_count += 1
                
    return frozen_count

def execute_collateral(loan_id, sale_price, sales_expense, user_id):
    """
    Ejecuta la garantía (Remate):
    1. Registra precio venta y gastos
    2. Calcula deuda total
    3. Calcula devolución (Venta - Gasto - Deuda)
    4. Cierra préstamo como 'liquidated'
    """
    loan = get_loan_details(loan_id)
    if not loan: return False, "Préstamo no encontrado"
    
    # Calculate debt (use frozen amount if frozen, else calculate)
    if loan['status'] == 'frozen':
        debt = loan['frozen_amount']
    else:
        debt = calculate_total_debt(loan_id)
        
    refund_amount = sale_price - sales_expense - debt
    
    conn = get_db_connection()
    try:
        conn.execute("""
            UPDATE loans 
            SET status = 'liquidated',
                sale_price = ?,
                sales_expense = ?
            WHERE id = ?
        """, (sale_price, sales_expense, loan_id))
        
        # Register income transaction (Sale Price)
        conn.execute("""
            INSERT INTO transactions (type, category, amount, description, user_id, loan_id)
            VALUES ('income', 'collateral_sale', ?, ?, ?, ?)
        """, (sale_price, f"Remate Garantía Préstamo #{loan_id}", user_id, loan_id))
        
        # Register expense transaction (Sales Expense)
        if sales_expense > 0:
            conn.execute("""
                INSERT INTO transactions (type, category, amount, description, user_id, loan_id)
                VALUES ('expense', 'sales_expense', ?, ?, ?, ?)
            """, (sales_expense, f"Gasto Venta Garantía Préstamo #{loan_id}", user_id, loan_id))
            
        # Register expense transaction (Refund to client if positive)
        if refund_amount > 0:
             conn.execute("""
                INSERT INTO transactions (type, category, amount, description, user_id, loan_id)
                VALUES ('expense', 'client_refund', ?, ?, ?, ?)
            """, (refund_amount, f"Devolución Excedente Remate Préstamo #{loan_id}", user_id, loan_id))
            
        conn.commit()
        log_action(user_id, "Remate", f"Garantía rematada. Venta: {sale_price}, Devolución: {refund_amount:.2f}")
        
        return True, f"Remate exitoso.\n\nDeuda: {debt:.2f}\nVenta: {sale_price:.2f}\nGastos: {sales_expense:.2f}\n\nDevolución al Cliente: {refund_amount:.2f}"
        
    except Exception as e:
        conn.rollback()
        return False, f"Error al ejecutar garantía: {str(e)}"
    finally:
        conn.close()

def create_legacy_frozen_loan(client_id, loan_type, amount, frozen_date, **kwargs):
    """
    Crea un préstamo congelado histórico directamente.
    
    Args:
        client_id: ID del cliente
        loan_type: 'rapidiario', 'empeno', 'bancario'
        amount: Monto base (Deuda actual para rapidiario, Capital original para otros)
        frozen_date: Fecha de congelamiento
        **kwargs:
            - admin_fee: Para rapidiario (si se calcula fuera) or auto-calc inside?
              Let's auto-calc inside based on rules to be safe, or allow override.
            - interest_rate: Para empeño/bancario
            - months_overdue: Para empeño/bancario
            - description: Descripción de garantía u observaciones
            - user_id: ID del usuario que registra
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get analyst_id from client
        cursor.execute("SELECT analyst_id FROM clients WHERE id = ?", (client_id,))
        client_row = cursor.fetchone()
        analyst_id = client_row['analyst_id'] if client_row else None
        
        frozen_amount = 0
        admin_fee = 0
        interest_rate = kwargs.get('interest_rate', 0)
        
        if loan_type == 'rapidiario':
            # Rule: Amount + 5%
            # The user said: "agregar automaticamente el 5% pero solo para rapidiarios"
            # We assume 'amount' passed here is the debt amount BEFORE the 5% fee?
            # Or is it the final amount? The prompt says "monto prestado... y automaticamente sale cuanto deve".
            # For Rapidiario: "agregar clientes... con el ultimo monto... y al poner eso agregar automaticamente el 5%"
            # So input is the base amount, we add 5%.
            admin_fee = amount * 0.05
            frozen_amount = amount + admin_fee
            interest_rate = 0 # Not relevant for frozen sum, but maybe keep record
            
        elif loan_type in ['empeno', 'bancario']:
            # Rule: Capital + (Capital * Rate * Months)
            months = kwargs.get('months_overdue', 0)
            interest_amount = amount * (interest_rate / 100) * months
            frozen_amount = amount + interest_amount
            # No admin fee mentioned for these in this specific legacy flow, just interest
            
        # Insert loan
        cursor.execute("""
            INSERT INTO loans (
                client_id, loan_type, amount, interest_rate, 
                start_date, due_date, status, 
                frozen_amount, admin_fee, frozen_date, analyst_id
            ) VALUES (?, ?, ?, ?, ?, ?, 'frozen', ?, ?, ?, ?)
        """, (
            client_id, loan_type, amount, interest_rate,
            frozen_date, frozen_date, # Start/Due date same as frozen for legacy? Or calculate backwards? 
            # Let's use frozen_date as start/due to keep it simple, or maybe start_date = frozen_date - months
            frozen_amount, admin_fee, frozen_date, analyst_id
        ))
        
        loan_id = cursor.lastrowid
        
        # Add description/collateral if provided
        description = kwargs.get('description', '')
        if description:
            # For Empeño, we might want to add a dummy entry in pawn_details if needed, 
            # or just use the description field in a transaction or note.
            # The schema has a 'description' in pawn_details.
            if loan_type == 'empeno':
                cursor.execute("""
                    INSERT INTO pawn_details (loan_id, item_type, brand, condition, market_value, characteristics, description)
                    VALUES (?, 'Otros', 'Varios', 'Usado', ?, 'Carga Histórica', ?)
                """, (loan_id, amount, description))
        
        # Log action
        user_id = kwargs.get('user_id')
        log_action(user_id, "Carga Histórica", f"Préstamo Congelado #{loan_id} - {loan_type} - Total: {frozen_amount:.2f}")
        
        # Create a single installment for the total frozen amount so payments can be processed
        cursor.execute("""
            INSERT INTO installments (loan_id, number, amount, due_date, status, amount_paid)
            VALUES (?, 1, ?, ?, 'pending', 0)
        """, (loan_id, frozen_amount, frozen_date))
        
        conn.commit()
        return True, f"Préstamo histórico registrado. ID: {loan_id}. Total Congelado: {frozen_amount:.2f}"
        
    except Exception as e:
        conn.rollback()
        return False, f"Error al registrar: {str(e)}"
    finally:
        conn.close()
