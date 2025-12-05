"""
Loan Payment Manager - Centralizes all loan payment logic
Handles payment processing, status updates, and installment tracking
"""

from database import get_db_connection, log_action
from datetime import datetime

def calculate_outstanding_balance(loan_id):
    """
    Calcula el saldo pendiente de un préstamo.
    
    Returns:
        dict: {
            'total_debt': Monto total adeudado (capital + intereses),
            'total_paid': Total pagado hasta ahora,
            'balance': Saldo pendiente,
            'loan_amount': Monto original del préstamo,
            'interest_amount': Intereses calculados,
            'installments_paid': Número de cuotas pagadas (si aplica),
            'installments_total': Total de cuotas (si aplica)
        }
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get loan details
    cursor.execute("SELECT * FROM loans WHERE id = ?", (loan_id,))
    loan = cursor.fetchone()
    
    if not loan:
        conn.close()
        return None
    
    # Calculate total paid from transactions
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) as total_paid
        FROM transactions
        WHERE loan_id = ? AND type = 'income' AND category = 'payment'
    """, (loan_id,))
    result = cursor.fetchone()
    total_paid = float(result['total_paid'])
    
    # Calculate interest based on loan type
    loan_amount = float(loan['amount'])
    interest_rate = float(loan['interest_rate']) if loan['interest_rate'] else 0
    
    # For scheduled loans, check installments
    cursor.execute("""
        SELECT COUNT(*) as total, 
               SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid
        FROM installments
        WHERE loan_id = ?
    """, (loan_id,))
    installment_info = cursor.fetchone()
    
    has_installments = installment_info and installment_info['total'] > 0
    
    if has_installments:
        # For scheduled loans, total debt is sum of all installments
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) as total_installments,
                   COALESCE(SUM(paid_amount), 0) as paid_installments
            FROM installments
            WHERE loan_id = ?
        """, (loan_id,))
        inst_result = cursor.fetchone()
        total_debt = float(inst_result['total_installments'])
        interest_amount = total_debt - loan_amount
        installments_paid = installment_info['paid']
        installments_total = installment_info['total']
    else:
        # For simple loans, calculate interest
        # Simplified: interest_amount = loan_amount * (interest_rate / 100)
        interest_amount = loan_amount * (interest_rate / 100)
        total_debt = loan_amount + interest_amount
        installments_paid = 0
        installments_total = 0
    
    balance = total_debt - total_paid
    
    conn.close()
    
    return {
        'total_debt': total_debt,
        'total_paid': total_paid,
        'balance': max(0, balance),  # Never negative
        'loan_amount': loan_amount,
        'interest_amount': interest_amount,
        'installments_paid': installments_paid,
        'installments_total': installments_total,
        'has_installments': has_installments
    }


def get_next_installment(loan_id):
    """
    Obtiene la siguiente cuota pendiente de un préstamo programado.
    
    Returns:
        dict: Información de la cuota o None si no hay cuotas pendientes
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM installments
        WHERE loan_id = ? AND status = 'pending'
        ORDER BY number ASC
        LIMIT 1
    """, (loan_id,))
    
    installment = cursor.fetchone()
    conn.close()
    
    return installment


def update_installment_payment(installment_id, amount, payment_method, payment_date=None):
    """
    Actualiza una cuota como pagada o parcialmente pagada.
    
    Args:
        installment_id: ID de la cuota
        amount: Monto pagado
        payment_method: Método de pago
        payment_date: Fecha de pago (default: hoy)
    
    Returns:
        bool: True si se actualizó correctamente
    """
    if payment_date is None:
        payment_date = datetime.now().strftime('%Y-%m-%d')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get installment info
    cursor.execute("SELECT * FROM installments WHERE id = ?", (installment_id,))
    installment = cursor.fetchone()
    
    if not installment:
        conn.close()
        return False
    
    installment_amount = float(installment['amount'])
    current_paid = float(installment['paid_amount']) if installment['paid_amount'] else 0
    new_paid = current_paid + amount
    
    # Determine new status
    if new_paid >= installment_amount:
        new_status = 'paid'
        new_paid = installment_amount  # Cap at installment amount
    elif new_paid > 0:
        new_status = 'partial'
    else:
        new_status = 'pending'
    
    # Update installment
    cursor.execute("""
        UPDATE installments
        SET status = ?, paid_amount = ?, payment_date = ?, payment_method = ?
        WHERE id = ?
    """, (new_status, new_paid, payment_date, payment_method, installment_id))
    
    conn.commit()
    conn.close()
    
    return True


def process_loan_payment(loan_id, amount, payment_method, session_id, user_id, description=None):
    """
    Procesa un pago de préstamo de manera completa.
    
    Realiza todas las operaciones necesarias:
    1. Registra la transacción
    2. Actualiza cuotas si es préstamo programado
    3. Actualiza estado del préstamo si se cancela completamente
    4. Registra fecha de cancelación
    
    Args:
        loan_id: ID del préstamo
        amount: Monto del pago
        payment_method: Método de pago (efectivo, yape, deposito)
        session_id: ID de la sesión de caja
        user_id: ID del usuario que registra el pago
        description: Descripción adicional (opcional)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'transaction_id': int,
            'balance_info': dict,
            'loan_paid_off': bool,
            'error': str (si success=False)
        }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Verify loan exists and is active
        cursor.execute("SELECT * FROM loans WHERE id = ?", (loan_id,))
        loan = cursor.fetchone()
        
        if not loan:
            conn.close()
            return {'success': False, 'error': 'Préstamo no encontrado'}
        
        if loan['status'] == 'paid':
            conn.close()
            return {'success': False, 'error': 'Este préstamo ya está cancelado'}
        
        # 2. Get balance info before payment
        balance_before = calculate_outstanding_balance(loan_id)
        
        if not balance_before:
            conn.close()
            return {'success': False, 'error': 'Error al calcular saldo'}
        
        # 3. Build description
        if not description:
            description = f"Pago préstamo #{loan_id}"
        
        # 4. Register transaction
        cursor.execute("""
            INSERT INTO transactions (type, category, amount, description, payment_method, cash_session_id, loan_id, user_id, date)
            VALUES ('income', 'payment', ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
        """, (amount, description, payment_method, session_id, loan_id, user_id))
        
        transaction_id = cursor.lastrowid
        
        # 5. Update installments if applicable
        if balance_before['has_installments']:
            remaining_amount = amount
            
            while remaining_amount > 0:
                next_inst = get_next_installment(loan_id)
                if not next_inst:
                    break  # No more pending installments
                
                inst_amount = float(next_inst['amount'])
                inst_paid = float(next_inst['paid_amount']) if next_inst['paid_amount'] else 0
                inst_balance = inst_amount - inst_paid
                
                # Apply payment to this installment
                payment_to_apply = min(remaining_amount, inst_balance)
                update_installment_payment(next_inst['id'], payment_to_apply, payment_method)
                
                remaining_amount -= payment_to_apply
        
        # 6. Calculate balance after payment
        balance_after = calculate_outstanding_balance(loan_id)
        
        # 7. Check if loan is fully paid
        loan_paid_off = False
        if balance_after['balance'] <= 0.01:  # Allow tiny rounding errors
            # Mark loan as paid
            cursor.execute("""
                UPDATE loans
                SET status = 'paid', end_date = DATE('now')
                WHERE id = ?
            """, (loan_id,))
            
            loan_paid_off = True
            
            # Log action
            log_action(user_id, 'loan_paid_off', f'Préstamo #{loan_id} cancelado completamente')
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'message': '¡Préstamo cancelado!' if loan_paid_off else 'Pago registrado correctamente',
            'transaction_id': transaction_id,
            'balance_info': balance_after,
            'loan_paid_off': loan_paid_off,
            'balance_before': balance_before['balance'],
            'balance_after': balance_after['balance']
        }
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return {
            'success': False,
            'error': f'Error al procesar pago: {str(e)}'
        }


