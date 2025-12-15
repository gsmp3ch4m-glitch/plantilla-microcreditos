import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from database import get_db_connection, log_action
from tkcalendar import DateEntry
from datetime import datetime, date
from utils.loan_calculator import obtener_info_prestamo
from utils.settings_manager import get_setting
from utils.loan_manager import can_refinance_rapidiario, refinance_rapidiario
import os

class LoansWindow(tk.Toplevel):
    def __init__(self, parent, user_data=None, loan_type=None):
        super().__init__(parent)
        self.parent = parent
        self.user_data = user_data or (parent.user_data if hasattr(parent, 'user_data') else {})
        self.loan_type = loan_type
        
        # Map loan types from menu to database values
        type_map = {
            'pawn': 'empeno',
            'bank': 'bancario',
            'rapid': 'rapidiario',
            'frozen': 'congelado'
        }
        if loan_type in type_map:
            self.loan_type = type_map[loan_type]
        
        title = "Gestión de Préstamos"
        if self.loan_type == "empeno": title = "Casa de Empeño"
        elif self.loan_type == "bancario": title = "Préstamo Bancario"
        elif self.loan_type == "rapidiario": title = "Rapidiario"
        elif self.loan_type == "congelado": title = "Préstamo Congelado"
        
        self.title(title)
        self.geometry("1200x700")
        
        self.create_widgets()
        self.load_loans()

    def create_widgets(self):
        # Toolbar
        toolbar = tk.Frame(self, bg="#2196F3", height=50)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)
        
        if self.loan_type != 'congelado':
            tk.Button(toolbar, text="➕ Nuevo Préstamo", command=self.open_add_loan_dialog,
                     bg='#4CAF50', fg='white', font=("Segoe UI", 10, "bold"),
                     relief='flat', cursor='hand2', padx=15, pady=8).pack(side=tk.LEFT, padx=10, pady=8)
        
        tk.Button(toolbar, text="📄 Ver Cronograma", command=self.view_schedule,
                 bg='#FF9800', fg='white', font=("Segoe UI", 10, "bold"),
                 relief='flat', cursor='hand2', padx=15, pady=8).pack(side=tk.LEFT, padx=5, pady=8)
        
        tk.Button(toolbar, text="🔄 Actualizar", command=self.load_loans,
                 bg='#2196F3', fg='white', font=("Segoe UI", 10, "bold"),
                 relief='flat', cursor='hand2', padx=15, pady=8).pack(side=tk.LEFT, padx=5, pady=8)

        # Refinance Button (Only for Rapidiario)
        if self.loan_type == 'rapidiario':
            self.btn_refinance = tk.Button(toolbar, text="💸 Refinanciar", command=self.refinance_selected,
                     bg='#9C27B0', fg='white', font=("Segoe UI", 10, "bold"),
                     relief='flat', cursor='hand2', padx=15, pady=8, state='disabled')
            self.btn_refinance.pack(side=tk.LEFT, padx=5, pady=8)

        # Freeze Button (For active loans)
        if self.loan_type != 'congelado':
            self.btn_freeze = tk.Button(toolbar, text="❄️ Congelar", command=self.freeze_selected,
                     bg='#607D8B', fg='white', font=("Segoe UI", 10, "bold"),
                     relief='flat', cursor='hand2', padx=15, pady=8, state='disabled')
            self.btn_freeze.pack(side=tk.LEFT, padx=5, pady=8)

        # Liquidate Button (For frozen loans)
        if self.loan_type == 'congelado':
            self.btn_liquidate = tk.Button(toolbar, text="🔨 Rematar Garantía", command=self.liquidate_selected,
                     bg='#E91E63', fg='white', font=("Segoe UI", 10, "bold"),
                     relief='flat', cursor='hand2', padx=15, pady=8, state='disabled')
            self.btn_liquidate.pack(side=tk.LEFT, padx=5, pady=8)
            
            # Check Overdue Button
            tk.Button(toolbar, text="⚠️ Verificar Mora", command=self.check_overdue,
                     bg='#FF5722', fg='white', font=("Segoe UI", 10, "bold"),
                     relief='flat', cursor='hand2', padx=15, pady=8).pack(side=tk.LEFT, padx=5, pady=8)

            # Legacy Frozen Loan Button
            tk.Button(toolbar, text="➕ Agregar Histórico", command=self.open_legacy_dialog,
                     bg='#607D8B', fg='white', font=("Segoe UI", 10, "bold"),
                     relief='flat', cursor='hand2', padx=15, pady=8).pack(side=tk.LEFT, padx=5, pady=8)

            # Pay Button (For frozen loans)
            self.btn_pay = tk.Button(toolbar, text="💰 Pagar", command=self.pay_selected,
                     bg='#4CAF50', fg='white', font=("Segoe UI", 10, "bold"),
                     relief='flat', cursor='hand2', padx=15, pady=8, state='disabled')
            self.btn_pay.pack(side=tk.LEFT, padx=5, pady=8)
        
        # Search
        tk.Label(toolbar, text="🔍 Buscar:", bg="#2196F3", fg='white',
                font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(20, 5), pady=8)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.load_loans())
        search_entry = tk.Entry(toolbar, textvariable=self.search_var, font=("Segoe UI", 10), width=20)
        search_entry.pack(side=tk.LEFT, padx=5, pady=8)

        # View Clients Button (Only for Pawn Shop)
        # View Clients Button (For all loan types)
        tk.Button(toolbar, text="👥 Ver Clientes", command=self.open_clients,
                  bg='#009688', fg='white', font=("Segoe UI", 10, "bold"),
                  relief='flat', cursor='hand2', padx=15, pady=8).pack(side=tk.RIGHT, padx=10, pady=8)

        # Treeview
        tree_frame = tk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("id", "client", "type", "amount", "interest", "date", "due_date", "status")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        
        self.tree.heading("id", text="ID")
        self.tree.heading("client", text="Cliente")
        self.tree.heading("type", text="Tipo")
        self.tree.heading("amount", text="Monto")
        self.tree.heading("interest", text="Interés %")
        self.tree.heading("date", text="Fecha Inicio")
        self.tree.heading("due_date", text="Vencimiento")
        self.tree.heading("status", text="Estado")
        
        self.tree.column("id", width=50, anchor='center')
        self.tree.column("client", width=200)
        self.tree.column("type", width=120)
        self.tree.column("amount", width=100, anchor='e')
        self.tree.column("interest", width=80, anchor='center')
        self.tree.column("date", width=100, anchor='center')
        self.tree.column("due_date", width=100, anchor='center')
        self.tree.column("status", width=100, anchor='center')
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            if hasattr(self, 'btn_refinance'): self.btn_refinance.config(state='disabled')
            if hasattr(self, 'btn_freeze'): self.btn_freeze.config(state='disabled')
            if hasattr(self, 'btn_liquidate'): self.btn_liquidate.config(state='disabled')
            return
            
        item = self.tree.item(selected[0])
        loan_id = item['values'][0]
        status = item['values'][7] # status column
        
        # Refinance logic
        if hasattr(self, 'btn_refinance'):
            can, msg = can_refinance_rapidiario(loan_id)
            if can:
                self.btn_refinance.config(state='normal', bg='#9C27B0')
            else:
                self.btn_refinance.config(state='disabled', bg='#cccccc')

        # Freeze logic
        if hasattr(self, 'btn_freeze'):
            if status in ['active', 'overdue']:
                self.btn_freeze.config(state='normal', bg='#607D8B')
            else:
                self.btn_freeze.config(state='disabled', bg='#cccccc')

        # Liquidate logic
        if hasattr(self, 'btn_liquidate'):
            if status == 'frozen':
                self.btn_liquidate.config(state='normal', bg='#E91E63')
            else:
                self.btn_liquidate.config(state='disabled', bg='#cccccc')

        # Pay logic
        if hasattr(self, 'btn_pay'):
            if status == 'frozen':
                self.btn_pay.config(state='normal', bg='#4CAF50')
            else:
                self.btn_pay.config(state='disabled', bg='#cccccc')

    def pay_selected(self):
        selected = self.tree.selection()
        if not selected: return
        
        item = self.tree.item(selected[0])
        loan_id = item['values'][0]
        
        from ui.payment_window import PaymentWindow
        PaymentWindow(self, loan_id)

    def freeze_selected(self):
        selected = self.tree.selection()
        if not selected: return
        
        item = self.tree.item(selected[0])
        loan_id = item['values'][0]
        
        from utils.loan_manager import freeze_loan
        
        if messagebox.askyesno("Confirmar Congelamiento", 
                             "¿Está seguro de congelar este préstamo?\n\n"
                             "- El estado cambiará a 'frozen'.\n"
                             "- Se calcularán gastos administrativos si aplica.\n"
                             "- El préstamo dejará de generar intereses regulares."):
            
            success, msg = freeze_loan(loan_id, self.user_data['id'])
            if success:
                messagebox.showinfo("Éxito", msg)
                self.load_loans()
            else:
                messagebox.showerror("Error", msg)

    def liquidate_selected(self):
        selected = self.tree.selection()
        if not selected: return
        
        item = self.tree.item(selected[0])
        loan_id = item['values'][0]
        
        # Ask for sale price
        from tkinter import simpledialog
        sale_price = simpledialog.askfloat("Remate", "Ingrese el precio de venta de la garantía (S/):")
        if sale_price is None: return
        
        sales_expense = simpledialog.askfloat("Remate", "Ingrese los gastos de venta (S/):", initialvalue=0.0)
        if sales_expense is None: return
        
        from utils.loan_manager import execute_collateral
        
        if messagebox.askyesno("Confirmar Remate", 
                             f"¿Confirmar remate?\n\nVenta: S/ {sale_price:.2f}\nGastos: S/ {sales_expense:.2f}"):
            
            success, msg = execute_collateral(loan_id, sale_price, sales_expense, self.user_data['id'])
            if success:
                messagebox.showinfo("Éxito", msg)
                self.load_loans()
            else:
                messagebox.showerror("Error", msg)

    def check_overdue(self):
        from utils.loan_manager import check_and_freeze_loans
        
        if messagebox.askyesno("Verificar Mora", 
                             "Se buscarán préstamos vencidos según las reglas:\n\n"
                             "- Rapidiario: 3 refinanciamientos + vencido\n"
                             "- Empeño: > 75 días desde inicio\n"
                             "- Bancario: > 105 días desde inicio\n\n"
                             "¿Desea continuar?"):
            
            count = check_and_freeze_loans(self.user_data['id'])
            if count > 0:
                messagebox.showinfo("Proceso Completado", f"Se han congelado {count} préstamos automáticamente.")
                self.load_loans()
            else:
                messagebox.showinfo("Proceso Completado", "No se encontraron préstamos para congelar.")

    def open_legacy_dialog(self):
        LegacyFrozenLoanDialog(self, self.load_loans)

    def refinance_selected(self):
        selected = self.tree.selection()
        if not selected: return
        
        item = self.tree.item(selected[0])
        loan_id = item['values'][0]
        
        if messagebox.askyesno("Confirmar Refinanciamiento", 
                             "¿Está seguro de refinanciar este préstamo?\n\n"
                             "- Se cerrará el préstamo actual.\n"
                             "- Se creará uno nuevo con la deuda total.\n"
                             "- Interés: 8%\n"
                             "- Plazo: 30 días"):
            
            success, msg = refinance_rapidiario(loan_id, self.user_data['id'])
            if success:
                messagebox.showinfo("Éxito", msg)
                self.load_loans()
            else:
                messagebox.showerror("Error", msg)

    def load_loans(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        search_term = self.search_var.get()
        query = """
            SELECT l.id, c.first_name || ' ' || c.last_name as client_name, 
                   l.loan_type, l.amount, l.interest_rate, l.start_date, l.due_date, l.status,
                   l.frozen_amount
            FROM loans l
            JOIN clients c ON l.client_id = c.id
            WHERE 1=1
        """
        params = []
        
        if self.loan_type == 'congelado':
            query += " AND l.status = 'frozen'"
        elif self.loan_type:
            query += " AND l.loan_type = ? AND l.status != 'frozen'"
            params.append(self.loan_type)
            
        if search_term:
            query += " AND (c.first_name LIKE ? OR c.last_name LIKE ? OR c.dni LIKE ?)"
            params.extend([f'%{search_term}%'] * 3)
        
        query += " ORDER BY l.id DESC"
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            amount_display = row['amount']
            if row['status'] == 'frozen' and row['frozen_amount']:
                amount_display = row['frozen_amount']
                
            self.tree.insert("", tk.END, values=(
                row["id"], row["client_name"], row["loan_type"], 
                f"S/ {amount_display:.2f}", f"{row['interest_rate']}%",
                row["start_date"], row["due_date"] or "N/A", row["status"]
            ))

    def view_schedule(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Seleccione un préstamo")
            return
        
        loan_id = self.tree.item(selection[0], "values")[0]
        from ui.schedule_window import ScheduleWindow
        ScheduleWindow(self, loan_id)

    def open_add_loan_dialog(self):
        LoanForm(self, self.loan_type, self.load_loans)

    def open_clients(self):
        def start_new_loan(client_id):
            LoanForm(self, self.loan_type, self.load_loans, client_id=client_id)
            
        from ui.clients_window import ClientsWindow
        ClientsWindow(self, filter_loan_type=self.loan_type, on_select_callback=start_new_loan)


class LegacyFrozenLoanDialog(tk.Toplevel):
    """Diálogo para agregar préstamos congelados históricos"""
    def __init__(self, parent, callback=None):
        super().__init__(parent)
        self.parent = parent
        self.callback = callback
        self.selected_client_id = None
        
        self.title("Agregar Préstamo Congelado Histórico")
        self.geometry("800x600")
        self.resizable(False, False)
        
        self.create_widgets()

    def create_widgets(self):
        # Header
        header = tk.Frame(self, bg="#607D8B", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="❄️ CARGA HISTÓRICA DE CONGELADOS", font=("Segoe UI", 14, "bold"),
                bg="#607D8B", fg='white').pack(pady=15)
        
        # Main form
        form = tk.Frame(self, padx=20, pady=20)
        form.pack(fill=tk.BOTH, expand=True)
        
        # 1. Client Selection (Reused logic)
        client_frame = tk.LabelFrame(form, text="1. Seleccionar Cliente", font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        client_frame.pack(fill=tk.X, pady=(0, 15))
        
        search_box = tk.Frame(client_frame)
        search_box.pack(fill=tk.X)
        
        tk.Label(search_box, text="Buscar:", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.entry_search = ttk.Entry(search_box, width=30)
        self.entry_search.pack(side=tk.LEFT, padx=5)
        self.entry_search.bind('<Return>', lambda e: self.search_client())
        
        tk.Button(search_box, text="🔍", command=self.search_client,
                 bg='#607D8B', fg='white', relief='flat').pack(side=tk.LEFT)
                 
        self.client_combo = ttk.Combobox(client_frame, state="readonly", width=50)
        self.client_combo.pack(fill=tk.X, pady=5)
        self.client_combo.bind("<<ComboboxSelected>>", self.on_client_select)
        
        self.load_clients()
        
        # 2. Loan Details
        details_frame = tk.LabelFrame(form, text="2. Datos del Préstamo", font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Type
        tk.Label(details_frame, text="Tipo de Préstamo:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.combo_type = ttk.Combobox(details_frame, values=["rapidiario", "empeno", "bancario"], state="readonly")
        self.combo_type.current(0)
        self.combo_type.grid(row=0, column=1, sticky="w", pady=5)
        self.combo_type.bind("<<ComboboxSelected>>", self.update_fields)
        
        # Date
        tk.Label(details_frame, text="Fecha Congelamiento:", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky="w", pady=5, padx=(20, 0))
        self.date_frozen = DateEntry(details_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.date_frozen.grid(row=0, column=3, sticky="w", pady=5)
        
        # Dynamic Fields Container
        self.dynamic_frame = tk.Frame(details_frame)
        self.dynamic_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=10)
        
        # Description
        tk.Label(details_frame, text="Observaciones / Garantía:", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="nw", pady=5)
        self.txt_desc = tk.Text(details_frame, height=3, width=50, font=("Segoe UI", 9))
        self.txt_desc.grid(row=2, column=1, columnspan=3, sticky="ew", pady=5)
        
        # Total Preview
        self.lbl_total = tk.Label(details_frame, text="Total a Pagar: S/ 0.00", font=("Segoe UI", 12, "bold"), fg="#E91E63")
        self.lbl_total.grid(row=3, column=0, columnspan=4, pady=15)
        
        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Button(btn_frame, text="💾 GUARDAR", command=self.save,
                 bg='#4CAF50', fg='white', font=("Segoe UI", 10, "bold"),
                 relief='flat', padx=20, pady=10).pack(side=tk.RIGHT)
                 
        tk.Button(btn_frame, text="❌ CANCELAR", command=self.destroy,
                 bg='#f44336', fg='white', font=("Segoe UI", 10, "bold"),
                 relief='flat', padx=20, pady=10).pack(side=tk.RIGHT, padx=10)
        
        self.update_fields()

    def load_clients(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, first_name, last_name, dni FROM clients ORDER BY first_name")
        clients = cursor.fetchall()
        conn.close()
        
        self.clients_data = {}
        self.all_client_names = []
        
        for client in clients:
            display_name = f"{client['first_name']} {client['last_name']} - DNI: {client['dni']}"
            self.all_client_names.append(display_name)
            self.clients_data[display_name] = client['id']

    def search_client(self):
        search_term = self.entry_search.get().lower()
        if not search_term:
            self.client_combo['values'] = self.all_client_names
            return

        filtered = [n for n in self.all_client_names if search_term in n.lower()]
        self.client_combo['values'] = filtered
        if filtered:
            self.client_combo.current(0)
            self.on_client_select(None)
            self.client_combo.event_generate('<Down>')

    def on_client_select(self, event):
        selected = self.client_combo.get()
        if selected in self.clients_data:
            self.selected_client_id = self.clients_data[selected]

    def update_fields(self, event=None):
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()
            
        loan_type = self.combo_type.get()
        
        if loan_type == 'rapidiario':
            tk.Label(self.dynamic_frame, text="Monto Deuda Actual (S/):", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
            self.entry_amount = ttk.Entry(self.dynamic_frame)
            self.entry_amount.grid(row=0, column=1, sticky="w", padx=5)
            self.entry_amount.bind('<KeyRelease>', self.calculate_total)
            
            tk.Label(self.dynamic_frame, text="+ 5% Gastos Admin Automático", fg="gray").grid(row=0, column=2, sticky="w")
            
        else: # empeno, bancario
            tk.Label(self.dynamic_frame, text="Capital Original (S/):", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
            self.entry_amount = ttk.Entry(self.dynamic_frame)
            self.entry_amount.grid(row=0, column=1, sticky="w", padx=5)
            self.entry_amount.bind('<KeyRelease>', self.calculate_total)
            
            tk.Label(self.dynamic_frame, text="Meses Atraso:", font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=5)
            self.entry_months = ttk.Entry(self.dynamic_frame, width=10)
            self.entry_months.grid(row=1, column=1, sticky="w", padx=5, pady=5)
            self.entry_months.bind('<KeyRelease>', self.calculate_total)
            
            tk.Label(self.dynamic_frame, text="Tasa Interés (%):", font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w")
            self.entry_rate = ttk.Entry(self.dynamic_frame, width=10)
            self.entry_rate.grid(row=2, column=1, sticky="w", padx=5)
            self.entry_rate.bind('<KeyRelease>', self.calculate_total)

    def calculate_total(self, event=None):
        try:
            loan_type = self.combo_type.get()
            amount = float(self.entry_amount.get() or 0)
            
            total = 0
            if loan_type == 'rapidiario':
                total = amount * 1.05
            else:
                months = float(self.entry_months.get() or 0)
                rate = float(self.entry_rate.get() or 0)
                interest = amount * (rate / 100) * months
                total = amount + interest
                
            self.lbl_total.config(text=f"Total a Pagar: S/ {total:.2f}")
            return total
        except ValueError:
            pass

    def save(self):
        if not self.selected_client_id:
            messagebox.showerror("Error", "Seleccione un cliente")
            return
            
        try:
            loan_type = self.combo_type.get()
            amount = float(self.entry_amount.get())
            frozen_date = self.date_frozen.get_date()
            desc = self.txt_desc.get("1.0", tk.END).strip()
            
            kwargs = {
                'description': desc,
                'user_id': self.parent.user_data.get('id') if hasattr(self.parent, 'user_data') else None
            }
            
            if loan_type != 'rapidiario':
                kwargs['months_overdue'] = float(self.entry_months.get())
                kwargs['interest_rate'] = float(self.entry_rate.get())
            
            from utils.loan_manager import create_legacy_frozen_loan
            success, msg = create_legacy_frozen_loan(self.selected_client_id, loan_type, amount, frozen_date, **kwargs)
            
            if success:
                messagebox.showinfo("Éxito", msg)
                if self.callback: self.callback()
                self.destroy()
            else:
                messagebox.showerror("Error", msg)
                
        except ValueError:
            messagebox.showerror("Error", "Verifique los valores numéricos")


class LoanForm(tk.Toplevel):
    """Formulario completo para crear un nuevo préstamo"""
    def __init__(self, parent, default_type=None, callback=None, client_id=None):
        super().__init__(parent)
        self.parent = parent
        self.default_type = default_type
        self.callback = callback
        self.start_with_client_id = client_id
        self.selected_client_id = None
        self.pawn_items = []
        
        self.title("Nuevo Préstamo")
        self.geometry("900x750")
        self.resizable(False, False)
        
        self.create_widgets()

    def create_widgets(self):
        # Main container with scroll
        main_container = tk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(main_container)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Header
        header = tk.Frame(scrollable_frame, bg="#2196F3", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="📝 NUEVO PRÉSTAMO", font=("Segoe UI", 16, "bold"),
                bg="#2196F3", fg='white').pack(pady=15)
        
        # Form content
        form = tk.Frame(scrollable_frame, padx=30, pady=20)
        form.pack(fill=tk.BOTH, expand=True)
        
        # Client Selection
        client_frame = tk.LabelFrame(form, text="Selección de Cliente", font=("Segoe UI", 11, "bold"),
                                     padx=15, pady=10)
        client_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Search container
        search_container = tk.Frame(client_frame)
        search_container.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(search_container, text="Buscar (Nombre/DNI):", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.entry_search = ttk.Entry(search_container, font=("Segoe UI", 10))
        self.entry_search.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        self.entry_search.bind('<Return>', lambda e: self.search_client())
        
        tk.Button(search_container, text="🔍 Buscar", command=self.search_client,
                 bg='#2196F3', fg='white', font=("Segoe UI", 9, "bold"),
                 relief='flat', cursor='hand2', padx=15).pack(side=tk.LEFT)
        
        # Result combo
        tk.Label(client_frame, text="Seleccionar Cliente:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.client_combo = ttk.Combobox(client_frame, font=("Segoe UI", 10), state="readonly", width=50)
        self.client_combo.pack(fill=tk.X, ipady=5)
        
        # Load all clients initially but don't show all in dropdown to avoid clutter if many
        self.load_clients()
        self.client_combo['values'] = [] # Start empty or with all, user prefers search
        
        self.client_combo.bind("<<ComboboxSelected>>", self.on_client_select)
        
        # Pre-select client if provided
        if self.start_with_client_id:
            # Find name in map
            for name, cid in self.clients_data.items():
                if cid == self.start_with_client_id:
                    self.client_combo.set(name)
                    self.selected_client_id = cid
                    break
        
        # Loan Details
        details_frame = tk.LabelFrame(form, text="Datos del Préstamo", font=("Segoe UI", 11, "bold"),
                                      padx=15, pady=10)
        details_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Tipo de Préstamo
        tk.Label(details_frame, text="Tipo de Préstamo:", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=5, padx=(0, 10))
        
        loan_types = ["rapidiario", "empeno", "bancario", "congelado"]
        self.combo_type = ttk.Combobox(details_frame, values=loan_types, font=("Segoe UI", 10),
                                       state="readonly", width=25)
        if self.default_type:
            self.combo_type.set(self.default_type)
            self.combo_type.configure(state="disabled")
        else:
            self.combo_type.current(0)
        self.combo_type.grid(row=0, column=1, sticky="ew", pady=5)
        self.combo_type.bind("<<ComboboxSelected>>", self.on_type_change)
        
        # Monto
        tk.Label(details_frame, text="Monto (S/):", font=("Segoe UI", 10, "bold")).grid(
            row=1, column=0, sticky="w", pady=5, padx=(0, 10))
        self.entry_amount = ttk.Entry(details_frame, font=("Segoe UI", 10), width=25)
        self.entry_amount.grid(row=1, column=1, sticky="ew", pady=5)
        
        # Tasa de Interés
        tk.Label(details_frame, text="Tasa de Interés (%):", font=("Segoe UI", 10, "bold")).grid(
            row=2, column=0, sticky="w", pady=5, padx=(0, 10))
        self.entry_interest = ttk.Entry(details_frame, font=("Segoe UI", 10), width=25)
        # Default empty as requested
        self.entry_interest.grid(row=2, column=1, sticky="ew", pady=5)
        
        # Fecha Inicio
        tk.Label(details_frame, text="Fecha de Inicio:", font=("Segoe UI", 10, "bold")).grid(
            row=3, column=0, sticky="w", pady=5, padx=(0, 10))
        self.date_start = DateEntry(details_frame, width=23, background='darkblue',
                                    foreground='white', borderwidth=2, font=("Segoe UI", 10))
        self.date_start.grid(row=3, column=1, sticky="w", pady=5)
        
        details_frame.columnconfigure(1, weight=1)
        
        # Dynamic Fields Frame
        self.dynamic_frame = tk.Frame(form)
        self.dynamic_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Summary Frame
        self.summary_frame = tk.LabelFrame(form, text="Resumen del Préstamo", font=("Segoe UI", 11, "bold"),
                                          padx=15, pady=10, bg="#f5f5f5")
        self.summary_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.lbl_summary = tk.Label(self.summary_frame, text="Complete los datos para ver el resumen",
                                   font=("Segoe UI", 10), bg="#f5f5f5", justify=tk.LEFT)
        self.lbl_summary.pack(anchor="w")
        
        # Buttons
        btn_frame = tk.Frame(form)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(btn_frame, text="💾 GUARDAR PRÉSTAMO", command=self.save,
                 bg='#4CAF50', fg='white', font=("Segoe UI", 12, "bold"),
                 relief='flat', cursor='hand2', padx=30, pady=12).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        tk.Button(btn_frame, text="❌ CANCELAR", command=self.destroy,
                 bg='#f44336', fg='white', font=("Segoe UI", 12, "bold"),
                 relief='flat', cursor='hand2', padx=30, pady=12).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Initialize dynamic fields
        self.on_type_change(None)
        
        # Bind mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.protocol("WM_DELETE_WINDOW", lambda: [canvas.unbind_all("<MouseWheel>"), self.destroy()])

    def load_clients(self):
        """Cargar lista de clientes"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, first_name, last_name, dni FROM clients ORDER BY first_name")
        clients = cursor.fetchall()
        conn.close()
        
        self.clients_data = {}
        self.all_client_names = []
        
        for client in clients:
            display_name = f"{client['first_name']} {client['last_name']} - DNI: {client['dni']}"
            self.all_client_names.append(display_name)
            self.clients_data[display_name] = client['id']
            
    def search_client(self):
        """Buscar cliente y actualizar combobox"""
        search_term = self.entry_search.get().lower()
        
        if not search_term:
            self.client_combo['values'] = self.all_client_names
            messagebox.showinfo("Info", "Mostrando todos los clientes")
            return

        filtered_list = [
            name for name in self.all_client_names 
            if search_term in name.lower()
        ]
        
        if not filtered_list:
            messagebox.showwarning("Sin resultados", "No se encontraron clientes con ese criterio")
            self.client_combo.set('')
            self.client_combo['values'] = []
        else:
            self.client_combo['values'] = filtered_list
            self.client_combo.current(0)
            self.on_client_select(None)
            # Open dropdown
            self.client_combo.event_generate('<Down>')

    def on_client_select(self, event):
        """Cuando se selecciona un cliente"""
        selected = self.client_combo.get()
        if selected in self.clients_data:
            self.selected_client_id = self.clients_data[selected]

    def on_type_change(self, event):
        """Actualizar campos dinámicos según tipo de préstamo"""
        # Clear dynamic frame
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()
            
        loan_type = self.combo_type.get()
        
        # Load default interest rate
        config_map = {
            'empeno': 'loan1',
            'bancario': 'loan2',
            'rapidiario': 'loan3',
            'congelado': 'loan4'
        }
        config_key = config_map.get(loan_type, 'loan1')
        
        # Interest field is now left empty by default as requested
        self.entry_interest.delete(0, tk.END)
        # interest = get_setting(f'{config_key}_interest') or "5.0"
        # self.entry_interest.insert(0, interest)
        
        self.max_items = int(get_setting(f'{config_key}_max_items') or "3")
        self.max_amount = float(get_setting(f'{config_key}_max_amount') or "10000")
        
        # Reset pawn items
        self.pawn_items = []
        
        if loan_type == 'rapidiario':
            self.create_rapidiario_fields()
        elif loan_type in ['empeno', 'bancario']:
            self.create_collateral_fields(loan_type)
        elif loan_type == 'congelado':
            self.create_congelado_fields()

    def create_rapidiario_fields(self):
        """Campos para Rapidiario"""
        frame = tk.LabelFrame(self.dynamic_frame, text="Configuración Rapidiario",
                             font=("Segoe UI", 11, "bold"), padx=15, pady=10)
        frame.pack(fill=tk.X)
        
        tk.Label(frame, text=f"⚠️ Monto máximo: S/ {self.max_amount:.2f}",
                font=("Segoe UI", 9), fg="red").pack(anchor="w", pady=5)
        
        tk.Label(frame, text="Frecuencia de Pago:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 5))
        self.combo_freq = ttk.Combobox(frame, values=["Diario", "Semanal"],
                                       font=("Segoe UI", 10), state="readonly", width=20)
        self.combo_freq.current(0)
        self.combo_freq.pack(anchor="w", ipady=5)
        
        tk.Label(frame, text="📌 Préstamo a 30 días (excluyendo domingos)",
                font=("Segoe UI", 9), fg="#666").pack(anchor="w", pady=(10, 0))

    def create_collateral_fields(self, loan_type):
        """Campos para Casa de Empeño y Bancario (con garantías)"""
        frame = tk.LabelFrame(self.dynamic_frame, text="Garantías Prendarias",
                             font=("Segoe UI", 11, "bold"), padx=15, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text=f"⚠️ Requerido: Al menos 1 garantía (máximo {self.max_items})",
                font=("Segoe UI", 9), fg="red").pack(anchor="w", pady=5)
        
        # Items container
        self.items_container = tk.Frame(frame)
        self.items_container.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Add button
        tk.Button(frame, text="➕ Agregar Garantía", command=self.add_pawn_item,
                 bg='#2196F3', fg='white', font=("Segoe UI", 10, "bold"),
                 relief='flat', cursor='hand2', padx=15, pady=8).pack(anchor="w")
        
        # Add first item by default
        self.add_pawn_item()
        
        # For Bancario, add months field
        if loan_type == 'bancario':
            months_frame = tk.Frame(self.dynamic_frame)
            months_frame.pack(fill=tk.X, pady=(15, 0))
            
            tk.Label(months_frame, text="Número de Meses:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
            self.entry_months = ttk.Entry(months_frame, font=("Segoe UI", 10), width=10)
            self.entry_months.insert(0, "3")
            self.entry_months.pack(side=tk.LEFT)

    def create_congelado_fields(self):
        """Campos para Préstamo Congelado"""
        frame = tk.LabelFrame(self.dynamic_frame, text="Configuración Préstamo Congelado",
                             font=("Segoe UI", 11, "bold"), padx=15, pady=10)
        frame.pack(fill=tk.X)
        
        tk.Label(frame, text="Plazo en Meses:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=5)
        self.entry_frozen_months = ttk.Entry(frame, font=("Segoe UI", 10), width=10)
        self.entry_frozen_months.insert(0, "6")
        self.entry_frozen_months.pack(anchor="w", ipady=5)
        
        tk.Label(frame, text="📌 Préstamo con condiciones especiales",
                font=("Segoe UI", 9), fg="#666").pack(anchor="w", pady=(10, 0))

    def add_pawn_item(self):
        """Agregar un bien como garantía"""
        if len(self.pawn_items) >= self.max_items:
            messagebox.showwarning("Límite", f"Máximo {self.max_items} garantías permitidas")
            return
        
        item_frame = tk.LabelFrame(self.items_container, text=f"Garantía #{len(self.pawn_items) + 1}",
                                   font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        item_frame.pack(fill=tk.X, pady=5)
        
        # Row 1: Tipo y Marca
        row1 = tk.Frame(item_frame)
        row1.pack(fill=tk.X, pady=5)
        
        tk.Label(row1, text="Tipo de Bien:", font=("Segoe UI", 9, "bold"), width=15, anchor="w").pack(side=tk.LEFT)
        e_type = ttk.Combobox(row1, values=["Electrónico", "Joya", "Vehículo", "Mueble", "Herramienta", "Otro"],
                             font=("Segoe UI", 9), width=20)
        e_type.pack(side=tk.LEFT, padx=5)
        
        tk.Label(row1, text="Marca/Modelo:", font=("Segoe UI", 9, "bold"), width=15, anchor="w").pack(side=tk.LEFT, padx=(20, 0))
        e_brand = ttk.Entry(row1, font=("Segoe UI", 9), width=20)
        e_brand.pack(side=tk.LEFT, padx=5)
        
        # Row 2: Estado y Valor
        row2 = tk.Frame(item_frame)
        row2.pack(fill=tk.X, pady=5)
        
        tk.Label(row2, text="Estado:", font=("Segoe UI", 9, "bold"), width=15, anchor="w").pack(side=tk.LEFT)
        e_cond = ttk.Combobox(row2, values=["Nuevo", "Usado - Bueno", "Usado - Regular", "Dañado"],
                             font=("Segoe UI", 9), width=20)
        e_cond.current(1)
        e_cond.pack(side=tk.LEFT, padx=5)
        
        tk.Label(row2, text="Valor Mercado (S/):", font=("Segoe UI", 9, "bold"), width=15, anchor="w").pack(side=tk.LEFT, padx=(20, 0))
        e_val = ttk.Entry(row2, font=("Segoe UI", 9), width=20)
        e_val.pack(side=tk.LEFT, padx=5)
        
        # Row 3: Características
        row3 = tk.Frame(item_frame)
        row3.pack(fill=tk.X, pady=5)
        
        tk.Label(row3, text="Características:", font=("Segoe UI", 9, "bold"), width=15, anchor="w").pack(side=tk.LEFT)
        e_chars = ttk.Entry(row3, font=("Segoe UI", 9))
        e_chars.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Remove button
        if len(self.pawn_items) > 0:  # Allow removing if not the first one
            tk.Button(row3, text="🗑️ Eliminar", command=lambda: self.remove_pawn_item(item_frame),
                     bg='#f44336', fg='white', font=("Segoe UI", 8, "bold"),
                     relief='flat', cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        self.pawn_items.append({
            'frame': item_frame,
            'type': e_type,
            'brand': e_brand,
            'cond': e_cond,
            'val': e_val,
            'chars': e_chars
        })

    def remove_pawn_item(self, frame):
        """Eliminar una garantía"""
        for i, item in enumerate(self.pawn_items):
            if item['frame'] == frame:
                frame.destroy()
                self.pawn_items.pop(i)
                # Renumber remaining items
                for j, remaining in enumerate(self.pawn_items):
                    remaining['frame'].config(text=f"Garantía #{j + 1}")
                break

    def save(self):
        """Guardar el préstamo"""
        # Validations
        if not self.selected_client_id:
            messagebox.showerror("Error", "Debe seleccionar un cliente")
            return
        
        try:
            amount = float(self.entry_amount.get())
            interest = float(self.entry_interest.get())
        except ValueError:
            messagebox.showerror("Error", "Monto e interés deben ser números válidos")
            return
        
        loan_type = self.combo_type.get()
        
        # Validate amount for rapidiario
        if loan_type == 'rapidiario' and amount > self.max_amount:
            messagebox.showerror("Error", f"El monto excede el límite de S/ {self.max_amount:.2f}")
            return
        
        # Validate collateral for empeno and bancario
        if loan_type in ['empeno', 'bancario']:
            if not self.pawn_items:
                messagebox.showerror("Error", "Debe agregar al menos una garantía")
                return
            
            # Validate all fields are filled
            for item in self.pawn_items:
                if not item['type'].get() or not item['brand'].get() or not item['val'].get():
                    messagebox.showerror("Error", "Complete todos los campos de las garantías")
                    return
            
            # Validate total collateral value
            total_collateral = sum(float(item['val'].get() or 0) for item in self.pawn_items)
            if total_collateral < amount:
                if not messagebox.askyesno("Advertencia", 
                    f"El valor total de las garantías (S/ {total_collateral:.2f}) es menor que el monto del préstamo (S/ {amount:.2f}).\n\n¿Desea continuar?"):
                    return
        
        # Calculate loan info
        try:
            start_date = self.date_start.get_date()
            kwargs = {}
            
            if loan_type == 'rapidiario':
                kwargs['frecuencia'] = self.combo_freq.get()
            elif loan_type == 'bancario':
                kwargs['meses'] = int(self.entry_months.get())
            elif loan_type == 'congelado':
                kwargs['meses'] = int(self.entry_frozen_months.get())
            
            loan_info = obtener_info_prestamo(loan_type, amount, interest, start_date, **kwargs)
            
            # Save to database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get analyst_id from client
            cursor.execute("SELECT analyst_id FROM clients WHERE id = ?", (self.selected_client_id,))
            client_row = cursor.fetchone()
            analyst_id = client_row['analyst_id'] if client_row else None
            
            due_date = loan_info.get('fecha_vencimiento', start_date)
            
            cursor.execute("""
                INSERT INTO loans (client_id, loan_type, amount, interest_rate, start_date, due_date, analyst_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
            """, (self.selected_client_id, loan_type, amount, interest, start_date, due_date, analyst_id))
            
            loan_id = cursor.lastrowid
            
            # Save collateral
            if loan_type in ['empeno', 'bancario']:
                for item in self.pawn_items:
                    # Create a description from the item details for the legacy column
                    desc = f"{item['type'].get()} {item['brand'].get()} - {item['chars'].get()}"
                    
                    cursor.execute("""
                        INSERT INTO pawn_details (loan_id, item_type, brand, condition, market_value, characteristics, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (loan_id, item['type'].get(), item['brand'].get(), item['cond'].get(),
                         float(item['val'].get() or 0), item['chars'].get(), desc))
            
            # Save installments
            for num, due, amt in loan_info['cuotas']:
                cursor.execute("""
                    INSERT INTO installments (loan_id, number, due_date, amount, status)
                    VALUES (?, ?, ?, ?, 'pending')
                """, (loan_id, num, due, amt))
            
            # Log action
            user_id = self.parent.user_data.get('id') if hasattr(self.parent, 'user_data') else None
            log_action(user_id, "Crear Préstamo",
                      f"Préstamo {loan_type} #{loan_id} - Cliente ID {self.selected_client_id} - S/ {amount:.2f}")
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Éxito",
                f"Préstamo registrado correctamente\n\n"
                f"ID: {loan_id}\n"
                f"Total a pagar: S/ {loan_info['total_pagar']:.2f}\n"
                f"Cuotas: {len(loan_info['cuotas'])}")
            
            if self.callback:
                self.callback()
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar préstamo:\n{str(e)}")
