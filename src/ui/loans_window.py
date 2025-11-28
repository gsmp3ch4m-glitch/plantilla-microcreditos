import tkinter as tk
from tkinter import ttk, messagebox
from database import get_db_connection
from tkcalendar import DateEntry
from datetime import datetime
import os

class LoansWindow(tk.Toplevel):
    def __init__(self, parent, loan_type=None):
        super().__init__(parent)
        self.loan_type = loan_type
        title = "Gestión de Préstamos"
        if loan_type == "empeno": title = "Casa de Empeño"
        elif loan_type == "bancario": title = "Préstamo Bancario"
        elif loan_type == "rapidiario": title = "Rapidiario"
        
        self.title(title)
        self.geometry("1000x600")
        
        self.create_widgets()
        self.load_loans()

    def create_widgets(self):
        # Toolbar
        toolbar = tk.Frame(self, bg="#e0e0e0")
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(toolbar, text="Nuevo Préstamo", command=self.open_add_loan_dialog).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Generar Contrato", command=self.generate_contract_pdf).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Actualizar", command=self.load_loans).pack(side=tk.LEFT, padx=5)
        
        # Filter
        tk.Label(toolbar, text="Buscar Cliente:", bg="#e0e0e0").pack(side=tk.LEFT, padx=(20, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.load_loans())
        tk.Entry(toolbar, textvariable=self.search_var).pack(side=tk.LEFT, padx=5)

        # Treeview
        columns = ("id", "client", "type", "amount", "date", "status")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("client", text="Cliente")
        self.tree.heading("type", text="Tipo")
        self.tree.heading("amount", text="Monto")
        self.tree.heading("date", text="Fecha Inicio")
        self.tree.heading("status", text="Estado")
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def load_loans(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        search_term = self.search_var.get()
        query = """
            SELECT l.id, c.first_name || ' ' || c.last_name as client_name, l.loan_type, l.amount, l.start_date, l.status
            FROM loans l
            JOIN clients c ON l.client_id = c.id
            WHERE 1=1
        """
        params = []
        
        if self.loan_type:
            query += " AND l.loan_type = ?"
            params.append(self.loan_type)
            
        if search_term:
            query += " AND (c.first_name LIKE ? OR c.last_name LIKE ?)"
            params.extend([f'%{search_term}%', f'%{search_term}%'])
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            self.tree.insert("", tk.END, values=(row["id"], row["client_name"], row["loan_type"], row["amount"], row["start_date"], row["status"]))

    def generate_contract_pdf(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un préstamo")
            return
            
        item = selection[0]
        loan_id = self.tree.item(item, "values")[0]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get Loan Data
        cursor.execute("SELECT * FROM loans WHERE id = ?", (loan_id,))
        loan_data = cursor.fetchone()
        
        # Get Client Data
        cursor.execute("SELECT * FROM clients WHERE id = ?", (loan_data['client_id'],))
        client_data = cursor.fetchone()
        
        # Get Pawn Data if exists
        pawn_data = None
        if loan_data['loan_type'] == 'empeno':
            cursor.execute("SELECT * FROM pawn_details WHERE loan_id = ?", (loan_id,))
            pawn_data = cursor.fetchone()
            
        conn.close()
        
        from utils.pdf_generator import generate_contract
        try:
            filepath = generate_contract(loan_data, client_data, pawn_data)
            messagebox.showinfo("Éxito", f"Contrato generado en:\n{filepath}")
            os.startfile(filepath)
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar PDF: {str(e)}")

    def open_add_loan_dialog(self):
        LoanForm(self, self.load_loans, default_type=self.loan_type)


class LoanForm(tk.Toplevel):
    def __init__(self, parent, callback, default_type=None):
        super().__init__(parent)
        self.parent = parent # Store parent to access user_data
        self.callback = callback
        self.default_type = default_type
        self.title("Nuevo Préstamo")
        self.geometry("500x600")
        
        self.create_widgets()

    def create_widgets(self):
        # Client Selection
        tk.Label(self, text="Cliente (DNI):").pack(pady=(10, 0))
        self.client_frame = tk.Frame(self)
        self.client_frame.pack()
        
        self.entry_dni = tk.Entry(self.client_frame)
        self.entry_dni.pack(side=tk.LEFT)
        tk.Button(self.client_frame, text="Buscar", command=self.search_client).pack(side=tk.LEFT, padx=5)
        
        self.lbl_client_name = tk.Label(self, text="Cliente no seleccionado", fg="red")
        self.lbl_client_name.pack()
        self.selected_client_id = None

        # Loan Type
        tk.Label(self, text="Tipo de Préstamo:").pack(pady=(10, 0))
        self.combo_type = ttk.Combobox(self, values=["empeno", "bancario", "rapidiario"])
        if self.default_type:
            self.combo_type.set(self.default_type)
            self.combo_type.configure(state="disabled")
        else:
            self.combo_type.current(0)
        self.combo_type.pack()
        self.combo_type.bind("<<ComboboxSelected>>", self.on_type_change)

        # Amount
        tk.Label(self, text="Monto:").pack()
        self.entry_amount = tk.Entry(self)
        self.entry_amount.pack()
        
        # Interest
        tk.Label(self, text="Tasa de Interés (%):").pack()
        self.entry_interest = tk.Entry(self)
        self.entry_interest.pack()

        # Dates
        tk.Label(self, text="Fecha Inicio:").pack()
        self.date_start = DateEntry(self, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.date_start.pack()

        # Dynamic Fields Frame
        self.dynamic_frame = tk.Frame(self)
        self.dynamic_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.on_type_change(None) # Init dynamic fields

        tk.Button(self, text="Guardar Préstamo", command=self.save).pack(pady=20)

    def search_client(self):
        dni = self.entry_dni.get()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, first_name, last_name FROM clients WHERE dni = ?", (dni,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            self.selected_client_id = row["id"]
            self.lbl_client_name.config(text=f"{row['first_name']} {row['last_name']}", fg="green")
        else:
            self.selected_client_id = None
            self.lbl_client_name.config(text="Cliente no encontrado", fg="red")

    def on_type_change(self, event):
        # Clear dynamic frame
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()
            
        loan_type = self.combo_type.get()
        
        # Map loan_type to config key (simplified mapping for now)
        # In a real scenario, we might map 'empeno' -> 'loan1', 'bancario' -> 'loan2', etc.
        # But here the user said "loan 1 is empeno", "loan 2 is bancario".
        # Let's assume the combo values match the keys or we map them.
        
        config_key = 'loan1' # Default
        if loan_type == 'empeno': config_key = 'loan1'
        elif loan_type == 'bancario': config_key = 'loan2'
        elif loan_type == 'rapidiario': config_key = 'loan3'
        
        from utils.settings_manager import get_setting
        
        # Load Settings
        interest = get_setting(f'{config_key}_interest') or "5"
        self.entry_interest.delete(0, tk.END)
        self.entry_interest.insert(0, interest)
        
        self.max_items = int(get_setting(f'{config_key}_max_items') or "3")
        self.max_amount = float(get_setting(f'{config_key}_max_amount') or "2000")
        
        # Collateral Fields (For Empeño and Bancario)
        self.pawn_items = []
        
        if loan_type in ['empeno', 'bancario']:
            tk.Label(self.dynamic_frame, text=f"--- Garantía (Máx {self.max_items}) ---", font=("Segoe UI", 9, "bold")).pack(pady=5)
            
            self.items_frame = tk.Frame(self.dynamic_frame)
            self.items_frame.pack(fill=tk.X)
            
            tk.Button(self.dynamic_frame, text="+ Agregar Bien", command=self.add_pawn_item).pack(pady=5)
            
            # Add first item by default
            self.add_pawn_item()
            
        elif loan_type == 'rapidiario':
            tk.Label(self.dynamic_frame, text=f"Límite de Monto: S/. {self.max_amount}", fg="red").pack()
            tk.Label(self.dynamic_frame, text="Pago: Diario / Semanal", font=("Segoe UI", 9, "bold")).pack()
            
            tk.Label(self.dynamic_frame, text="Frecuencia de Pago:").pack()
            self.combo_freq = ttk.Combobox(self.dynamic_frame, values=["Diario", "Semanal"])
            self.combo_freq.current(0)
            self.combo_freq.pack()

    def add_pawn_item(self):
        if len(self.pawn_items) >= self.max_items:
            messagebox.showwarning("Límite", f"Máximo {self.max_items} bienes permitidos.")
            return
            
        frame = tk.LabelFrame(self.items_frame, text=f"Bien #{len(self.pawn_items)+1}")
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Type, Brand, Characteristics, Condition, Value
        tk.Label(frame, text="Tipo:").grid(row=0, column=0)
        e_type = tk.Entry(frame, width=15)
        e_type.grid(row=0, column=1)
        
        tk.Label(frame, text="Marca:").grid(row=0, column=2)
        e_brand = tk.Entry(frame, width=15)
        e_brand.grid(row=0, column=3)
        
        tk.Label(frame, text="Estado:").grid(row=1, column=0)
        e_cond = ttk.Combobox(frame, values=["Nuevo", "Usado", "Dañado"], width=12)
        e_cond.grid(row=1, column=1)
        
        tk.Label(frame, text="Valor:").grid(row=1, column=2)
        e_val = tk.Entry(frame, width=10)
        e_val.grid(row=1, column=3)
        
        tk.Label(frame, text="Características:").grid(row=2, column=0)
        e_chars = tk.Entry(frame, width=40)
        e_chars.grid(row=2, column=1, columnspan=3)
        
        self.pawn_items.append({
            'type': e_type, 'brand': e_brand, 'cond': e_cond, 'val': e_val, 'chars': e_chars
        })

    def save(self):
        if not self.selected_client_id:
            messagebox.showerror("Error", "Seleccione un cliente")
            return
            
        amount = float(self.entry_amount.get())
        interest = self.entry_interest.get()
        loan_type = self.combo_type.get()
        
        # Validation
        if loan_type == 'rapidiario' and amount > self.max_amount:
            messagebox.showerror("Error", f"El monto excede el límite de S/. {self.max_amount}")
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        from database import log_action
        
        try:
            cursor.execute("""
                INSERT INTO loans (client_id, loan_type, amount, interest_rate, start_date, status)
                VALUES (?, ?, ?, ?, ?, 'active')
            """, (self.selected_client_id, loan_type, amount, interest, self.date_start.get_date()))
            
            loan_id = cursor.lastrowid
            
            # Save Pawn Items
            if loan_type in ['empeno', 'bancario']:
                for item in self.pawn_items:
                    cursor.execute("""
                        INSERT INTO pawn_details (loan_id, item_type, brand, condition, market_value, characteristics)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (loan_id, item['type'].get(), item['brand'].get(), item['cond'].get(), 
                          item['val'].get() or 0, item['chars'].get()))
            
            # Generate Installments (Cronograma)
            from datetime import timedelta, date
            start_date = self.date_start.get_date()
            
            installments = []
            
            if loan_type == 'rapidiario':
                freq = self.combo_freq.get()
                term_days = int(get_setting(f'loan3_term_days') or "30")
                
                # Simple logic: 
                # If Daily: Pay every day for 'term_days' (excluding Sundays?) - Let's keep it simple for now: every day.
                # If Weekly: Pay every 7 days until term ends.
                
                # Calculate total to pay (Amount + Interest)
                # Interest for rapidiario is usually flat fee or percentage? 
                # Let's assume the interest rate entered is the TOTAL interest percentage for the period.
                total_interest = amount * (float(interest) / 100)
                total_pay = amount + total_interest
                
                if freq == 'Diario':
                    num_installments = term_days
                    amount_per_inst = total_pay / num_installments
                    for i in range(1, num_installments + 1):
                        due_date = start_date + timedelta(days=i)
                        installments.append((i, due_date, amount_per_inst))
                        
                elif freq == 'Semanal':
                    num_installments = term_days // 7
                    if num_installments == 0: num_installments = 1
                    amount_per_inst = total_pay / num_installments
                    for i in range(1, num_installments + 1):
                        due_date = start_date + timedelta(weeks=i)
                        installments.append((i, due_date, amount_per_inst))
                        
            else: 
                # Empeño / Bancario - Usually 1 month term renewable, or fixed monthly installments?
                # For MVP, let's assume 1 installment at the end of 30 days (standard pawn shop model)
                # Or if user wants monthly payments, we'd need a 'Term (Months)' field.
                # Let's default to 1 installment (Capital + Interest) due in 30 days.
                
                term_days = 30 # Default for Empeño
                due_date = start_date + timedelta(days=term_days)
                
                # Interest is usually monthly.
                total_interest = amount * (float(interest) / 100)
                total_pay = amount + total_interest
                
                installments.append((1, due_date, total_pay))
            
            # Insert Installments
            for num, due, amt in installments:
                cursor.execute("""
                    INSERT INTO installments (loan_id, number, due_date, amount, status)
                    VALUES (?, ?, ?, ?, 'pending')
                """, (loan_id, num, due, amt))

            # Log Action
            user_id = self.parent.user_data['id'] if hasattr(self.parent, 'user_data') else None
            log_action(user_id, "Crear Préstamo", f"Préstamo {loan_type} creado: ID {loan_id} - Monto {amount} - {len(installments)} cuotas")
            
            conn.commit()
            messagebox.showinfo("Éxito", "Préstamo registrado correctamente")
            self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()