def get_loan_payment_history(loan_id):
    """
    Obtiene el historial completo de pagos de un préstamo.
    
    Returns:
        list: Lista de transacciones de pago
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT t.*, u.full_name as cashier_name
        FROM transactions t
        LEFT JOIN users u ON t.user_id = u.id
        WHERE t.loan_id = ? AND t.type = 'income' AND t.category = 'payment'
        ORDER BY t.date DESC
    """, (loan_id,))
    
    payments = cursor.fetchall()
    conn.close()
    
    return payments


def get_rapidiario_schedule(loan_id):
    """
    Obtiene el cronograma completo de un préstamo Rapidiario con estados actuales.
    
    Returns:
        dict: {
            'overdue': [cuotas vencidas],
            'today': cuota de hoy o None,
            'pending': [cuotas futuras],
            'paid': [cuotas pagadas],
            'total_overdue': monto total vencido,
            'total_pending': monto total pendiente,
            'all_installments': todas las cuotas ordenadas
        }
    """
    from datetime import date
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all installments for this loan
    cursor.execute("""
        SELECT * FROM installments
        WHERE loan_id = ?
        ORDER BY number ASC
    """, (loan_id,))
    
    installments = cursor.fetchall()
    
    # If no installments found, try to create them automatically
    if not installments:
        conn.close()
        
        # Try to auto-generate installments
        try:
            from utils.loan_calculator import calcular_cuota_rapidiario
            
            conn2 = get_db_connection()
            cursor2 = conn2.cursor()
            
            # Get loan details
            cursor2.execute("SELECT * FROM loans WHERE id = ?", (loan_id,))
            loan = cursor2.fetchone()
            
            if loan and loan['loan_type'] in ('rapid', 'rapidiario'):
                amount = float(loan['amount'])
                interest_rate = float(loan['interest_rate']) if loan['interest_rate'] else 8.0
                start_date_str = loan['start_date']
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                
                # Generate installments
                loan_info = calcular_cuota_rapidiario(amount, interest_rate, start_date, 'Diario')
                
                # Insert them
                for num, due, amt in loan_info['cuotas']:
                    cursor2.execute("""
                        INSERT INTO installments (loan_id, number, due_date, amount, status, paid_amount)
                        VALUES (?, ?, ?, ?, 'pending', 0)
                    """, (loan_id, num, due, amt))
                
                conn2.commit()
                
                # Re-fetch installments
                cursor2.execute("""
                    SELECT * FROM installments
                    WHERE loan_id = ?
                    ORDER BY number ASC
                """, (loan_id,))
                
                installments = cursor2.fetchall()
                conn2.close()
            else:
                conn2.close()
        except Exception as e:
            print(f"Error auto-creating installments: {e}")
            pass
    else:
        conn.close()
    
    if not installments:
        return {
            'overdue': [],
            'today': None,
            'pending': [],
            'paid': [],
            'total_overdue': 0,
            'total_pending': 0,
            'all_installments': []
        }
    
    today = date.today()
    
    overdue = []
    today_inst = None
    pending = []
    paid = []
    
    for inst in installments:
        inst_dict = dict(inst)
        due_date = datetime.strptime(inst['due_date'], '%Y-%m-%d').date()
        paid_amount = float(inst['paid_amount']) if inst['paid_amount'] else 0
        inst_amount = float(inst['amount'])
        balance = inst_amount - paid_amount
        
        inst_dict['balance'] = balance
        inst_dict['due_date_obj'] = due_date
        
        if inst['status'] == 'paid':
            paid.append(inst_dict)
        elif due_date < today and balance > 0:
            # Overdue
            overdue.append(inst_dict)
        elif due_date == today and balance > 0:
            # Due today
            today_inst = inst_dict
        elif due_date > today:
            # Future
            pending.append(inst_dict)
    
    total_overdue = sum(i['balance'] for i in overdue)
    if today_inst:
        total_overdue += today_inst['balance']
    
    total_pending = sum(i['balance'] for i in pending)
    if today_inst:
        total_pending += today_inst['balance']
    total_pending += sum(i['balance'] for i in overdue)
    
    return {
        'overdue': overdue,
        'today': today_inst,
        'pending': pending,
        'paid': paid,
        'total_overdue': total_overdue,
        'total_pending': total_pending,
        'all_installments': installments
    }


