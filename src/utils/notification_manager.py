
from datetime import date, datetime
import sqlite3
from database import get_db_connection

def generate_due_notifications(user_id=None):
    """
    Generates notifications for installments that are due today or overdue.
    Should be called on application startup or periodically.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today_str = date.today().isoformat()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Get unpaid installments due today (or overdue but active)
    # We join with loans and clients to get details
    # We filter by loan status 'active' or 'overdue' so we don't notify for closed loans
    query = """
        SELECT 
            i.id, i.due_date, i.amount, i.paid_amount,
            l.id as loan_id, l.loan_type, l.status as loan_status,
            c.first_name, c.last_name
        FROM installments i
        JOIN loans l ON i.loan_id = l.id
        JOIN clients c ON l.client_id = c.id
        WHERE i.status != 'paid' 
          AND i.due_date <= ?
          AND l.status IN ('active', 'overdue')
    """
    
    try:
        cursor.execute(query, (today_str,))
        due_items = cursor.fetchall()
        
        count = 0
        for item in due_items:
            # item might be tuple (sqlite) or Row/dict
            if isinstance(item, tuple) or isinstance(item, sqlite3.Row):
                # SQLite Row factory allows index or name, but let's be safe if using default cursor
                # Index mapping based on query SELECT order:
                # 0:i.id, 1:due_date, 2:amount, 3:paid_amount, 4:loan_id, 5:loan_type, 6:loan_status, 7:first, 8:last
                iid, due, amount, paid, lid, ltype, lstatus, fname, lname = item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8]
            else:
                # Dictionary (Postgres wrapper sometimes)
                iid = item['id']
                due = item['due_date']
                amount = item['amount']
                paid = item['paid_amount']
                lid = item['loan_id']
                ltype = item['loan_type']
                lstatus = item['loan_status']
                fname = item['first_name']
                lname = item['last_name']

            # Format Message
            # "Vence HOY: Juan Perez (Rapidiario) - Cuota S/ 50.00"
            # or "Venció el YYYY-MM-DD: ..."
            
            is_today = (str(due) == today_str)
            prefix = "VENCE HOY" if is_today else f"VENCIÓ EL {due}"
            
            # Identify the notification uniquely to avoid duplicates for the same day
            # We want to remind every day? Or just once?
            # User says: "cada dia que venza el dia de pago ... notificar" -> implies notify daily until paid?
            # "ese dia actualice manually"
            # Let's notify IF not already notified TODAY about this item.
            
            desc = f"{prefix}: {fname} {lname} ({ltype.capitalize()}) - Cuota S/ {amount:.2f}"
            
            # Check if notification exists created TODAY for this description
            # SQLite: strftime('%Y-%m-%d', created_at)
            # Postgres: created_at::date
            # Safe way: check substring "YYYY-MM-DD" match in created_at or verify via a dedicated key?
            # We can use the description text + date check.
            
            check_sql = """
                SELECT id FROM notifications 
                WHERE description = ? 
                  AND date(created_at) = date('now')
            """
            # SQLITE uses date('now'). Postgres uses CURRENT_DATE.
            # Compatibility hack: using LIKE for date
            
            cursor.execute("SELECT id FROM notifications WHERE description = ? AND created_at LIKE ?", (desc, f"{today_str}%"))
            existing = cursor.fetchone()
            
            if not existing:
                cursor.execute("""
                    INSERT INTO notifications (description, notify_date, created_by, is_done, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (desc, now_str, user_id, 0, now_str))
                count += 1
                
        conn.commit()
        if count > 0:
            print(f"Generated {count} new payment reminders.")
            
    except Exception as e:
        print(f"Error generating notifications: {e}")
    finally:
        conn.close()
