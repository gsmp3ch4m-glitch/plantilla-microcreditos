import sqlite3
from datetime import datetime, timedelta
from database import get_db_connection
import calendar

class AnalyticsManager:
    def get_investment_distribution(self):
        """
        Retorna la distribución del dinero invertido por tipo de préstamo.
        Considera el saldo pendiente de capital.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Para préstamos activos, el monto invertido es el saldo pendiente.
        # Para simplificar, usaremos el monto original menos lo pagado (aprox) o el monto total si no hay pagos parciales complejos.
        # Mejor enfoque: Sumar 'amount' de préstamos activos/congelados.
        # Nota: En congelados, 'amount' es el monto original, 'frozen_amount' es la deuda total.
        # La inversión real es el Capital Original.
        
        query = """
            SELECT loan_type, SUM(amount) as total_capital
            FROM loans
            WHERE status IN ('active', 'overdue', 'frozen')
            GROUP BY loan_type
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        data = {row['loan_type']: row['total_capital'] for row in rows}
        
        # Mapear nombres
        labels = {
            'rapidiario': 'Rapidiario',
            'empeno': 'Empeño',
            'bancario': 'Bancario',
            'congelado': 'Congelado' # Si hay préstamos que nacieron congelados o migraron
        }
        
        # Ajustar para que 'frozen' sea una categoría propia si el status es frozen, 
        # pero la query agrupa por loan_type original.
        # El usuario quiere ver "cuanto en rapidiario, casa de empeño, bancario y congelado".
        # Entonces debemos agrupar por status='frozen' vs loan_type para los no frozen.
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Activos por tipo
        cursor.execute("""
            SELECT loan_type, SUM(amount) as total
            FROM loans 
            WHERE status IN ('active', 'overdue')
            GROUP BY loan_type
        """)
        active_rows = cursor.fetchall()
        
        # 2. Congelados (Todos juntos o separados? El usuario dijo "y congelado", singular)
        cursor.execute("""
            SELECT SUM(amount) as total
            FROM loans 
            WHERE status = 'frozen'
        """)
        frozen_row = cursor.fetchone()
        frozen_total = frozen_row['total'] if frozen_row and frozen_row['total'] else 0
        
        result = {}
        for row in active_rows:
            name = labels.get(row['loan_type'], row['loan_type'])
            result[name] = row['total']
            
        if frozen_total > 0:
            result['Congelado'] = frozen_total
            
        conn.close()
        return result

    def get_client_quality_evolution(self, months=6):
        """
        Retorna la evolución histórica de la calidad de clientes (últimos 6 meses).
        Clasificación:
        - Bueno (Verde): Atraso <= 3 días.
        - Regular (Amarillo): Atraso 4-15 días.
        - Riesgoso (Naranja): Atraso > 15 días pero con pagos recientes (<30 días) o parciales.
        - Malo (Rojo): Atraso > 30 días sin pagos recientes.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Obtener todos los datos necesarios en memoria para no hacer queries en loop
        # Clientes
        cursor.execute("SELECT id FROM clients")
        client_ids = [row['id'] for row in cursor.fetchall()]
        
        # Préstamos
        cursor.execute("SELECT id, client_id, status, frozen_date FROM loans")
        loans = cursor.fetchall() # List of Row objects
        
        # Cuotas (Installments)
        cursor.execute("SELECT id, loan_id, due_date, amount FROM installments")
        installments = cursor.fetchall()
        
        # Pagos (Transactions o Installments updates... el sistema guarda pagos en installments.payment_date y amount_paid)
        # Pero para historia necesitamos saber CUANDO se pagó.
        # La tabla installments tiene 'payment_date'.
        # Si hay pagos parciales, installments solo guarda el ultimo payment_date?
        # Revisemos schema: installments tiene `payment_date` y `paid_amount`.
        # Asumiremos que `payment_date` es la fecha del pago (o del último pago parcial).
        # Esto es una limitación si hubo múltiples pagos parciales en fechas distintas para una misma cuota.
        # Pero servirá para la aproximación.
        
        cursor.execute("SELECT loan_id, due_date, payment_date, amount, paid_amount FROM installments")
        all_installments = cursor.fetchall()
        
        conn.close()
        
        # Generar fechas de corte (fin de mes)
        end_date = datetime.now().date()
        dates = []
        curr = end_date.replace(day=1)
        for _ in range(months):
            # Ir al último día del mes anterior
            last_day_prev_month = curr - timedelta(days=1)
            dates.append(last_day_prev_month)
            curr = last_day_prev_month.replace(day=1)
        dates.reverse()
        dates.append(end_date) # Incluir fecha actual
        
        # Estructura de resultados
        history = {
            'fechas': [d.strftime("%Y-%m") for d in dates],
            'Bueno': [],
            'Regular': [],
            'Riesgoso': [],
            'Malo': []
        }
        
        for cut_date in dates:
            cut_date_str = cut_date.strftime("%Y-%m-%d")
            
            counts = {'Bueno': 0, 'Regular': 0, 'Riesgoso': 0, 'Malo': 0}
            
            for client_id in client_ids:
                # Determinar estado del cliente en cut_date
                client_loans = [l for l in loans if l['client_id'] == client_id]
                
                max_overdue_days = 0
                last_payment_date = None
                has_active_loans = False
                
                for loan in client_loans:
                    # Ignorar préstamos creados después de cut_date (no tenemos created_at en loans, usamos start_date si existe o aprox con primera cuota)
                    # Usaremos la fecha de la primera cuota como proxy de inicio
                    loan_installments = [i for i in all_installments if i['loan_id'] == loan['id']]
                    if not loan_installments: continue
                    
                    first_due = min(i['due_date'] for i in loan_installments)
                    if first_due > cut_date_str: continue # Préstamo futuro
                    
                    # Verificar si el préstamo estaba activo/congelado en esa fecha
                    # Si ya estaba pagado antes de cut_date, no cuenta como deuda activa
                    # Chequear si todas las cuotas estaban pagadas antes de cut_date
                    is_fully_paid = True
                    for inst in loan_installments:
                        if inst['payment_date'] and inst['payment_date'] <= cut_date_str:
                            if inst['paid_amount'] >= inst['amount']:
                                continue # Pagada
                        is_fully_paid = False
                        break
                    
                    if is_fully_paid: continue
                    
                    has_active_loans = True
                    
                    # Calcular atraso máximo en este préstamo a la fecha cut_date
                    for inst in loan_installments:
                        due = inst['due_date']
                        if due <= cut_date_str:
                            # Estaba vencida?
                            is_paid_on_time = False
                            if inst['payment_date'] and inst['payment_date'] <= cut_date_str:
                                if inst['paid_amount'] >= inst['amount']:
                                    is_paid_on_time = True
                            
                            if not is_paid_on_time:
                                # Calcular días de atraso
                                due_dt = datetime.strptime(due, "%Y-%m-%d").date()
                                days = (cut_date - due_dt).days
                                if days > max_overdue_days:
                                    max_overdue_days = days
                                    
                        # Track last payment
                        if inst['payment_date'] and inst['payment_date'] <= cut_date_str:
                            pay_dt = datetime.strptime(inst['payment_date'], "%Y-%m-%d").date()
                            if last_payment_date is None or pay_dt > last_payment_date:
                                last_payment_date = pay_dt

                if not has_active_loans:
                    continue # Cliente inactivo en esa fecha (o sin deuda), no lo contamos o lo contamos como Bueno?
                             # Generalmente calidad de cartera es sobre clientes con saldo.
                
                # Clasificar Cliente
                category = 'Bueno'
                days_since_payment = 9999
                if last_payment_date:
                    days_since_payment = (cut_date - last_payment_date).days
                
                if max_overdue_days > 30:
                    if days_since_payment <= 30:
                        category = 'Riesgoso' # Debe mucho pero pagó hace poco
                    else:
                        category = 'Malo' # Debe mucho y no paga
                elif max_overdue_days > 15:
                    category = 'Riesgoso'
                elif max_overdue_days > 3:
                    category = 'Regular'
                else:
                    category = 'Bueno'
                
                counts[category] += 1
            
            history['Bueno'].append(counts['Bueno'])
            history['Regular'].append(counts['Regular'])
            history['Riesgoso'].append(counts['Riesgoso'])
            history['Malo'].append(counts['Malo'])
            
        return history

    def get_profit_loss(self, period='monthly', start_date=None, end_date=None):
        """
        Calcula utilidad vs tiempo.
        Utilidad = Intereses cobrados + Utilidad de Congelados.
        Soporta filtrado por rango de fechas.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Agrupamiento por fecha
        group_format = '%Y-%m'
        if period == 'yearly': group_format = '%Y'
        elif period == 'daily': group_format = '%Y-%m-%d'
        
        # Construir filtro de fecha
        date_filter = "AND i.payment_date IS NOT NULL"
        params = []
        
        if start_date:
            date_filter += " AND i.payment_date >= ?"
            params.append(start_date)
        if end_date:
            date_filter += " AND i.payment_date <= ?"
            params.append(end_date)
            
        cursor.execute(f"""
            SELECT i.payment_date, i.amount_paid, l.loan_type, l.amount as capital, 
                   l.interest_rate, l.status, l.frozen_amount, l.frozen_date
            FROM installments i
            JOIN loans l ON i.loan_id = l.id
            WHERE i.amount_paid > 0 {date_filter}
            ORDER BY i.payment_date
        """, params)
        
        payments = cursor.fetchall()
        
        profits = {} # period -> value
        
        for p in payments:
            # Determinar la clave de agrupación según el periodo
            date_str = p['payment_date']
            if period == 'yearly':
                period_key = date_str[:4]
            elif period == 'monthly':
                period_key = date_str[:7]
            else: # daily
                period_key = date_str[:10]
            
            amount_paid = p['amount_paid']
            loan_type = p['loan_type']
            capital = p['capital']
            
            profit = 0
            
            if p['status'] == 'frozen' and p['frozen_amount']:
                # Lógica Congelados: Proporcional
                if p['frozen_amount'] > 0:
                    margin = (p['frozen_amount'] - capital) / p['frozen_amount']
                    profit = amount_paid * margin
            else:
                # Lógica Normal
                if loan_type == 'rapidiario':
                    rate = p['interest_rate']
                    profit = amount_paid * (rate / (100 + rate))
                else:
                    # Estimación conservadora del 15% para otros préstamos
                    profit = amount_paid * 0.15 
            
            profits[period_key] = profits.get(period_key, 0) + profit
            
        conn.close()
        
        # Ordenar y formatear
        sorted_keys = sorted(profits.keys())
        return sorted_keys, [profits[k] for k in sorted_keys]

    def get_profit_breakdown(self, start_date=None, end_date=None):
        """
        Calcula el desglose de utilidad por tipo de préstamo en un rango de fechas.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Construir filtro de fecha
        date_filter = "AND i.payment_date IS NOT NULL"
        params = []
        
        if start_date:
            date_filter += " AND i.payment_date >= ?"
            params.append(start_date)
        if end_date:
            date_filter += " AND i.payment_date <= ?"
            params.append(end_date)
            
        cursor.execute(f"""
            SELECT i.amount_paid, l.loan_type, l.amount as capital, 
                   l.interest_rate, l.status, l.frozen_amount
            FROM installments i
            JOIN loans l ON i.loan_id = l.id
            WHERE i.amount_paid > 0 {date_filter}
        """, params)
        
        payments = cursor.fetchall()
        conn.close()
        
        breakdown = {'Rapidiario': 0, 'Empeño': 0, 'Bancario': 0, 'Congelado': 0}
        
        for p in payments:
            amount_paid = p['amount_paid']
            loan_type = p['loan_type']
            capital = p['capital']
            status = p['status']
            
            profit = 0
            category = 'Otros'
            
            if status == 'frozen' and p['frozen_amount']:
                 # Lógica Congelados
                if p['frozen_amount'] > 0:
                    margin = (p['frozen_amount'] - capital) / p['frozen_amount']
                    profit = amount_paid * margin
                category = 'Congelado'
            else:
                if loan_type == 'rapidiario':
                    rate = p['interest_rate']
                    profit = amount_paid * (rate / (100 + rate))
                    category = 'Rapidiario'
                elif loan_type == 'empeno':
                    profit = amount_paid * 0.15
                    category = 'Empeño'
                elif loan_type == 'bancario':
                    profit = amount_paid * 0.15
                    category = 'Bancario'
            
            if category in breakdown:
                breakdown[category] += profit
                
        return breakdown

    def get_general_expenses(self, start_date=None, end_date=None):
        """
        Calcula los gastos generales (operativos) en un rango de fechas.
        Se basa en la tabla transactions con type='expense' y category='operational' (o similar).
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT SUM(amount) as total FROM transactions WHERE type = 'expense' AND category != 'loan_disbursement'"
        params = []
        
        if start_date:
            query += " AND date(date) >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date(date) <= ?"
            params.append(end_date)
            
        cursor.execute(query, params)
        row = cursor.fetchone()
        conn.close()
        
        return row['total'] if row and row['total'] else 0

    def get_client_lifetime_value(self, client_id):
        """
        Calcula la utilidad total generada por un cliente específico.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener todos los pagos del cliente
        cursor.execute("""
            SELECT i.amount_paid, l.loan_type, l.amount as capital, 
                   l.interest_rate, l.status, l.frozen_amount
            FROM installments i
            JOIN loans l ON i.loan_id = l.id
            WHERE l.client_id = ? AND i.amount_paid > 0
        """, (client_id,))
        
        payments = cursor.fetchall()
        conn.close()
        
        total_profit = 0
        
        for p in payments:
            amount_paid = p['amount_paid']
            loan_type = p['loan_type']
            capital = p['capital']
            
            profit = 0
            
            if p['status'] == 'frozen' and p['frozen_amount'] and p['frozen_amount'] > 0:
                margin = (p['frozen_amount'] - capital) / p['frozen_amount']
                profit = amount_paid * margin
            else:
                if loan_type == 'rapidiario':
                    rate = p['interest_rate']
                    profit = amount_paid * (rate / (100 + rate))
                else:
                    profit = amount_paid * 0.15
            
            total_profit += profit
            
        return total_profit

    def get_pawn_inventory(self):
        """
        Retorna el inventario de prendas con su valoración y utilidad estimada.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pd.*, l.status as loan_status, l.amount as loan_amount, 
                   l.sale_price, l.sales_expense, l.frozen_amount
            FROM pawn_details pd
            JOIN loans l ON pd.loan_id = l.id
        """)
        
        items = cursor.fetchall()
        conn.close()
        
        inventory = []
        for item in items:
            # Calcular utilidad estimada si se vendió o si se recuperó
            utility = 0
            status = item['loan_status']
            
            # Si el préstamo está pagado, la utilidad es el interés ganado (aprox)
            # Si se vendió (asumimos que hay un estado o flag, o si sale_price > 0)
            if item['sale_price'] and item['sale_price'] > 0:
                # Utilidad = Precio Venta - Préstamo - Gastos
                utility = item['sale_price'] - item['loan_amount'] - (item['sales_expense'] or 0)
            elif status == 'paid':
                # Estimación de utilidad por intereses (ej. 15% del monto)
                utility = item['loan_amount'] * 0.15
            
            inventory.append({
                'id': item['id'],
                'item_type': item['item_type'],
                'brand': item['brand'],
                'characteristics': item['characteristics'],
                'condition': item['condition'],
                'market_value': item['market_value'],
                'loan_status': status,
                'estimated_utility': utility
            })
            
        return inventory