def apply_rapidiario_payment(loan_id, amount, payment_method, session_id, user_id, description=None):
    """
    Aplica un pago a un préstamo Rapidiario con lógica específica de cuotas diarias.
    
    Lógica:
    1. Pagar cuotas vencidas en orden cronológico
    2. Si sobra dinero, pagar cuota de hoy
    3. Si aún sobra, aplicar excedente a las ÚLTIMAS cuotas (de atrás hacia adelante)
    
    Args:
        loan_id: ID del préstamo
        amount: Monto del pago
        payment_method: Método de pago
        session_id: ID de sesión de caja
        user_id: ID del usuario
        description: Descripción adicional
    
    Returns:
        dict: Resultado del pago con detalles de cuotas pagadas
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get loan info
        cursor.execute("SELECT * FROM loans WHERE id = ?", (loan_id,))
        loan = cursor.fetchone()
        
        if not loan:
            conn.close()
            return {'success': False, 'error': 'Préstamo no encontrado'}
        
        # Get schedule
        schedule = get_rapidiario_schedule(loan_id)
        
        if not description:
            description = f"Pago préstamo Rapidiario #{loan_id}"
        
        # Register transaction
        cursor.execute("""
            INSERT INTO transactions (type, category, amount, description, payment_method, cash_session_id, loan_id, user_id, date)
            VALUES ('income', 'payment', ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
        """, (amount, description, payment_method, session_id, loan_id, user_id))
        
        transaction_id = cursor.lastrowid
        
        # Apply payment to installments
        remaining = amount
        installments_paid = []
        
        # 1. Pay overdue installments first (chronological order)
        for inst in schedule['overdue']:
            if remaining <= 0:
                break
            
            inst_id = inst['id']
            balance = inst['balance']
            paid_amount = float(inst['paid_amount']) if inst['paid_amount'] else 0
            
            payment_to_apply = min(remaining, balance)
            new_paid = paid_amount + payment_to_apply
            
            # Update installment
            if new_paid >= float(inst['amount']):
                cursor.execute("""
                    UPDATE installments
                    SET status = 'paid', paid_amount = ?, payment_date = DATE('now'), payment_method = ?
                    WHERE id = ?
                """, (new_paid, payment_method, inst_id))
                installments_paid.append(f"Cuota #{inst['number']} (vencida)")
            else:
                cursor.execute("""
                    UPDATE installments
                    SET status = 'partial', paid_amount = ?, payment_date = DATE('now'), payment_method = ?
                    WHERE id = ?
                """, (new_paid, payment_method, inst_id))
                installments_paid.append(f"Cuota #{inst['number']} parcial")
            
            remaining -= payment_to_apply
        
        # 2. Pay today's installment
        if remaining > 0 and schedule['today']:
            inst = schedule['today']
            inst_id = inst['id']
            balance = inst['balance']
            paid_amount = float(inst['paid_amount']) if inst['paid_amount'] else 0
            
            payment_to_apply = min(remaining, balance)
            new_paid = paid_amount + payment_to_apply
            
            if new_paid >= float(inst['amount']):
                cursor.execute("""
                    UPDATE installments
                    SET status = 'paid', paid_amount = ?, payment_date = DATE('now'), payment_method = ?
                    WHERE id = ?
                """, (new_paid, payment_method, inst_id))
                installments_paid.append(f"Cuota #{inst['number']} (hoy)")
            else:
                cursor.execute("""
                    UPDATE installments
                    SET status = 'partial', paid_amount = ?, payment_date = DATE('now'), payment_method = ?
                    WHERE id = ?
                """, (new_paid, payment_method, inst_id))
                installments_paid.append(f"Cuota #{inst['number']} parcial")
            
            remaining -= payment_to_apply
        
        # 3. If excess, apply to LAST installments (reverse order)
        if remaining > 0 and schedule['pending']:
            # Reverse order (last installments first)
            pending_reversed = sorted(schedule['pending'], key=lambda x: x['number'], reverse=True)
            
            for inst in pending_reversed:
                if remaining <= 0:
                    break
                
                inst_id = inst['id']
                inst_amount = float(inst['amount'])
                paid_amount = float(inst['paid_amount']) if inst['paid_amount'] else 0
                balance = inst_amount - paid_amount
                
                payment_to_apply = min(remaining, balance)
                new_paid = paid_amount + payment_to_apply
                
                if new_paid >= inst_amount:
                    cursor.execute("""
                        UPDATE installments
                        SET status = 'paid', paid_amount = ?, payment_date = DATE('now'), payment_method = ?
                        WHERE id = ?
                    """, (new_paid, payment_method, inst_id))
                    installments_paid.append(f"Cuota #{inst['number']} (adelantada)")
                else:
                    cursor.execute("""
                        UPDATE installments
                        SET status = 'partial', paid_amount = ?, payment_date = DATE('now'), payment_method = ?
                        WHERE id = ?
                    """, (new_paid, payment_method, inst_id))
                    installments_paid.append(f"Cuota #{inst['number']} parcial")
                
                remaining -= payment_to_apply
        
        # Check if all installments are paid
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid_count
            FROM installments
            WHERE loan_id = ?
        """, (loan_id,))
        
        result = cursor.fetchone()
        all_paid = result['total'] == result['paid_count']
        
        if all_paid:
            cursor.execute("""
                UPDATE loans
                SET status = 'paid', end_date = DATE('now')
                WHERE id = ?
            """, (loan_id,))
            
            log_action(user_id, 'loan_paid_off', f'Préstamo Rapidiario #{loan_id} cancelado')
        
        conn.commit()
        conn.close()
        
        # Get updated schedule
        updated_schedule = get_rapidiario_schedule(loan_id)
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'loan_paid_off': all_paid,
            'installments_paid': installments_paid,
            'remaining_balance': updated_schedule['total_pending'],
            'schedule': updated_schedule,
            'message': '¡Préstamo cancelado!' if all_paid else f'Pago aplicado a {len(installments_paid)} cuota(s)'
        }
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return {
            'success': False,
            'error': f'Error al procesar pago: {str(e)}'
        }


def can_refinance_loan(loan_id):
    """
    Verifica si un préstamo puede ser refinanciado.
    
    Returns:
        dict: {'can_refinance': bool, 'reason': str}
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM loans WHERE id = ?", (loan_id,))
    loan = cursor.fetchone()
    
    if not loan:
        conn.close()
        return {'can_refinance': False, 'reason': 'Préstamo no encontrado'}
    
    if loan['status'] == 'paid':
        conn.close()
        return {'can_refinance': False, 'reason': 'Préstamo ya cancelado'}
    
    if loan['loan_type'] == 'rapid':
        # Check refinance count
        refinance_count = loan.get('refinance_count', 0) or 0
        if refinance_count >= 3:
            conn.close()
            return {'can_refinance': False, 'reason': 'Máximo 3 refinanciamientos alcanzado'}
    
    conn.close()
    return {'can_refinance': True, 'reason': 'Puede refinanciar'}
