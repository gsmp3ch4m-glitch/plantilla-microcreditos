import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from database import get_db_connection, log_action
from datetime import datetime
from utils.pdf_generator import PDFGenerator
from utils.settings_manager import get_setting
import os
import subprocess
import platform
import sqlite3

class CashWindow(tk.Toplevel):
    def __init__(self, parent, user_data):
        super().__init__(parent)
        self.parent = parent
        self.user_data = user_data
        self.title("Caja - Sistema de Gestión")
        self.geometry("1200x700")
        self.configure(bg='#f5f5f5')
        
        self.current_session = None
        self.check_and_create_session()
        
    def check_and_create_session(self):
        """Check for active session or prompt to create one"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cash_sessions WHERE user_id = ? AND status = 'open' ORDER BY opening_date DESC LIMIT 1", 
                      (self.user_data['id'],))
        session = cursor.fetchone()
        conn.close()
        
        if session:
            self.current_session = dict(session)
            self.create_widgets()
        else:
            # Prompt for opening balance
            # Show "Open Session" screen
            self.show_open_session_screen()
    
    def prompt_opening_balance(self):
        """Show dialog to open cash session"""
        dialog = tk.Toplevel(self)
        dialog.title("Apertura de Caja")
        dialog.geometry("400x200")
        dialog.transient(self)
        dialog.grab_set()
        
        tk.Label(dialog, text="Apertura de Caja", font=("Segoe UI", 16, "bold")).pack(pady=20)
        
        tk.Label(dialog, text="Dinero en Caja:", font=("Segoe UI", 10)).pack(pady=(10,0))
        entry_cash = tk.Entry(dialog, font=("Segoe UI", 12), width=20)
        entry_cash.pack(pady=5)
        entry_cash.focus()
        
        def save_opening():
            try:
                val = entry_cash.get().strip()
                if not val:
                    messagebox.showerror("Error", "Por favor ingrese un monto")
                    return
                    
                opening_balance = float(val)
                
                # Get company initial cash from settings (configured by admin)
                try:
                    company_cash_str = get_setting('company_initial_cash')
                    company_cash = float(company_cash_str) if company_cash_str else 0.0
                except ValueError:
                    company_cash = 0.0
                
                # For admin, add company cash to opening balance
                if self.user_data.get('role') == 'admin' and company_cash > 0:
                    opening_balance += company_cash
                
                # --- Validation against previous session ---
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT closing_balance 
                    FROM cash_sessions 
                    WHERE user_id = ? AND status = 'closed' 
                    ORDER BY closing_date DESC LIMIT 1
                """, (self.user_data['id'],))
                last_session = cursor.fetchone()
                
                observation = None
                
                if last_session:
                    last_closing = last_session['closing_balance']
                    # Compare with tolerance for float precision
                    if abs(opening_balance - last_closing) > 0.01:
                        # Ask for observation
                        obs_dialog = tk.Toplevel(dialog)
                        obs_dialog.title("Observación Requerida")
                        obs_dialog.geometry("400x250")
                        obs_dialog.transient(dialog)
                        obs_dialog.grab_set()
                        
                        tk.Label(obs_dialog, text="⚠️ Discrepancia Detectada", font=("Segoe UI", 12, "bold"), fg="#F44336").pack(pady=10)
                        tk.Label(obs_dialog, text=f"Monto ingresado: S/ {opening_balance:.2f}").pack()
                        tk.Label(obs_dialog, text=f"Cierre anterior: S/ {last_closing:.2f}").pack()
                        tk.Label(obs_dialog, text="Ingrese el motivo de la diferencia:", font=("Segoe UI", 10)).pack(pady=(10,5))
                        
                        txt_obs = tk.Text(obs_dialog, height=3, width=40, font=("Segoe UI", 10))
                        txt_obs.pack(pady=5)
                        
                        obs_var = tk.StringVar()
                        
                        def confirm_obs():
                            obs = txt_obs.get("1.0", tk.END).strip()
                            if not obs:
                                messagebox.showerror("Error", "Debe ingresar una observación")
                                return
                            obs_var.set(obs)
                            obs_dialog.destroy()
                            
                        tk.Button(obs_dialog, text="Confirmar y Abrir", command=confirm_obs,
                                 bg="#F44336", fg="white", font=("Segoe UI", 10, "bold")).pack(pady=10)
                        
                        dialog.wait_window(obs_dialog)
                        
                        observation = obs_var.get()
                        if not observation: # User closed dialog without confirming
                            conn.close()
                            return

                # Save session
                cursor.execute("""
                    INSERT INTO cash_sessions (user_id, opening_balance, status, observation)
                    VALUES (?, ?, 'open', ?)
                """, (self.user_data['id'], opening_balance, observation))
                session_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                # Reload session
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM cash_sessions WHERE id = ?", (session_id,))
                self.current_session = dict(cursor.fetchone())
                conn.close()
                
                dialog.destroy()
                self.create_widgets()
            except ValueError:
                messagebox.showerror("Error", "El monto ingresado no es válido. Use punto (.) para decimales.")
            except Exception as e:
                messagebox.showerror("Error", f"Error inesperado: {e}")
        
        tk.Button(dialog, text="🔓 ABRIR CAJA", command=save_opening, bg="#4CAF50", fg="white", 
                 font=("Segoe UI", 14, "bold"), padx=40, pady=15, cursor='hand2').pack(pady=20)

    def show_open_session_screen(self):
        """Show screen to open a new cash session"""
        for widget in self.winfo_children():
            widget.destroy()
            
        frame = tk.Frame(self, bg='#f5f5f5')
        frame.pack(expand=True, fill='both')
        
        tk.Label(frame, text="🔒 Caja Cerrada", font=("Segoe UI", 24, "bold"), bg='#f5f5f5', fg='#757575').pack(pady=(150, 20))
        tk.Label(frame, text="Debe realizar la apertura de caja para comenzar.", font=("Segoe UI", 12), bg='#f5f5f5', fg='#757575').pack(pady=(0, 30))
        
        tk.Button(frame, text="🔓 APERTURAR CAJA", command=self.prompt_opening_balance,
                 bg="#4CAF50", fg="white", font=("Segoe UI", 14, "bold"), padx=30, pady=15, cursor='hand2').pack()
    
    def create_widgets(self):
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()
        
        if not self.current_session:
            return
        
        # Header
        header = tk.Frame(self, bg="#2196F3", height=120)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="💰 Caja", font=("Segoe UI", 20, "bold"), bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=20, pady=20)
        
        # Balance display (Container for 3 balances)
        balance_container = tk.Frame(header, bg="#2196F3")
        balance_container.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # 1. Main Cash
        frame_main = tk.Frame(balance_container, bg="#1976D2", relief=tk.RAISED, bd=1, padx=10, pady=5)
        frame_main.pack(side=tk.LEFT, padx=5)
        tk.Label(frame_main, text="Caja Principal", font=("Segoe UI", 9), bg="#1976D2", fg="#E3F2FD").pack()
        self.lbl_balance = tk.Label(frame_main, text="S/ 0.00", font=("Segoe UI", 16, "bold"), bg="#1976D2", fg="#FFF")
        self.lbl_balance.pack()
        
        # 2. Petty Cash
        frame_petty = tk.Frame(balance_container, bg="#0288D1", relief=tk.RAISED, bd=1, padx=10, pady=5)
        frame_petty.pack(side=tk.LEFT, padx=5)
        tk.Label(frame_petty, text="Caja Chica", font=("Segoe UI", 9), bg="#0288D1", fg="#E3F2FD").pack()
        self.lbl_petty = tk.Label(frame_petty, text="S/ 0.00", font=("Segoe UI", 16, "bold"), bg="#0288D1", fg="#FFF")
        self.lbl_petty.pack()
        
        # 3. Total
        frame_total = tk.Frame(balance_container, bg="#01579B", relief=tk.RAISED, bd=1, padx=10, pady=5)
        frame_total.pack(side=tk.LEFT, padx=5)
        tk.Label(frame_total, text="Total Efectivo", font=("Segoe UI", 9), bg="#01579B", fg="#E3F2FD").pack()
        self.lbl_total = tk.Label(frame_total, text="S/ 0.00", font=("Segoe UI", 16, "bold"), bg="#01579B", fg="#FFF")
        self.lbl_total.pack()
        
        # Notebook (Tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Movimientos
        self.tab_movements = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.tab_movements, text="📋 Movimientos")
        self.setup_movements_tab()
        
        # Tab 2: Cierre
        self.tab_closing = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.tab_closing, text="🔒 Cierre de Caja")
        self.setup_closing_tab()
        
        self.update_balance()
    
    def setup_movements_tab(self):
        # Main container
        container = tk.Frame(self.tab_movements, bg='white')
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Actions
        left_panel = tk.Frame(container, bg='#f9f9f9', width=350, relief=tk.RAISED, bd=1)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10))
        left_panel.pack_propagate(False)
        
        tk.Label(left_panel, text="Registrar Movimiento", font=("Segoe UI", 14, "bold"), bg='#f9f9f9').pack(pady=15)
        
        # Income buttons
        tk.Label(left_panel, text="INGRESOS", font=("Segoe UI", 10, "bold"), bg='#f9f9f9', fg='#4CAF50').pack(pady=(10,5))
        
        tk.Button(left_panel, text="💵 Pago de Préstamo", command=self.open_loan_payment_form,
                 bg='#4CAF50', fg='white', font=("Segoe UI", 10), width=25, pady=8).pack(pady=5, padx=15)
        
        tk.Button(left_panel, text="🏷️ Remate / Otros Ingresos", command=self.open_other_income_form,
                 bg='#2196F3', fg='white', font=("Segoe UI", 10), width=25, pady=8).pack(pady=5, padx=15)
                 
        tk.Button(left_panel, text="📥 Retirar de Caja Chica", command=self.withdraw_from_petty_cash,
                 bg='#009688', fg='white', font=("Segoe UI", 10), width=25, pady=8).pack(pady=5, padx=15)
        
        # Expense buttons
        tk.Label(left_panel, text="EGRESOS", font=("Segoe UI", 10, "bold"), bg='#f9f9f9', fg='#F44336').pack(pady=(20,5))
        
        tk.Button(left_panel, text="🏢 Gastos Operativos", command=self.open_expense_form,
                 bg='#F44336', fg='white', font=("Segoe UI", 10), width=25, pady=8).pack(pady=5, padx=15)
        
        tk.Button(left_panel, text="💼 Desembolso de Préstamo", command=self.open_disbursement_form,
                 bg='#FF9800', fg='white', font=("Segoe UI", 10), width=25, pady=8).pack(pady=5, padx=15)
                 
        tk.Button(left_panel, text="📤 Guardar en Caja Chica", command=self.deposit_to_petty_cash,
                 bg='#795548', fg='white', font=("Segoe UI", 10), width=25, pady=8).pack(pady=5, padx=15)
        
        # Right panel - Transaction list
        right_panel = tk.Frame(container, bg='white')
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(right_panel, text="Movimientos del Día", font=("Segoe UI", 14, "bold"), bg='white').pack(pady=10)
        
        # Treeview
        columns = ("hora", "tipo", "categoria", "metodo", "monto", "descripcion")
        self.tree = ttk.Treeview(right_panel, columns=columns, show="headings", height=20)
        
        self.tree.heading("hora", text="Hora")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("categoria", text="Categoría")
        self.tree.heading("metodo", text="Método Pago")
        self.tree.heading("monto", text="Monto")
        self.tree.heading("descripcion", text="Descripción")
        
        self.tree.column("hora", width=80)
        self.tree.column("tipo", width=80)
        self.tree.column("categoria", width=120)
        self.tree.column("metodo", width=100)
        self.tree.column("monto", width=100)
        self.tree.column("descripcion", width=250)
        
        scrollbar = ttk.Scrollbar(right_panel, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.load_transactions()
    
    def setup_closing_tab(self):
        container = tk.Frame(self.tab_closing, bg='white')
        container.pack(fill=tk.BOTH, expand=True, padx=50, pady=30)
        
        tk.Label(container, text="Cierre de Caja", font=("Segoe UI", 18, "bold"), bg='white').pack(pady=20)
        
        # Summary frame
        summary = tk.Frame(container, bg='#f5f5f5', relief=tk.RAISED, bd=2)
        summary.pack(fill=tk.X, pady=20)
        
        tk.Label(summary, text="Resumen del Día", font=("Segoe UI", 14, "bold"), bg='#f5f5f5').pack(pady=15)
        
        self.lbl_opening = tk.Label(summary, text="Apertura: S/ 0.00", font=("Segoe UI", 12), bg='#f5f5f5')
        self.lbl_opening.pack(pady=5)
        
        self.lbl_income = tk.Label(summary, text="Ingresos: S/ 0.00", font=("Segoe UI", 12), bg='#f5f5f5', fg='#4CAF50')
        self.lbl_income.pack(pady=5)
        
        self.lbl_expense = tk.Label(summary, text="Egresos: S/ 0.00", font=("Segoe UI", 12), bg='#f5f5f5', fg='#F44336')
        self.lbl_expense.pack(pady=5)
        
        tk.Frame(summary, bg='#ddd', height=2).pack(fill=tk.X, padx=20, pady=10)
        
        self.lbl_expected = tk.Label(summary, text="Saldo Esperado: S/ 0.00", font=("Segoe UI", 14, "bold"), bg='#f5f5f5')
        self.lbl_expected.pack(pady=10)
        
        # Close button
        tk.Button(container, text="🔒 Cerrar Caja y Generar Reporte", command=self.close_cash_register,
                 bg='#4CAF50', fg='white', font=("Segoe UI", 12, "bold"), padx=30, pady=15).pack(pady=30)
        
        self.update_closing_summary()
    
    def load_transactions(self):
        """Load today's transactions for current session"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT * FROM transactions 
            WHERE cash_session_id = ? AND date(date) = ?
            ORDER BY date DESC
        """, (self.current_session['id'], today))
        
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            hora = row['date'][11:16] if len(row['date']) > 16 else ""
            tipo = "Ingreso" if row['type'] == 'income' else "Egreso"
            tag = "income" if row['type'] == 'income' else "expense"
            
            self.tree.insert("", 0, values=(
                hora,
                tipo,
                row['category'],
                row['payment_method'] or 'N/A',
                f"S/ {row['amount']:.2f}",
                row['description']
            ), tags=(tag,))
        
        self.tree.tag_configure("income", foreground="#4CAF50")
        self.tree.tag_configure("expense", foreground="#F44336")
    
    def update_balance(self):
        """Calculate and update current balance"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
            FROM transactions
            WHERE cash_session_id = ?
        """, (self.current_session['id'],))
        
        result = cursor.fetchone()
        conn.close()
        
        income = result['income'] or 0
        expense = result['expense'] or 0
        balance = self.current_session['opening_balance'] + income - expense
        
        self.lbl_balance.config(text=f"S/ {balance:,.2f}")
        
        # Update Petty Cash
        petty_cash = float(get_setting('petty_cash_balance') or '0')
        self.lbl_petty.config(text=f"S/ {petty_cash:,.2f}")
        
        # Update Total
        total = balance + petty_cash
        self.lbl_total.config(text=f"S/ {total:,.2f}")

    def deposit_to_petty_cash(self):
        """Move money from Main Cash to Petty Cash"""
        dialog = tk.Toplevel(self)
        dialog.title("Guardar en Caja Chica")
        dialog.geometry("350x250")
        
        tk.Label(dialog, text="Monto a Guardar:", font=("Segoe UI", 11)).pack(pady=(20,5))
        entry = tk.Entry(dialog, font=("Segoe UI", 12))
        entry.pack(pady=5)
        
        def save():
            try:
                amount = float(entry.get())
                if amount <= 0: raise ValueError
                
                # Check if enough balance
                current_balance = float(self.lbl_balance.cget("text").replace("S/ ", "").replace(",", ""))
                if amount > current_balance:
                    messagebox.showerror("Error", "Saldo insuficiente en Caja Principal")
                    return
                
                # 1. Register Expense in Session
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO transactions (type, category, amount, description, payment_method, cash_session_id)
                    VALUES ('expense', 'petty_cash_deposit', ?, 'Transferencia a Caja Chica', 'efectivo', ?)
                """, (amount, self.current_session['id']))
                conn.commit()
                conn.close()
                
                # 2. Update Petty Cash Balance in Settings
                from utils.settings_manager import update_setting, get_setting
                current_petty = float(get_setting('petty_cash_balance') or '0')
                update_setting('petty_cash_balance', str(current_petty + amount))
                
                messagebox.showinfo("Éxito", "Dinero guardado en Caja Chica")
                self.refresh_data()
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "Monto inválido")
        
        tk.Button(dialog, text="Guardar", command=save, bg="#795548", fg="white", font=("Segoe UI", 10, "bold"), padx=20).pack(pady=20)

    def withdraw_from_petty_cash(self):
        """Move money from Petty Cash to Main Cash"""
        dialog = tk.Toplevel(self)
        dialog.title("Retirar de Caja Chica")
        dialog.geometry("350x250")
        
        tk.Label(dialog, text="Monto a Retirar:", font=("Segoe UI", 11)).pack(pady=(20,5))
        entry = tk.Entry(dialog, font=("Segoe UI", 12))
        entry.pack(pady=5)
        
        def save():
            try:
                amount = float(entry.get())
                if amount <= 0: raise ValueError
                
                # Check if enough balance in Petty Cash
                from utils.settings_manager import get_setting, update_setting
                current_petty = float(get_setting('petty_cash_balance') or '0')
                
                if amount > current_petty:
                    messagebox.showerror("Error", f"Saldo insuficiente en Caja Chica (Disp: {current_petty:.2f})")
                    return
                
                # 1. Register Income in Session
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO transactions (type, category, amount, description, payment_method, cash_session_id)
                    VALUES ('income', 'petty_cash_withdrawal', ?, 'Retiro de Caja Chica', 'efectivo', ?)
                """, (amount, self.current_session['id']))
                conn.commit()
                conn.close()
                
                # 2. Update Petty Cash Balance
                update_setting('petty_cash_balance', str(current_petty - amount))
                
                messagebox.showinfo("Éxito", "Dinero retirado de Caja Chica")
                self.refresh_data()
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "Monto inválido")
        
        tk.Button(dialog, text="Retirar", command=save, bg="#009688", fg="white", font=("Segoe UI", 10, "bold"), padx=20).pack(pady=20)
    
    def update_closing_summary(self):
        """Update closing tab summary"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
            FROM transactions
            WHERE cash_session_id = ? AND date(date) = ?
        """, (self.current_session['id'], today))
        
        result = cursor.fetchone()
        conn.close()
        
        opening = self.current_session['opening_balance']
        income = result['income'] or 0
        expense = result['expense'] or 0
        expected = opening + income - expense
        
        self.lbl_opening.config(text=f"Apertura: S/ {opening:,.2f}")
        self.lbl_income.config(text=f"Ingresos: S/ {income:,.2f}")
        self.lbl_expense.config(text=f"Egresos: S/ {expense:,.2f}")
        self.lbl_expected.config(text=f"Saldo Esperado: S/ {expected:,.2f}")
    
    def open_loan_payment_form(self):
        LoanPaymentForm(self, self.current_session['id'], self.refresh_data)
    
    def open_other_income_form(self):
        OtherIncomeForm(self, self.current_session['id'], self.refresh_data)
    
    def open_expense_form(self):
        ExpenseForm(self, self.current_session['id'], self.refresh_data)
    
    def open_disbursement_form(self):
        DisbursementForm(self, self.current_session['id'], self.refresh_data)
    
    def refresh_data(self):
        """Refresh all data displays"""
        self.load_transactions()
        self.update_balance()
        self.update_closing_summary()
    
    def close_cash_register(self):
        """Close cash session and generate report"""
        if not messagebox.askyesno("Confirmar", "¿Desea cerrar la caja y generar el reporte?"):
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all transactions for this session
        cursor.execute("SELECT * FROM transactions WHERE cash_session_id = ? ORDER BY date ASC", 
                      (self.current_session['id'],))
        transactions = cursor.fetchall()
        
        # Calculate final balance
        income = sum(t['amount'] for t in transactions if t['type'] == 'income')
        expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
        closing_balance = self.current_session['opening_balance'] + income - expense
        
        # Update session
        cursor.execute("""
            UPDATE cash_sessions 
            SET status = 'closed', closing_balance = ?, closing_date = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (closing_balance, self.current_session['id']))
        
        conn.commit()
        conn.close()
        
        # Generate PDF
        try:
            data = {
                'income': income,
                'expense': expense,
                'balance': closing_balance,
                'details': transactions,
                'user': self.user_data.get('full_name', 'Usuario')
            }
            
            generator = PDFGenerator()
            filepath = generator.generate_cash_report(data)
            
            messagebox.showinfo("Éxito", f"Caja cerrada. Reporte generado:\n{filepath}")
            
            # Open PDF
            if platform.system() == 'Windows':
                os.startfile(filepath)
            
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar reporte: {e}")


# ===== FORM DIALOGS =====

class LoanPaymentForm(tk.Toplevel):
    def __init__(self, parent, session_id, callback):
        super().__init__(parent)
        self.session_id = session_id
        self.callback = callback
        self.title("Registrar Pago")
        self.geometry("550x650")
        self.configure(bg='white')
        self.transient(parent)
        self.grab_set()
        
        self.create_widgets()
    
    def create_widgets(self):
        # Header
        header_frame = tk.Frame(self, bg="#4CAF50", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="💵 Registrar Pago", font=("Segoe UI", 20, "bold"), bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=20)
        
        # Main Container
        main_container = tk.Frame(self, bg='white', padx=30, pady=20)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 1. Client Search Section
        tk.Label(main_container, text="1. Buscar Cliente", font=("Segoe UI", 11, "bold"), bg='white', fg='#555').pack(anchor='w')
        
        search_frame = tk.Frame(main_container, bg='white')
        search_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.entry_search = tk.Entry(search_frame, font=("Segoe UI", 12), relief=tk.SOLID, bd=1)
        self.entry_search.pack(fill=tk.X, ipady=5)
        self.entry_search.bind('<KeyRelease>', self.search_clients)
        
        self.listbox_clients = tk.Listbox(main_container, height=3, font=("Segoe UI", 10), relief=tk.SOLID, bd=1)
        self.listbox_clients.pack(fill=tk.X, pady=(0, 15))
        self.listbox_clients.bind('<<ListboxSelect>>', self.load_client_loans)
        
        # 2. Loan Selection
        tk.Label(main_container, text="2. Seleccionar Préstamo", font=("Segoe UI", 11, "bold"), bg='white', fg='#555').pack(anchor='w')
        
        self.combo_loan = ttk.Combobox(main_container, state='readonly', font=("Segoe UI", 11))
        self.combo_loan.pack(fill=tk.X, pady=(5, 15), ipady=3)
        self.combo_loan.bind('<<ComboboxSelected>>', self.on_loan_select)
        
        # Pawn Options (Dynamic)
        self.frame_pawn_options = tk.Frame(main_container, bg='#F5F5F5', padx=15, pady=10, relief=tk.RIDGE, bd=1)
        
        tk.Label(self.frame_pawn_options, text="Opciones de Empeño", font=("Segoe UI", 10, "bold"), bg='#F5F5F5', fg='#333').pack(anchor='w', pady=(0,5))
        
        tk.Label(self.frame_pawn_options, text="Tipo de Pago:", bg='#F5F5F5').pack(anchor='w')
        self.combo_payment_type = ttk.Combobox(self.frame_pawn_options, values=["Pago Completo", "Solo Interés (Refinanciar)"], 
                                             state='readonly', font=("Segoe UI", 10))
        self.combo_payment_type.current(0)
        self.combo_payment_type.pack(fill=tk.X, pady=2)
        self.combo_payment_type.bind('<<ComboboxSelected>>', self.calculate_total)
        
        self.var_mos = tk.BooleanVar(value=True)
        self.chk_mos = tk.Checkbutton(self.frame_pawn_options, text="Cobrar MOS (0.1%)", variable=self.var_mos, 
                                    command=self.calculate_total, font=("Segoe UI", 10), bg='#F5F5F5')
        self.chk_mos.pack(anchor='w', pady=5)
        
        # 3. Payment Details
        tk.Label(main_container, text="3. Detalles del Pago", font=("Segoe UI", 11, "bold"), bg='white', fg='#555').pack(anchor='w')
        
        details_frame = tk.Frame(main_container, bg='white')
        details_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Amount
        tk.Label(details_frame, text="Monto a Pagar (S/):", font=("Segoe UI", 10), bg='white').grid(row=0, column=0, sticky='w', pady=5)
        self.entry_amount = tk.Entry(details_frame, font=("Segoe UI", 12, "bold"), width=15, justify='right', relief=tk.SOLID, bd=1)
        self.entry_amount.grid(row=0, column=1, sticky='e', padx=(10,0), pady=5)
        
        # Method
        tk.Label(details_frame, text="Método de Pago:", font=("Segoe UI", 10), bg='white').grid(row=1, column=0, sticky='w', pady=5)
        self.combo_method = ttk.Combobox(details_frame, values=["efectivo", "yape", "deposito"], 
                                         state='readonly', font=("Segoe UI", 10), width=13)
        self.combo_method.current(0)
        self.combo_method.grid(row=1, column=1, sticky='e', padx=(10,0), pady=5)
        
        # Footer Action Button
        footer_frame = tk.Frame(self, bg='#f0f0f0', height=80)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        tk.Button(footer_frame, text="✅ REGISTRAR PAGO", command=self.save, 
                 bg="#4CAF50", fg="white", font=("Segoe UI", 12, "bold"), 
                 relief=tk.FLAT, cursor='hand2', padx=30, pady=10).pack(pady=15)
        
        self.clients = []
        self.loans = []
        self.selected_loan = None
        self.selected_client = None

    def on_loan_select(self, event=None):
        idx = self.combo_loan.current()
        if idx >= 0:
            self.selected_loan = self.loans[idx]
            
            # Show/Hide Pawn Options
            if self.selected_loan['loan_type'] == 'empeno':
                self.frame_pawn_options.pack(after=self.combo_loan, pady=5)
                self.calculate_total()
            else:
                self.frame_pawn_options.pack_forget()
                self.entry_amount.delete(0, tk.END)

    def calculate_total(self, event=None):
        if not self.selected_loan: return
        
        loan = self.selected_loan
        payment_type = self.combo_payment_type.get()
        
        # Basic logic: 
        # If Refinance: Amount = Interest
        # If Full: Amount = Total Due (Capital + Interest)
        # MOS: 0.1% of Capital
        
        # Note: This is a simplified calculation. Ideally, we should fetch the exact due amount from DB logic.
        # Assuming loan['amount'] is Capital. 
        # We need interest rate. For now, let's assume we can get it or calculate it.
        # Since we don't have the full interest logic here, we might need to rely on manual input or fetch more data.
        # But for now, let's implement the MOS logic at least.
        
        capital = loan['amount']
        mos_amount = capital * 0.001 if self.var_mos.get() else 0
        
        # Placeholder for interest calculation (User might need to input it or we fetch it)
        # For now, we'll just pre-fill with MOS if Refinance, or leave empty for user to fill.
        # If user wants auto-calc, we need the interest rate.
        
        current_val = self.entry_amount.get()
        if not current_val: current_val = "0"
        
        try:
            amount = float(current_val)
        except:
            amount = 0
            
        # If just toggling MOS, we might want to update the field?
        # Let's just show a label with the MOS amount for reference
        self.chk_mos.config(text=f"Cobrar MOS (0.1% = S/ {mos_amount:.2f})")

    def search_clients(self, event=None):
        query = self.entry_search.get()
        if len(query) < 2:
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, dni, first_name, last_name 
            FROM clients 
            WHERE dni LIKE ? OR first_name LIKE ? OR last_name LIKE ?
            LIMIT 10
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))
        
        self.clients = cursor.fetchall()
        conn.close()
        
        self.listbox_clients.delete(0, tk.END)
        for client in self.clients:
            self.listbox_clients.insert(tk.END, f"{client['dni']} - {client['first_name']} {client['last_name']}")
    
    def load_client_loans(self, event=None):
        selection = self.listbox_clients.curselection()
        if not selection:
            return
        
        self.selected_client = self.clients[selection[0]]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, loan_type, amount, status, start_date, interest_rate 
            FROM loans 
            WHERE client_id = ? AND status IN ('active', 'overdue')
        """, (self.selected_client['id'],))
        
        self.loans = cursor.fetchall()
        conn.close()
        
        loan_options = [f"ID:{l['id']} - {l['loan_type'].upper()} - S/{l['amount']:.2f} - {l['status']}" 
                       for l in self.loans]
        self.combo_loan['values'] = loan_options
        if loan_options:
            self.combo_loan.current(0)
            self.on_loan_select()
    
    def save(self):
        if not self.selected_loan:
            messagebox.showerror("Error", "Seleccione un préstamo")
            return
            
        if not self.selected_client:
            messagebox.showerror("Error", "Error interno: Cliente no seleccionado")
            return
        
        try:
            amount = float(self.entry_amount.get())
            loan = self.selected_loan
            client = self.selected_client
            payment_method = self.combo_method.get()
            
            is_pawn = loan['loan_type'] == 'empeno'
            is_refinance = is_pawn and self.combo_payment_type.get() == "Solo Interés (Refinanciar)"
            has_mos = is_pawn and self.var_mos.get()
            
            # MOS Authorization
            if is_pawn and not has_mos:
                # Require Admin or Password
                # For simplicity, let's just ask for a password if not admin
                user_role = self.master.user_data.get('role')
                if user_role != 'admin':
                    pwd = tk.simpledialog.askstring("Autorización", "Ingrese contraseña de administrador para omitir MOS:", show='*')
                    if pwd != "admin123": # Hardcoded for now, should check DB
                        messagebox.showerror("Error", "Contraseña incorrecta")
                        return

            conn = get_db_connection()
            cursor = conn.cursor()
            
            desc = f"Pago préstamo #{loan['id']}"
            if is_refinance:
                desc += " (Refinanciación)"
                # Update Loan Start Date to Today (Extend period)
                cursor.execute("UPDATE loans SET start_date = DATE('now') WHERE id = ?", (loan['id'],))
            
            if has_mos:
                desc += " + MOS"
            
            # Record transaction
            cursor.execute("""
                INSERT INTO transactions (type, category, amount, description, payment_method, cash_session_id, loan_id)
                VALUES ('income', 'payment', ?, ?, ?, ?, ?)
            """, (amount, desc, payment_method, self.session_id, loan['id']))
            
            transaction_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            # Show receipt dialog
            self.show_receipt_dialog(transaction_id, amount, payment_method, client, loan, desc)
            
            self.callback()
            self.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Monto inválido")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def show_receipt_dialog(self, transaction_id, amount, payment_method, client, loan, description):
        """Show dialog with receipt options"""
        from utils.pdf_generator import generate_payment_receipt
        from pathlib import Path
        from tkinter import filedialog
        import io
        
        # Prepare payment data
        payment_data = {
            'transaction_id': transaction_id,
            'amount': amount,
            'payment_method': payment_method,
            'date': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'description': description
        }
        
        # Get user data from parent window
        user_data = self.master.user_data if hasattr(self.master, 'user_data') else {'username': 'Cajero'}
        
        # Create dialog
        dialog = tk.Toplevel(self)
        dialog.title("Recibo de Pago")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        
        tk.Label(dialog, text="✅ Pago Registrado", font=("Segoe UI", 16, "bold"), fg="#4CAF50").pack(pady=20)
        tk.Label(dialog, text=f"Monto: S/ {amount:.2f}", font=("Segoe UI", 14)).pack(pady=5)
        tk.Label(dialog, text="¿Desea generar un recibo?", font=("Segoe UI", 11)).pack(pady=10)
        
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        def print_receipt():
            try:
                filename = f"recibo_pago_{transaction_id}.pdf"
                filepath = os.path.abspath(filename)
                generate_payment_receipt(filepath, payment_data, dict(client), dict(loan), user_data)
                os.startfile(filepath)
                messagebox.showinfo("Éxito", "Recibo generado y abierto")
            except Exception as e:
                messagebox.showerror("Error", f"Error al generar recibo: {e}")
        
        def save_pdf():
            try:
                filename = f"recibo_{client['first_name']}_{transaction_id}.pdf"
                filepath = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("PDF Documents", "*.pdf")],
                    initialfile=filename
                )
                if filepath:
                    generate_payment_receipt(filepath, payment_data, dict(client), dict(loan), user_data)
                    messagebox.showinfo("Éxito", "Recibo guardado correctamente")
                    os.startfile(filepath)
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}")
        
        def share_receipt():
            try:
                downloads_path = str(Path.home() / "Downloads")
                filename = f"recibo_{client['first_name']}_{transaction_id}.png"
                filepath = os.path.join(downloads_path, filename)
                
                # Prepare full data for image generator
                full_data = payment_data.copy()
                full_data.update({
                    'client_name': f"{client['first_name']} {client['last_name']}",
                    'client_dni': client['dni'],
                    'loan_id': loan['id'],
                    'loan_type': loan['loan_type'],
                    'receipt_number': f"REC-{transaction_id}",
                    'cashier': user_data.get('username', 'Admin')
                })

                # Generate Image
                from utils.image_generator import ImageGenerator
                gen = ImageGenerator()
                img = gen.generate_payment_receipt_image(full_data)
                
                # Save to file
                img.save(filepath)
                
                # Copy to clipboard
                try:
                    gen.copy_to_clipboard(img)
                    
                    messagebox.showinfo("✅ Listo para Compartir", 
                                      f"Recibo guardado en:\n{filepath}\n\n"
                                      "✅ Copiado al portapapeles\n"
                                      "Ahora puedes ir a WhatsApp y presionar Ctrl+V para pegarlo")
                except Exception as e:
                    print(f"Clipboard error: {e}")
                    messagebox.showinfo("✅ Recibo Guardado", 
                                      f"Recibo guardado en:\n{filepath}\n\n"
                                      "Puedes encontrarlo en tu carpeta de Descargas")
            except Exception as e:
                messagebox.showerror("Error", f"Error al generar imagen: {e}")
        
        tk.Button(btn_frame, text="🖨️ Imprimir", command=print_receipt,
                 bg='#2196F3', fg='white', font=("Segoe UI", 10, "bold"),
                 padx=15, pady=8, width=15).pack(pady=5)
        
        tk.Button(btn_frame, text="💾 Guardar PDF", command=save_pdf,
                 bg='#4CAF50', fg='white', font=("Segoe UI", 10, "bold"),
                 padx=15, pady=8, width=15).pack(pady=5)
        
        tk.Button(btn_frame, text="📤 Compartir", command=share_receipt,
                 bg='#FF9800', fg='white', font=("Segoe UI", 10, "bold"),
                 padx=15, pady=8, width=15).pack(pady=5)
        
        tk.Button(btn_frame, text="Cerrar", command=dialog.destroy,
                 bg='#757575', fg='white', font=("Segoe UI", 10),
                 padx=15, pady=8, width=15).pack(pady=5)
                 
        self.wait_window(dialog)


