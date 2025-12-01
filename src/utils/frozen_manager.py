import sqlite3
from datetime import datetime, timedelta
from database import get_db_connection

class FrozenManager:
    def __init__(self, db_path=None):
        self.db_path = db_path

    def get_connection(self):
        if self.db_path:
            return sqlite3.connect(self.db_path)
        return get_db_connection()

    def refinanciar_rapidiario(self, loan_id, current_date=None):
        """
        Refinancia un préstamo Rapidiario.
        - Máximo 3 refinanciamientos.
        - Tasa de interés 8%.
        - Nuevo plazo de 30 días.
        """
        if current_date is None:
            current_date = datetime.now().date()
            
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Obtener info del préstamo
            cursor.execute("SELECT * FROM loans WHERE id = ?", (loan_id,))
            loan = cursor.fetchone()
            
            if not loan:
                return {'success': False, 'message': 'Préstamo no encontrado'}
                
            # Verificar tipo
            if loan['loan_type'] != 'rapidiario':
                return {'success': False, 'message': 'Solo se pueden refinanciar préstamos Rapidiario'}
                
            # Verificar límite de refinanciamientos
            refinance_count = loan['refinance_count'] if loan['refinance_count'] else 0
            if refinance_count >= 3:
                return {'success': False, 'message': 'Límite de refinanciamientos (3) alcanzado. Debe congelar el préstamo.'}
            
            # Calcular nuevos valores
            new_interest_rate = 8.0
            new_start_date = current_date
            new_end_date = current_date + timedelta(days=30)
            
            # Actualizar préstamo
            cursor.execute("""
                UPDATE loans 
                SET refinance_count = refinance_count + 1,
                    interest_rate = ?,
                    start_date = ?,
                    end_date = ?,
                    status = 'active',
                    due_date = ?
                WHERE id = ?
            """, (new_interest_rate, new_start_date, new_end_date, new_end_date, loan_id))
            
            conn.commit()
            return {
                'success': True, 
                'message': f'Préstamo refinanciado exitosamente (Refinanciamiento {refinance_count + 1}/3)',
                'new_due_date': new_end_date
            }
            
        except Exception as e:
            conn.rollback()
            return {'success': False, 'message': str(e)}
        finally:
            conn.close()

    def congelar_prestamo(self, loan_id, admin_fee=0, reason="Mora excesiva"):
        """
        Congela un préstamo.
        - Cambia estado a 'frozen'.
        - Establece fecha de congelamiento.
        - Calcula monto congelado.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM loans WHERE id = ?", (loan_id,))
            loan = cursor.fetchone()
            
            if not loan:
                return {'success': False, 'message': 'Préstamo no encontrado'}
            
            # Calcular monto pendiente (simplificado por ahora, idealmente sumar cuotas pendientes)
            # Aquí asumimos que el monto congelado es el monto original + intereses pendientes + mora
            # Por ahora usaremos el monto original + admin_fee como base
            frozen_amount = loan['amount'] + admin_fee 
            
            current_date = datetime.now().date()
            
            cursor.execute("""
                UPDATE loans 
                SET status = 'frozen',
                    frozen_date = ?,
                    admin_fee = ?,
                    frozen_amount = ?
                WHERE id = ?
            """, (current_date, admin_fee, frozen_amount, loan_id))
            
            conn.commit()
            return {'success': True, 'message': 'Préstamo congelado exitosamente'}
            
        except Exception as e:
            conn.rollback()
            return {'success': False, 'message': str(e)}
        finally:
            conn.close()

    def verificar_mora_automatica(self):
        """
        Verifica préstamos vencidos y sugiere o aplica congelamiento.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        results = []
        current_date = datetime.now().date()
        
        try:
            # Buscar préstamos activos vencidos
            cursor.execute("SELECT * FROM loans WHERE status = 'active' AND due_date < ?", (current_date,))
            overdue_loans = cursor.fetchall()
            
            for loan in overdue_loans:
                days_overdue = (current_date - datetime.strptime(loan['due_date'], '%Y-%m-%d').date()).days
                
                if loan['loan_type'] == 'rapidiario':
                    # Rapidiario se congela si pasa cierto tiempo o intentos fallidos?
                    # Por ahora solo reportamos
                    if days_overdue > 30:
                         results.append({'loan_id': loan['id'], 'action': 'suggest_freeze', 'reason': f'{days_overdue} días de mora'})
                         
                elif loan['loan_type'] in ['empeno', 'bancario']:
                    # Regla 60/90 días
                    if days_overdue > 60:
                        results.append({'loan_id': loan['id'], 'action': 'suggest_freeze', 'reason': f'{days_overdue} días de mora (Regla 60 días)'})
                        
        except Exception as e:
            print(f"Error verificando mora: {e}")
        finally:
            conn.close()
            
        return results