class OtherIncomeForm(tk.Toplevel):
    def __init__(self, parent, session_id, callback):
        super().__init__(parent)
        self.session_id = session_id
        self.callback = callback
        self.title("Otros Ingresos")
        self.geometry("450x400")
        
        self.create_widgets()
    
    def create_widgets(self):
        tk.Label(self, text="Otros Ingresos", font=("Segoe UI", 14, "bold")).pack(pady=15)
        
        tk.Label(self, text="Categoría:").pack(pady=(10,0))
        self.combo_category = ttk.Combobox(self, values=["remate", "otros"], state='readonly', font=("Segoe UI", 10))
        self.combo_category.current(0)
        self.combo_category.pack(pady=5)
        
        tk.Label(self, text="Descripción:").pack(pady=(10,0))
        self.entry_desc = tk.Entry(self, font=("Segoe UI", 11), width=35)
        self.entry_desc.pack(pady=5)
        
        tk.Label(self, text="Monto:").pack(pady=(10,0))
        self.entry_amount = tk.Entry(self, font=("Segoe UI", 11), width=20)
        self.entry_amount.pack(pady=5)
        
        tk.Label(self, text="Método de Pago:").pack(pady=(10,0))
        self.combo_method = ttk.Combobox(self, values=["efectivo", "yape", "deposito"], 
                                         state='readonly', font=("Segoe UI", 10))
        self.combo_method.current(0)
        self.combo_method.pack(pady=5)
        
        tk.Button(self, text="Registrar", command=self.save, bg="#2196F3", fg="white",
                 font=("Segoe UI", 11, "bold"), padx=20, pady=8).pack(pady=20)
    
    def save(self):
        try:
            amount = float(self.entry_amount.get())
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO transactions (type, category, amount, description, payment_method, cash_session_id)
                VALUES ('income', ?, ?, ?, ?, ?)
            """, (self.combo_category.get(), amount, self.entry_desc.get(), 
                 self.combo_method.get(), self.session_id))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Éxito", "Ingreso registrado")
            self.callback()
            self.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Monto inválido")
        except Exception as e:
            messagebox.showerror("Error", str(e))


class ExpenseForm(tk.Toplevel):
    def __init__(self, parent, session_id, callback):
        super().__init__(parent)
        self.session_id = session_id
        self.callback = callback
        self.title("Gastos Operativos")
        self.geometry("450x400")
        
        self.create_widgets()
    
    def create_widgets(self):
        tk.Label(self, text="Gastos Operativos", font=("Segoe UI", 14, "bold")).pack(pady=15)
        
        tk.Label(self, text="Categoría:").pack(pady=(10,0))
        categories = ["alquiler", "luz", "agua", "internet", "personal_1_gerente", 
                     "personal_2_caja", "personal_3_admin", "personal_4_contador", "personal_5_otros"]
        self.combo_category = ttk.Combobox(self, values=categories, state='readonly', font=("Segoe UI", 10), width=30)
        self.combo_category.current(0)
        self.combo_category.pack(pady=5)
        
        tk.Label(self, text="Descripción/Comentario:").pack(pady=(10,0))
        self.entry_desc = tk.Entry(self, font=("Segoe UI", 11), width=35)
        self.entry_desc.pack(pady=5)
        
        tk.Label(self, text="Monto:").pack(pady=(10,0))
        self.entry_amount = tk.Entry(self, font=("Segoe UI", 11), width=20)
        self.entry_amount.pack(pady=5)
        
        tk.Button(self, text="Registrar Gasto", command=self.save, bg="#F44336", fg="white",
                 font=("Segoe UI", 11, "bold"), padx=20, pady=8).pack(pady=20)
    
    def save(self):
        try:
            amount = float(self.entry_amount.get())
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO transactions (type, category, amount, description, payment_method, cash_session_id)
                VALUES ('expense', ?, ?, ?, 'efectivo', ?)
            """, (self.combo_category.get(), amount, self.entry_desc.get(), self.session_id))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Éxito", "Gasto registrado")
            self.callback()
            self.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Monto inválido")
        except Exception as e:
            messagebox.showerror("Error", str(e))


class DisbursementForm(tk.Toplevel):
    def __init__(self, parent, session_id, callback):
        super().__init__(parent)
        self.session_id = session_id
        self.callback = callback
        self.title("Desembolso de Préstamo")
        self.geometry("450x350")
        
        self.create_widgets()
    
    def create_widgets(self):
        tk.Label(self, text="Desembolso de Préstamo", font=("Segoe UI", 14, "bold")).pack(pady=15)
        
        tk.Label(self, text="Monto Desembolsado:").pack(pady=(10,0))
        self.entry_amount = tk.Entry(self, font=("Segoe UI", 11), width=20)
        self.entry_amount.pack(pady=5)
        
        tk.Label(self, text="Descripción:").pack(pady=(10,0))
        self.entry_desc = tk.Entry(self, font=("Segoe UI", 11), width=35)
        self.entry_desc.pack(pady=5)
        
        tk.Label(self, text="Método de Pago:").pack(pady=(10,0))
        self.combo_method = ttk.Combobox(self, values=["efectivo", "yape", "deposito"], 
                                         state='readonly', font=("Segoe UI", 10))
        self.combo_method.current(0)
        self.combo_method.pack(pady=5)
        
        tk.Button(self, text="Registrar Desembolso", command=self.save, bg="#FF9800", fg="white",
                 font=("Segoe UI", 11, "bold"), padx=20, pady=8).pack(pady=20)
    
    def save(self):
        try:
            amount = float(self.entry_amount.get())
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO transactions (type, category, amount, description, payment_method, cash_session_id)
                VALUES ('expense', 'loan_disbursement', ?, ?, ?, ?)
            """, (amount, self.entry_desc.get(), self.combo_method.get(), self.session_id))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Éxito", "Desembolso registrado")
            self.callback()
            self.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Monto inválido")
        except Exception as e:
            messagebox.showerror("Error", str(e))
