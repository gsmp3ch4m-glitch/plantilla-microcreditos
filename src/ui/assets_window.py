import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from database import get_db_connection
from ui.ui_utils import apply_styles, ModernButton
from ui.date_picker import DateEntry
from datetime import date

class AssetsWindow(tk.Toplevel):
    def __init__(self, parent, user_data):
        super().__init__(parent)
        self.title("Gestión de Activos")
        self.user_data = user_data
        
        # Window Setup
        window_width = 1100
        window_height = 700
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        # Apply Theme
        apply_styles(self)
        
        # Data
        self.fixed_assets_data = []
        
        self.create_widgets()
        
    def create_widgets(self):
        # Header
        header_frame = tk.Frame(self, bg="#009688", height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="💰 Gestión de Activos (Contabilidad)", font=("Segoe UI", 16, "bold"), fg="white", bg="#009688").pack(side=tk.LEFT, padx=20)
        
        # Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.tab_dashboard = tk.Frame(self.notebook, bg="#f5f5f5")
        self.tab_fixed = tk.Frame(self.notebook, bg="#f5f5f5")
        self.tab_receivables = tk.Frame(self.notebook, bg="#f5f5f5")
        self.tab_cash = tk.Frame(self.notebook, bg="#f5f5f5")
        
        # New Order: Cash, Receivables, Fixed, Dashboard
        self.notebook.add(self.tab_cash, text="💵 Efectivo y Cuentas")
        self.notebook.add(self.tab_receivables, text="📉 Cuentas por Cobrar")
        self.notebook.add(self.tab_fixed, text="🏢 Activos Fijos")
        self.notebook.add(self.tab_dashboard, text="📊 Resumen")
        
        self.setup_dashboard_tab()
        self.setup_fixed_assets_tab()
        self.setup_receivables_tab()
        self.setup_cash_tab()
        
        # Initial Data Load
        self.refresh_all()
        
    def setup_dashboard_tab(self):
        # Refresh logic contained in load_dashboard_data
        self.lbl_total_assets = tk.Label(self.tab_dashboard, text="Cargando...", font=("Segoe UI", 24, "bold"))
        self.lbl_total_assets.pack(pady=20)
        
        # Cards container
        cards_frame = tk.Frame(self.tab_dashboard, bg="#f5f5f5")
        cards_frame.pack(fill=tk.X, padx=20, pady=20)
        
        self.card_fixed = self.create_summary_card(cards_frame, "Activos Fijos", "#009688")
        self.card_receivables = self.create_summary_card(cards_frame, "Cuentas por Cobrar", "#E91E63")
        self.card_fixed = self.create_summary_card(cards_frame, "Activos Fijos", "#009688")
        self.card_receivables = self.create_summary_card(cards_frame, "Cuentas por Cobrar", "#E91E63")
        self.card_cash = self.create_summary_card(cards_frame, "Efectivo y Cuentas", "#4CAF50")
        
        self.card_fixed.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        self.card_receivables.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        self.card_cash.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        tk.Button(self.tab_dashboard, text="🔄 Actualizar Datos", command=self.refresh_all).pack(pady=20)

    def create_summary_card(self, parent, title, color):
        frame = tk.Frame(parent, bg="white", highlightbackground=color, highlightthickness=2)
        tk.Label(frame, text=title, font=("Segoe UI", 12, "bold"), fg=color, bg="white").pack(pady=(10,5))
        lbl_value = tk.Label(frame, text="S/ 0.00", font=("Segoe UI", 18, "bold"), fg="#333333", bg="white")
        lbl_value.pack(pady=(0,10))
        frame.lbl_value = lbl_value # Store reference
        return frame

    def setup_fixed_assets_tab(self):
        # Container
        container = tk.Frame(self.tab_fixed, bg="#f5f5f5")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Toolbar
        toolbar = tk.Frame(container, bg="#f5f5f5")
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        tk.Button(toolbar, text="➕ Agregar Inversión/Gasto", command=self.add_fixed_asset, bg="#4CAF50", fg="white", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        tk.Button(toolbar, text="✏️ Editar", command=self.edit_fixed_asset, bg="#FFC107", fg="black", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=10)
        tk.Button(toolbar, text="🗑️ Eliminar", command=self.delete_fixed_asset, bg="#F44336", fg="white", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        
        # --- Section 1: Equipment ---
        lbl_eq = tk.Label(container, text="🏢 Equipamiento y Bienes (Motos, Muebles, Computadoras)", font=("Segoe UI", 11, "bold"), bg="#f5f5f5", fg="#0277BD")
        lbl_eq.pack(anchor="w", pady=(5, 5))
        
        cols = ("ID", "Nombre", "Descripción", "Fecha Compra", "Valor")
        self.tree_fixed = ttk.Treeview(container, columns=cols, show='headings', height=6)
        
        self.tree_fixed.heading("ID", text="ID")
        self.tree_fixed.heading("Nombre", text="Nombre")
        self.tree_fixed.heading("Descripción", text="Descripción")
        self.tree_fixed.heading("Fecha Compra", text="Fecha")
        self.tree_fixed.heading("Valor", text="Costo")
        
        self.tree_fixed.column("ID", width=40)
        self.tree_fixed.column("Nombre", width=150)
        self.tree_fixed.column("Descripción", width=250)
        self.tree_fixed.column("Fecha Compra", width=100)
        self.tree_fixed.column("Valor", width=100, anchor="e")
        
        self.tree_fixed.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # --- Section 2: Startup Expenses ---
        lbl_st = tk.Label(container, text="📜 Gastos de Inicio / Constitución (Licencias, Local, Legal)", font=("Segoe UI", 11, "bold"), bg="#f5f5f5", fg="#E65100")
        lbl_st.pack(anchor="w", pady=(5, 5))
        
        self.tree_startup = ttk.Treeview(container, columns=cols, show='headings', height=6)
        
        self.tree_startup.heading("ID", text="ID")
        self.tree_startup.heading("Nombre", text="Concepto")
        self.tree_startup.heading("Descripción", text="Detalle")
        self.tree_startup.heading("Fecha Compra", text="Fecha")
        self.tree_startup.heading("Valor", text="Costo")
        
        self.tree_startup.column("ID", width=40)
        self.tree_startup.column("Nombre", width=150)
        self.tree_startup.column("Descripción", width=250)
        self.tree_startup.column("Fecha Compra", width=100)
        self.tree_startup.column("Valor", width=100, anchor="e")
        
        self.tree_startup.pack(fill=tk.BOTH, expand=True, pady=(0, 0))
        
        # Footer Total
        frame_total = tk.Frame(self.tab_fixed, bg="#009688", height=40)
        frame_total.pack(fill=tk.X, side=tk.BOTTOM)
        frame_total.pack_propagate(False)
        
        tk.Label(frame_total, text="💰 TOTAL INVERSIÓN (Bienes + Gastos):", font=("Segoe UI", 12, "bold"), fg="white", bg="#009688").pack(side=tk.LEFT, padx=20)
        self.lbl_fixed_total = tk.Label(frame_total, text="S/ 0.00", font=("Segoe UI", 16, "bold"), fg="white", bg="#009688")
        self.lbl_fixed_total.pack(side=tk.RIGHT, padx=20)

    def setup_receivables_tab(self):
        # Container
        container = tk.Frame(self.tab_receivables, bg="#f5f5f5")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Toolbar
        toolbar = tk.Frame(container, bg="#f5f5f5")
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        tk.Button(toolbar, text="➕ Agregar Deuda Manual", command=self.add_manual_receivable, bg="#4CAF50", fg="white", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        tk.Button(toolbar, text="✏️ Editar Manual", command=self.edit_manual_receivable, bg="#FFC107", fg="black", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=10)
        tk.Button(toolbar, text="🗑️ Eliminar Manual", command=self.delete_manual_receivable, bg="#F44336", fg="white", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        
        # Summary Label (Right aligned in toolbar or below)
        self.lbl_receivables_summary = tk.Label(toolbar, text="Total: S/ 0.00", font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="#333")
        self.lbl_receivables_summary.pack(side=tk.RIGHT)
        
        # Table
        # Cols: Source, ID, Client, Modality, Lent, Total Debt, Paid, Balance, Cap Pend, Int Pend, Status
        cols = ("Origen", "ID", "Cliente", "Modalidad", "Prestado", "Total Deuda", "Pagado", "Saldo", "Cap. Pend", "Int. Pend", "Estado")
        self.tree_receivables = ttk.Treeview(container, columns=cols, show='headings')
        
        self.tree_receivables.heading("Origen", text="Tipo")
        self.tree_receivables.heading("ID", text="ID")
        self.tree_receivables.heading("Cliente", text="Cliente")
        self.tree_receivables.heading("Modalidad", text="Modalidad")
        self.tree_receivables.heading("Prestado", text="Prestado")
        self.tree_receivables.heading("Total Deuda", text="Total Deuda")
        self.tree_receivables.heading("Pagado", text="Pagado")
        self.tree_receivables.heading("Saldo", text="Saldo")
        self.tree_receivables.heading("Cap. Pend", text="Cap. Pend")
        self.tree_receivables.heading("Int. Pend", text="Int. Pend")
        self.tree_receivables.heading("Estado", text="Estado")
        
        self.tree_receivables.column("Origen", width=60, anchor="center")
        self.tree_receivables.column("ID", width=40, anchor="center")
        self.tree_receivables.column("Cliente", width=200)
        self.tree_receivables.column("Modalidad", width=100)
        self.tree_receivables.column("Prestado", width=80, anchor="e")
        self.tree_receivables.column("Total Deuda", width=80, anchor="e")
        self.tree_receivables.column("Pagado", width=80, anchor="e")
        self.tree_receivables.column("Saldo", width=80, anchor="e")
        self.tree_receivables.column("Cap. Pend", width=80, anchor="e")
        self.tree_receivables.column("Int. Pend", width=80, anchor="e")
        self.tree_receivables.column("Estado", width=80, anchor="center")
            
        self.tree_receivables.pack(fill=tk.BOTH, expand=True)
        
    def setup_cash_tab(self):
        # --- Capital Tracking UI ---
        
        # Summary Frame (Top)
        frame_summary = tk.Frame(self.tab_cash, bg="#f5f5f5")
        frame_summary.pack(fill=tk.X, padx=20, pady=20)
        
        # Note: We need create_summary_card available
        
        # Card: Capital Cash
        self.card_cap_cash = self.create_summary_card(frame_summary, "Capital Efectivo (Caja)", "#4CAF50")
        self.card_cap_cash.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Card: Capital Bank
        self.card_cap_bank = self.create_summary_card(frame_summary, "Capital Cuenta/Yape", "#2196F3")
        self.card_cap_bank.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        # Action Button - Protected
        btn_add = tk.Button(frame_summary, text="➕ Agregar Capital", command=lambda: self.require_admin(self.show_capital_modal), bg="#FF9800", fg="white", font=("Segoe UI", 12, "bold"))
        btn_add.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # History Table (Bottom)
        lbl_hist = tk.Label(self.tab_cash, text="Historial de Inyección de Capital", font=("Segoe UI", 12, "bold"), bg="#f5f5f5")
        lbl_hist.pack(anchor="w", padx=20, pady=(10, 5))
        
        cols = ("ID", "Fecha", "Destino", "Nota", "Monto")
        self.tree_capital = ttk.Treeview(self.tab_cash, columns=cols, show='headings', height=10, displaycolumns=("Fecha", "Destino", "Nota", "Monto"))
        
        self.tree_capital.heading("Fecha", text="Fecha")
        self.tree_capital.heading("Destino", text="Destino")
        self.tree_capital.heading("Nota", text="Nota")
        self.tree_capital.heading("Monto", text="Monto")
        
        self.tree_capital.column("Fecha", width=100)
        self.tree_capital.column("Destino", width=150)
        self.tree_capital.column("Nota", width=300)
        self.tree_capital.column("Monto", width=120, anchor="e")
        
        self.tree_capital.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Context Menu
        self.menu_capital = tk.Menu(self, tearoff=0)
        self.menu_capital.add_command(label="✏️ Editar", command=self.on_edit_capital)
        self.menu_capital.add_command(label="🗑️ Eliminar", command=self.on_delete_capital)
        
        self.tree_capital.bind("<Button-3>", self.show_context_menu)
        
        # Footer Total
        frame_total = tk.Frame(self.tab_cash, bg="#009688", height=50)
        frame_total.pack(fill=tk.X, side=tk.BOTTOM)
        frame_total.pack_propagate(False)
        
        tk.Label(frame_total, text="💰 TOTAL CAPITAL REGISTRADO:", font=("Segoe UI", 14, "bold"), fg="white", bg="#009688").pack(side=tk.LEFT, padx=20)
        self.lbl_capital_total = tk.Label(frame_total, text="S/ 0.00", font=("Segoe UI", 18, "bold"), fg="white", bg="#009688")
        self.lbl_capital_total.pack(side=tk.RIGHT, padx=20)

    def refresh_all(self):
        self.load_fixed_assets()
        self.load_receivables()
        self.load_cash_info()
        # self.load_bank_accounts() # Removed operational load
        self.update_dashboard_summary()

    def load_fixed_assets(self):
        # Clear both trees
        for item in self.tree_fixed.get_children():
            self.tree_fixed.delete(item)
        for item in self.tree_startup.get_children():
            self.tree_startup.delete(item)
            
        conn = get_db_connection()
        cursor = conn.cursor()
        # Ensure category column exists (handled in init_db, but safe query)
        try:
            cursor.execute("SELECT id, name, description, purchase_date, value, category FROM fixed_assets WHERE status='active'")
        except sqlite3.OperationalError:
            # Fallback if migration hasn't run in this session
            cursor.execute("SELECT id, name, description, purchase_date, value, 'equipment' as category FROM fixed_assets WHERE status='active'")
            
        rows = cursor.fetchall()
        conn.close()
        
        total_val = 0.0
        
        for row in rows:
            cat = row['category'] if 'category' in row.keys() else 'equipment'
            
            # Values tuple
            # row: id, name, desc, date, value, category
            vals = (row['id'], row['name'], row['description'], row['purchase_date'], f"S/ {row['value']:,.2f}")
            
            if cat == 'startup':
                self.tree_startup.insert('', tk.END, values=vals)
            else:
                self.tree_fixed.insert('', tk.END, values=vals)
                
            total_val += row['value']
            
        self.lbl_fixed_total.config(text=f"S/ {total_val:,.2f}")
        
        # Update main Dashboard card too
        try:
            self.card_fixed.lbl_value.config(text=f"S/ {total_val:,.2f}")
        except:
            pass

    def load_receivables(self):
        for item in self.tree_receivables.get_children():
            self.tree_receivables.delete(item)
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        total_receivable = 0.0
        total_capital = 0.0
        total_interest = 0.0
        
        # 1. Load System Loans
        try:
            cursor.execute("""
                SELECT l.id, c.first_name || ' ' || c.last_name as client_name, 
                    l.loan_type, l.amount as principal, l.total_payment, l.status
                FROM loans l
                JOIN clients c ON l.client_id = c.id
                WHERE l.status IN ('active', 'overdue')
            """)
            
            system_loans = cursor.fetchall()
            
            for loan in system_loans:
                try:
                    cursor.execute("SELECT SUM(amount) FROM transactions WHERE loan_id = ? AND type='income'", (loan['id'],))
                    res = cursor.fetchone()
                    paid = res[0] if res and res[0] else 0.0
                    
                    principal = loan['principal']
                    total_due = loan['total_payment']
                    expected_interest = total_due - principal
                    
                    # Estimate capital vs interest paid: Proportional? Or Capital first?
                    # Simplified logic: Balance = Outstanding Capital + Outstanding Interest
                    # If paid < principal: Outstanding Capital = Principal - Paid, Outstanding Interest = Full Interest
                    # If paid >= principal: Outstanding Capital = 0, Outstanding Interest = Total Due - Paid
                    
                    if paid < principal:
                        balance_capital = principal - paid
                        balance_interest = expected_interest
                    else:
                        balance_capital = 0
                        balance_interest = total_due - paid
                        
                    balance = balance_capital + balance_interest
                    if balance < 0.01: continue
                    
                    # Calculate total balance for the row
                    balance = balance_capital + balance_interest

                    status_es = 'Activo' if loan['status'] == 'active' else 'Vencido'
                    
                    self.tree_receivables.insert('', tk.END, values=(
                        "SISTEMA",
                        f"L{loan['id']}",
                        loan['client_name'], 
                        loan['loan_type'], 
                        f"S/ {principal:,.2f}",
                        f"S/ {total_due:,.2f}",
                        f"S/ {paid:,.2f}",
                        f"S/ {balance:,.2f}", # New: Saldo
                        f"S/ {balance_capital:,.2f}", 
                        f"S/ {balance_interest:,.2f}",
                        status_es
                    ))
                    total_receivable += (balance_capital + balance_interest)
                    total_capital += balance_capital
                    total_interest += balance_interest
                except Exception as e:
                    print(f"Error processing loan {loan['id']}: {e}")
        except Exception:
            pass

        # 2. Load Manual Receivables
        try:
             cursor.execute("SELECT * FROM manual_receivables")
             manual_rows = cursor.fetchall()
             
             for row in manual_rows:
                 status_es = 'Pagado' if row['status'] == 'paid' else ('Vencido' if row['status'] == 'overdue' else 'Pendiente')
                 
                 # Logic for manual breakdown
                 lent = row['amount_lent']
                 total_debt = row['total_debt']
                 interest = row['interest'] # Logic check: lent + interest should be total_debt approx
                 paid = row['paid_amount']
                 balance = row['balance']
                 
                 # Recalculate breakdown dynamically based on paid amount
                 if row['modality'] == 'Rapidiario' and total_debt > 0:
                      # Proportional split logic matches calculate_totals
                      cap_ratio = lent / total_debt
                      int_ratio = interest / total_debt
                      
                      cap_paid = paid * cap_ratio
                      int_paid = paid * int_ratio
                      
                      bal_cap = max(0, lent - cap_paid)
                      bal_int = max(0, interest - int_paid)
                 elif paid < lent:
                     bal_cap = lent - paid
                     bal_int = interest
                 else:
                     bal_cap = 0
                     bal_int = max(0, total_debt - paid)
                 
                 # If explicit balance in DB is different from calc, trust DB for total but use logic solely for breakdown display?
                 # Let's trust logic derived from balance for consistency with simple math
                 
                 self.tree_receivables.insert('', tk.END, values=(
                    "MANUAL",
                    f"M{row['id']}",
                    row['client_name'],
                    row['modality'],
                    f"S/ {lent:,.2f}",
                    f"S/ {total_debt:,.2f}",
                    f"S/ {paid:,.2f}",
                    f"S/ {balance:,.2f}", # New: Saldo (Total Pending)
                    f"S/ {bal_cap:,.2f}", 
                    f"S/ {bal_int:,.2f}", 
                    status_es
                 ))
                 if balance > 0:
                     total_receivable += balance
                     total_capital += bal_cap
                     total_interest += bal_int
             
        except sqlite3.OperationalError:
            pass 

        conn.close()
        summary_text = (f"Total por Cobrar: S/ {total_receivable:,.2f}  |  "
                        f"Capital: S/ {total_capital:,.2f}  |  "
                        f"Interés: S/ {total_interest:,.2f}")
        self.lbl_receivables_summary.config(text=summary_text)
        self.total_receivable_val = total_receivable

    def add_manual_receivable(self):
        self.require_admin(lambda: self.show_receivable_modal())

    def edit_manual_receivable(self):
        sel = self.tree_receivables.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Seleccione un registro")
            return
            
        values = self.tree_receivables.item(sel[0])['values']
        origin = values[0]
        rec_id_str = values[1]
        
        if origin != "MANUAL":
            messagebox.showinfo("Información", "Solo se pueden editar registros manuales aquí.\nPara préstamos del sistema, vaya al módulo de Préstamos.")
            return
            
        rec_id = int(rec_id_str[1:])
        self.require_admin(lambda: self.show_receivable_modal(rec_id))

    def delete_manual_receivable(self):
        sel = self.tree_receivables.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Seleccione un registro")
            return
            
        values = self.tree_receivables.item(sel[0])['values']
        origin = values[0]
        rec_id_str = values[1]
        
        if origin != "MANUAL":
            messagebox.showinfo("Información", "Solo se pueden eliminar registros manuales aquí.")
            return
            
        def delete_action():
            if not messagebox.askyesno("Confirmar", "¿Eliminar este registro manual?"):
                return
                
            rec_id = int(rec_id_str[1:])
            
            conn = get_db_connection()
            try:
                conn.execute("DELETE FROM manual_receivables WHERE id=?", (rec_id,))
                conn.commit()
                messagebox.showinfo("Éxito", "Eliminado correctamente")
                self.load_receivables()
                self.update_dashboard_summary()
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                conn.close()

        self.require_admin(delete_action)

    def show_receivable_modal(self, rec_id=None):
        modal = tk.Toplevel(self)
        title = "Editar Deuda Manual" if rec_id else "Agregar Deuda Manual"
        modal.title(title)
        modal.geometry("450x600") # Resized for better fit
        
        # --- SCROLLABLE SUPPORT ---
        # 1. Main container
        main_frame = tk.Frame(modal)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 2. Canvas
        canvas = tk.Canvas(main_frame)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 3. Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 4. Configure Canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 5. Inner Frame
        container = tk.Frame(canvas, padx=20, pady=20)
        
        # Window in canvas
        window_id = canvas.create_window((0, 0), window=container, anchor="nw")
        
        def configure_scroll(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Adjust window width to canvas width if needed
            canvas.itemconfig(window_id, width=event.width)
            
        container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", configure_scroll)

        # Mousewheel
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
        # Bind mousewheel only when hovering modal or global? 
        # Global bind for modal
        modal.bind_all("<MouseWheel>", on_mousewheel)
        modal.bind("<Destroy>", lambda e: modal.unbind_all("<MouseWheel>"))


        # --- FORM FIELDS (Inside container) ---
        
        def add_row(parent, label_text, widget_class, **kwargs):
            f = tk.Frame(parent)
            f.pack(fill=tk.X, pady=2)
            tk.Label(f, text=label_text, anchor="w", font=("Segoe UI", 9, "bold")).pack(anchor="w")
            w = widget_class(f, **kwargs)
            w.pack(fill=tk.X)
            return w

        # Client
        tk.Label(container, text="Cliente:", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 2))
        frm_client = tk.Frame(container)
        frm_client.pack(fill=tk.X, pady=(0, 5))
        
        entry_client = tk.Entry(frm_client)
        entry_client.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        selected_client_id = tk.IntVar(value=0)
        
        def search_client():
            search_term = entry_client.get().strip()
            if not search_term: return
            
            popup = tk.Toplevel(modal)
            popup.title("Resultados")
            popup.geometry("600x400")
            
            lb = tk.Listbox(popup, font=("Segoe UI", 11))
            lb.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            conn = get_db_connection()
            rows = conn.execute("SELECT id, first_name, last_name, dni FROM clients WHERE first_name LIKE ? OR last_name LIKE ? OR dni LIKE ?", 
                               (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%')).fetchall()
            conn.close()
            
            if not rows:
                lb.insert(tk.END, "No se encontraron clientes.")
            else:
                for r in rows:
                    lb.insert(tk.END, f"{r['first_name']} {r['last_name']} ({r['dni']}) - ID:{r['id']}")
            
            def on_select(evt):
                if not rows: return
                w = evt.widget
                if not w.curselection(): return
                idx = int(w.curselection()[0])
                txt = w.get(idx)
                try:
                    cid = int(txt.split("ID:")[-1])
                    name = txt.split(" (")[0]
                    selected_client_id.set(cid)
                    entry_client.delete(0, tk.END)
                    entry_client.insert(0, name)
                    popup.destroy()
                except: pass
                
            lb.bind('<<ListboxSelect>>', on_select)

        tk.Button(frm_client, text="🔍", command=search_client, relief="flat", bg="#ddd").pack(side=tk.LEFT, padx=5)

        # Basic Info
        entry_concept = add_row(container, "Concepto:", tk.Entry)
        
        tk.Label(container, text="Modalidad:", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(5, 2))
        cb_modality = ttk.Combobox(container, values=["Rapidiario", "Casa de Empeño", "Bancarizado", "Congelado"], state="readonly")
        cb_modality.current(0)
        cb_modality.pack(fill=tk.X, pady=(0, 5))
        
        # Financials
        frame_nums = tk.Frame(container)
        frame_nums.pack(fill=tk.X, pady=5)
        
        f1 = tk.Frame(frame_nums); f1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        tk.Label(f1, text="Monto Prestado (S/):", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        entry_lent = tk.Entry(f1)
        entry_lent.pack(fill=tk.X)
        
        f2 = tk.Frame(frame_nums); f2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0))
        tk.Label(f2, text="Tasa Interés (%):", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        entry_rate = tk.Entry(f2); entry_rate.insert(0, "10.0")
        entry_rate.pack(fill=tk.X)
        
        # Dynamic Fields Wrapper
        frame_dynamic = tk.Frame(container)
        frame_dynamic.pack(fill=tk.X, pady=5)
        
        # Re-usable dynamic widgets
        lbl_paid = tk.Label(frame_dynamic, text="Monto Ya Pagado (S/):", font=("Segoe UI", 9, "bold"))
        entry_paid = tk.Entry(frame_dynamic); entry_paid.insert(0, "0.0")
        
        lbl_times = tk.Label(frame_dynamic, text="Veces Int. Pagado:", font=("Segoe UI", 9, "bold"))
        entry_times = tk.Entry(frame_dynamic); entry_times.insert(0, "0")
        
        # Date
        tk.Label(container, text="Fecha Préstamo:", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(5, 2))
        date_loan = DateEntry(container)
        date_loan.pack(fill=tk.X)
        
        # Calculation Result Panel
        lbl_info = tk.Label(container, text="...", fg="#333", justify=tk.LEFT, bg="#e8f5e9", relief="groove", padx=10, pady=10)
        lbl_info.pack(fill=tk.BOTH, pady=15)
        
        # SAVE BUTTON - Explicitly packed at bottom of frame
        btn_save = tk.Button(container, text="GUARDAR DEUDA", command=lambda: save(), 
                             bg="#2E7D32", fg="white", font=("Segoe UI", 11, "bold"), height=2, cursor="hand2")
        btn_save.pack(fill=tk.X, pady=(5, 30)) # Extra padding at bottom
        
        
        # LOGIC
        def update_dynamic_fields(event=None):
            for w in frame_dynamic.winfo_children(): w.pack_forget()
            mod = cb_modality.get()
            if mod == "Rapidiario":
                lbl_paid.pack(anchor="w"); entry_paid.pack(fill=tk.X)
            elif mod == "Casa de Empeño":
                lbl_times.pack(anchor="w"); entry_times.pack(fill=tk.X)
            else:
                lbl_paid.pack(anchor="w"); entry_paid.pack(fill=tk.X)
            calculate_totals()

        cb_modality.bind("<<ComboboxSelected>>", update_dynamic_fields)

        def calculate_totals(event=None):
            try:
                mod = cb_modality.get()
                lent = float(entry_lent.get() or 0)
                rate = float(entry_rate.get() or 0)
                
                # FIX: get_date returns string, we need object for math
                start_date = date_loan.get_date_obj() 
                if not start_date:
                    lbl_info.config(text="Seleccione fecha válida", fg="red")
                    return None
                
                info_text = ""
                total_debt = 0; balance = 0; interest = 0; paid = 0
                
                from datetime import date, timedelta
                today = date.today()
                d_due = start_date 
                
                if mod == "Rapidiario":
                    interest = lent * (rate / 100)
                    total_debt = lent + interest
                    paid = float(entry_paid.get() or 0)
                    balance = max(0, total_debt - paid)
                    
                if mod == "Rapidiario":
                    interest = lent * (rate / 100)
                    total_debt = lent + interest
                    paid = float(entry_paid.get() or 0)
                    balance = max(0, total_debt - paid)
                    
                    d_due = start_date + timedelta(days=30)
                    days = (d_due - today).days

                    st = f"{days} días restantes" if days >= 0 else f"VENCIDO {abs(days)} días"
                    
                    # Proportional Split Logic (User Requirement)
                    # Every payment covers proportional parts of Capital and Interest
                    if total_debt > 0:
                        cap_ratio = lent / total_debt
                        int_ratio = interest / total_debt
                    else:
                        cap_ratio = 1; int_ratio = 0
                        
                    cap_paid = paid * cap_ratio
                    int_paid = paid * int_ratio
                    
                    cap_pend = max(0, lent - cap_paid)
                    int_pend = max(0, interest - int_paid)
                    
                    info_text = (f"Deuda Total: S/ {total_debt:.2f} | Saldo: S/ {balance:.2f}\n"
                                 f"ABONADO: S/ {paid:.2f} (Int: {int_paid:.2f} | Cap: {cap_paid:.2f})\n"
                                 f"PENDIENTE: Cap: S/ {cap_pend:.2f} | Int: S/ {int_pend:.2f}\n"
                                 f"Estado: {st}")
                                 
                elif mod == "Casa de Empeño":
                    times = float(entry_times.get() or 0)
                    months = (today.year - start_date.year)*12 + today.month - start_date.month
                    if today.day > start_date.day: months += 1
                    months = max(1, months) if today >= start_date else 0
                    
                    m_int = lent * (rate / 100)
                    tot_int_gen = months * m_int
                    int_paid = times * m_int
                    int_debt = tot_int_gen - int_paid
                    
                    total_debt = lent + int_debt 
                    balance = total_debt
                    interest = tot_int_gen
                    paid = int_paid 
                    
                    try:
                        next_m = today.month + (1 if today.day >= start_date.day else 0)
                        next_y = today.year + (1 if next_m > 12 else 0)
                        next_m = 1 if next_m > 12 else next_m
                        d_due = date(next_y, next_m, start_date.day)
                    except: d_due = date(today.year, today.month, 28)

                    info_text = (f"Meses: {months} | Int. Men: S/ {m_int:.2f}\n"
                                 f"Int. Generado: S/ {tot_int_gen:.2f} | Pagado: S/ {int_paid:.2f}\n"
                                 f"DEUDA TOTAL: S/ {balance:.2f} (Cap + Int. Pend)")
                
                else:
                    interest = lent * (rate/100)
                    total_debt = lent + interest
                    paid = float(entry_paid.get() or 0)
                    balance = total_debt - paid
                    info_text = f"Saldo: S/ {balance:.2f}"
                
                lbl_info.config(text=info_text, fg="#000")
                return lent, interest, total_debt, paid, balance, start_date, d_due
                
            except Exception as e:
                lbl_info.config(text=f"Error: {str(e)}", fg="red")
                return None

        # Bindings
        for w in [entry_lent, entry_rate, entry_paid, entry_times]:
            w.bind('<KeyRelease>', calculate_totals)
        date_loan.bind("<<DateEntrySelected>>", calculate_totals)
        
        # Init Data
        conn = get_db_connection()
        if rec_id:
            row = conn.execute("SELECT * FROM manual_receivables WHERE id=?", (rec_id,)).fetchone()
            if row:
                entry_date_loan_str = row['loan_date']
                entry_client.insert(0, row['client_name'])
                if row['client_id']: selected_client_id.set(row['client_id'])
                entry_concept.insert(0, row['concept'] or "")
                cb_modality.set(row['modality'] or "Rapidiario")
                entry_lent.insert(0, str(row['amount_lent']))
                
                if row['modality'] == "Rapidiario":
                    entry_paid.delete(0, tk.END); entry_paid.insert(0, str(row['paid_amount']))
        conn.close()
        
        update_dynamic_fields()

        def save():
            client_name = entry_client.get()
            cid = selected_client_id.get()
            concept = entry_concept.get()
            modality = cb_modality.get()
            
            res = calculate_totals()
            if not res: return
            lent, interest, total_debt, paid, balance, d_loan, d_due = res
            
            status = 'paid' if balance <= 0.1 else ('overdue' if date.today() > d_due else 'pending')
            
            # Serialize dates for SQLite
            d_loan_str = d_loan.isoformat() if d_loan else None
            d_due_str = d_due.isoformat() if d_due else None
            
            conn = get_db_connection()
            try:
                if rec_id:
                    conn.execute("""UPDATE manual_receivables SET client_name=?, client_id=?, concept=?, modality=?, amount_lent=?, interest=?, total_debt=?, paid_amount=?, balance=?, status=?, loan_date=?, due_date=? WHERE id=?""", 
                                (client_name, cid if cid else None, concept, modality, lent, interest, total_debt, paid, balance, status, d_loan_str, d_due_str, rec_id))
                else:
                     conn.execute("""INSERT INTO manual_receivables (client_name, client_id, concept, modality, amount_lent, interest, total_debt, paid_amount, balance, status, loan_date, due_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                                (client_name, cid if cid else None, concept, modality, lent, interest, total_debt, paid, balance, status, d_loan_str, d_due_str))
                conn.commit()
                messagebox.showinfo("Éxito", "Guardado correctamente")
                modal.destroy()
                self.load_receivables()
                self.update_dashboard_summary()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {str(e)}")
            finally:
                conn.close()

    def load_receivables_deprecated(self):
        for item in self.tree_receivables.get_children():
            self.tree_receivables.delete(item)
            
        conn = get_db_connection()
        cursor = conn.cursor()
        # Query to calculate outstanding debt
        # Logic: Loan Amount + Interest - Paid Amount = Outstanding
        # Note: This is an estimation. Real logic might depend on installments.
        # Let's use installments if possible or loan totals.
        # Simple Approach: Scan active loans.
        
        cursor.execute("""
            SELECT l.id, c.first_name || ' ' || c.last_name as client_name, 
                   l.loan_type, l.amount, l.interest_rate, l.status
            FROM loans l
            JOIN clients c ON l.client_id = c.id
            WHERE l.status = 'active' OR l.status = 'overdue'
        """)
        loans = cursor.fetchall()
        
        total_receivable = 0
        
        for loan in loans:
            loan_id = loan['id']
            principal = loan['amount']
            # Calculate total expected payment (Principal + Interest)
            # This depends on how interest is stored (percent vs flat). Assuming percent for now or simple interest logic
            # For simplicity in this view, let's look at installments table if exists
            
            cursor.execute("SELECT SUM(amount) as total_due, SUM(paid_amount) as total_paid FROM installments WHERE loan_id = ?", (loan_id,))
            inst_data = cursor.fetchone()
            
            if inst_data and inst_data['total_due']:
                total_due = inst_data['total_due']
                paid = inst_data['total_paid'] or 0
                balance = total_due - paid
            else:
                 # Fallback if no installments generated yet
                total_due = principal # Assume at least principal
                paid = 0
                balance = principal
            
            if balance > 0.01: # Filter fully paid floating point diffs
                # Traducir estado de préstamo
                loan_status_map = {
                    'active': 'Activo',
                    'overdue': 'Vencido',
                    'paid': 'Pagado'
                }
                status_es = loan_status_map.get(loan['status'], loan['status'])
                
                self.tree_receivables.insert('', tk.END, values=(
                    loan['client_name'], 
                    loan['loan_type'], 
                    f"S/ {principal:.2f}",
                    "-", # Interest detail complex to calc here
                    f"S/ {total_due:.2f}",
                    f"S/ {paid:.2f}",
                    f"S/ {balance:.2f}",
                    status_es
                ))
                total_receivable += balance

        conn.close()
        self.lbl_receivables_summary.config(text=f"Total por Cobrar: S/ {total_receivable:,.2f}")
        self.total_receivable_val = total_receivable

    def load_cash_info(self):
        # Now used to load CAPITAL history
        for item in self.tree_capital.get_children():
            self.tree_capital.delete(item)
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Load Capital Entries
        cursor.execute("""
            SELECT c.id, c.entry_date, c.target_type, c.amount, c.description, b.bank_name 
            FROM capital_entries c
            LEFT JOIN bank_accounts b ON c.target_id = b.id
            ORDER BY c.entry_date DESC, c.id DESC
        """)
        rows = cursor.fetchall()
        
        total_cap_cash = 0.0
        total_cap_bank = 0.0
        
        for row in rows:
            tgt = "Efectivo (Caja)" if row['target_type'] == 'cash' else f"Banco: {row['bank_name']}"
            self.tree_capital.insert('', tk.END, values=(row['id'], row['entry_date'], tgt, row['description'] or "-", f"S/ {row['amount']:,.2f}"))
            
            if row['target_type'] == 'cash':
                total_cap_cash += row['amount']
            else:
                total_cap_bank += row['amount']
        
        conn.close()
        
        self.current_cap_cash = total_cap_cash
        self.current_cap_bank = total_cap_bank
        
        self.card_cap_cash.lbl_value.config(text=f"S/ {total_cap_cash:,.2f}")
        self.card_cap_bank.lbl_value.config(text=f"S/ {total_cap_bank:,.2f}")
        
        # Update Total Footer
        grand_total = total_cap_cash + total_cap_bank
        try:
            self.lbl_capital_total.config(text=f"S/ {grand_total:,.2f}")
        except AttributeError:
            pass # If layout changed
        
        self.update_total_availability()

    def update_total_availability(self):
        # Placeholder to prevent errors if called, though logic moved to Dashboard update
        pass

            
    # --- Context Menu Logic ---
    def show_context_menu(self, event):
        item = self.tree_capital.identify_row(event.y)
        if item:
            self.tree_capital.selection_set(item)
            self.menu_capital.post(event.x_root, event.y_root)

    def on_edit_capital(self):
        sel = self.tree_capital.selection()
        if sel:
            item_id = self.tree_capital.item(sel[0])['values'][0]
            self.require_admin(lambda: self.show_capital_modal(item_id))

    def on_delete_capital(self):
        sel = self.tree_capital.selection()
        if sel:
            item_id = self.tree_capital.item(sel[0])['values'][0]
            
            def delete_action():
                if messagebox.askyesno("Confirmar", "¿Eliminar inversión?"):
                     conn = get_db_connection()
                     try:
                         conn.execute("DELETE FROM capital_entries WHERE id=?", (item_id,))
                         conn.commit()
                         messagebox.showinfo("Éxito", "Eliminado correctamente")
                         self.load_cash_info()
                         self.update_dashboard_summary()
                     except Exception as e:
                         messagebox.showerror("Error", str(e))
                     finally:
                         conn.close()

            self.require_admin(delete_action)

    # --- Auth Helper ---
    def require_admin(self, callback):
        password_window = tk.Toplevel(self)
        password_window.title("Seguridad Admin")
        password_window.geometry("300x150")
        
        tk.Label(password_window, text="Ingrese Contraseña de Administrador:", font=("Segoe UI", 10)).pack(pady=10)
        entry_pass = tk.Entry(password_window, show="*")
        entry_pass.pack(pady=5)
        entry_pass.focus()
        
        def check_password():
            pwd = entry_pass.get()
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE role='admin' AND password=?", (pwd,))
            admin_user = cursor.fetchone()
            conn.close()
            
            if admin_user:
                password_window.destroy()
                callback()
            else:
                messagebox.showerror("Error", "Contraseña incorrecta")
        
        tk.Button(password_window, text="Verificar", command=check_password, bg="#2196F3", fg="white").pack(pady=10)
        password_window.bind('<Return>', lambda e: check_password())

    def show_capital_modal(self, entry_id=None):
        modal = tk.Toplevel(self)
        title = "Editar Capital" if entry_id else "Registrar Capital"
        modal.title(title)
        modal.geometry("400x450")
        
        tk.Label(modal, text="Destino del Capital:", font=("Segoe UI", 9, "bold")).pack(pady=5)
        cmb_target = ttk.Combobox(modal, values=["Efectivo (Caja)", "Cuenta Bancaria"], state="readonly")
        cmb_target.set("Efectivo (Caja)")
        cmb_target.pack(pady=5)
        
        # Bank Selector (Hidden by default or shown if Bank selected)
        frame_bank = tk.Frame(modal)
        tk.Label(frame_bank, text="Seleccionar Banco:").pack()
        cmb_bank = ttk.Combobox(frame_bank, state="readonly")
        
        # Load Banks
        conn = get_db_connection()
        banks = conn.execute("SELECT id, bank_name FROM bank_accounts").fetchall()
        bank_map = {b['bank_name']: b['id'] for b in banks}
        # Reverse map for loading
        id_to_bank = {b['id']: b['bank_name'] for b in banks}
        
        cmb_bank['values'] = list(bank_map.keys())
        if banks: cmb_bank.current(0)
        
        frame_bank.pack(pady=5)
        
        def toggle_bank(event):
            if cmb_target.get() == "Cuenta Bancaria":
                frame_bank.pack(pady=5)
            else:
                frame_bank.pack_forget()
        
        cmb_target.bind("<<ComboboxSelected>>", toggle_bank)
        toggle_bank(None) # Init state
        
        tk.Label(modal, text="Monto (S/):").pack(pady=5)
        entry_amount = tk.Entry(modal)
        entry_amount.pack(pady=5)
        
        tk.Label(modal, text="Fecha (YYYY-MM-DD):").pack(pady=5)
        entry_date = tk.Entry(modal)
        from datetime import date
        entry_date.insert(0, str(date.today()))
        entry_date.pack(pady=5)
        
        tk.Label(modal, text="Nota / Descripción:").pack(pady=5)
        entry_desc = tk.Entry(modal, width=40)
        entry_desc.pack(pady=5)
        
        # Load Data if Editing
        if entry_id:
            cursor = conn.cursor()
            cursor.execute("SELECT target_type, target_id, amount, entry_date, description FROM capital_entries WHERE id=?", (entry_id,))
            row = cursor.fetchone()
            if row:
                t_type = "Efectivo (Caja)" if row['target_type'] == 'cash' else "Cuenta Bancaria"
                cmb_target.set(t_type)
                toggle_bank(None)
                
                if row['target_id'] and row['target_id'] in id_to_bank:
                    cmb_bank.set(id_to_bank[row['target_id']])
                    
                entry_amount.insert(0, str(row['amount']))
                entry_date.delete(0, tk.END)
                entry_date.insert(0, str(row['entry_date']))
                entry_desc.insert(0, row['description'] or "")
        
        conn.close()
        
        def save():
            try:
                amt = float(entry_amount.get())
            except:
                messagebox.showerror("Error", "Monto inválido")
                return
            
            ttype = 'cash' if cmb_target.get() == "Efectivo (Caja)" else 'bank'
            tid = None
            if ttype == 'bank':
                if not cmb_bank.get():
                    messagebox.showerror("Error", "Seleccione un banco")
                    return
                tid = bank_map[cmb_bank.get()]
            
            entry_dt = entry_date.get()
            desc = entry_desc.get()
            
            conn = get_db_connection()
            try:
                if entry_id:
                     conn.execute("UPDATE capital_entries SET target_type=?, target_id=?, amount=?, entry_date=?, description=? WHERE id=?", 
                                 (ttype, tid, amt, entry_dt, desc, entry_id))
                     messagebox.showinfo("Éxito", "Capital actualizado")
                else:
                    conn.execute("INSERT INTO capital_entries (target_type, target_id, amount, entry_date, description) VALUES (?, ?, ?, ?, ?)", 
                                 (ttype, tid, amt, entry_dt, desc))
                    messagebox.showinfo("Éxito", "Capital registrado")
                    
                conn.commit()
                modal.destroy()
                self.load_cash_info() # Reload capital table
                self.update_dashboard_summary()
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                conn.close()
        
        tk.Button(modal, text="Guardar Inversión", command=save, bg="#4CAF50", fg="white").pack(pady=20)

    def update_dashboard_summary(self):
        # Calculate Fixed Assets Total
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(value) FROM fixed_assets WHERE status='active'")
        result = cursor.fetchone()
        fixed_val = result[0] if result and result[0] else 0.0
        conn.close()
        
        msg_receivables = getattr(self, 'total_receivable_val', 0.0)
        
        # Use Capital Values for Dashboard
        msg_cap_cash = getattr(self, 'current_cap_cash', 0.0)
        msg_cap_bank = getattr(self, 'current_cap_bank', 0.0)
        
        total_cap_equivalent = msg_cap_cash + msg_cap_bank
        total_assets = fixed_val + msg_receivables + total_cap_equivalent
        
        try:
            self.card_fixed.lbl_value.config(text=f"S/ {fixed_val:,.2f}")
            self.card_receivables.lbl_value.config(text=f"S/ {msg_receivables:,.2f}")
            self.card_cash.lbl_value.config(text=f"S/ {total_cap_equivalent:,.2f}")
            
            self.lbl_total_assets.config(text=f"Total Activos: S/ {total_assets:,.2f}")
        except:
            pass

    # CRUD for Fixed Assets
    def add_fixed_asset(self):
        self.show_asset_modal()

    def edit_fixed_asset(self):
        # Check selection in both trees
        sel_eq = self.tree_fixed.selection()
        sel_st = self.tree_startup.selection()
        
        if not sel_eq and not sel_st:
            messagebox.showwarning("Aviso", "Seleccione un ítem")
            return
            
        if sel_eq:
            item_id = self.tree_fixed.item(sel_eq[0])['values'][0]
        else:
            item_id = self.tree_startup.item(sel_st[0])['values'][0]
            
        self.show_asset_modal(item_id)

    def delete_fixed_asset(self):
        # Check selection in both trees
        sel_eq = self.tree_fixed.selection()
        sel_st = self.tree_startup.selection()
        
        if not sel_eq and not sel_st:
            messagebox.showwarning("Aviso", "Seleccione un ítem")
            return
            
        # Determine strict selection
        if sel_eq:
            selection = sel_eq
            tree = self.tree_fixed
        else:
            selection = sel_st
            tree = self.tree_startup
            
        if not messagebox.askyesno("Confirmar", "¿Eliminar este ítem?"):
            return
            
        item_id = tree.item(selection[0])['values'][0]
        
        conn = get_db_connection()
        try:
            conn.execute("DELETE FROM fixed_assets WHERE id = ?", (item_id,))
            conn.commit()
            messagebox.showinfo("Éxito", "Activo eliminado")
            self.load_fixed_assets()
            self.update_dashboard_summary()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    def show_asset_modal(self, asset_id=None):
        modal = tk.Toplevel(self)
        modal.title("Inversión / Activo Fijo")
        modal.geometry("400x450")
        
        # Category Selector
        tk.Label(modal, text="Tipo de Inversión:", font=("Segoe UI", 9, "bold")).pack(pady=(10, 5))
        cmb_cat = ttk.Combobox(modal, values=["Equipamiento / Bienes", "Gastos de Inicio/Licencias"], state="readonly")
        cmb_cat.set("Equipamiento / Bienes")
        cmb_cat.pack(pady=5)
        
        tk.Label(modal, text="Nombre / Concepto:").pack(pady=5)
        entry_name = tk.Entry(modal)
        entry_name.pack(pady=5)
        
        tk.Label(modal, text="Descripción / Detalle:").pack(pady=5)
        entry_desc = tk.Entry(modal)
        entry_desc.pack(pady=5)
        
        tk.Label(modal, text="Fecha de Compra/Gasto:").pack(pady=5)
        # Use DateEntry widget
        date_entry = DateEntry(modal)
        date_entry.pack(pady=5)
        
        tk.Label(modal, text="Costo / Valor (S/):").pack(pady=5)
        entry_val = tk.Entry(modal)
        entry_val.pack(pady=5)
        
        conn = get_db_connection()
        if asset_id:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT name, description, value, purchase_date, category FROM fixed_assets WHERE id = ?", (asset_id,))
                row = cursor.fetchone()
                if row:
                    entry_name.insert(0, row['name'])
                    entry_desc.insert(0, row['description'] or "")
                    entry_val.insert(0, str(row['value']))
                    date_entry.set_date(row['purchase_date'])
                    
                    cat = row['category'] if 'category' in row.keys() else 'equipment'
                    if cat == 'startup':
                        cmb_cat.set("Gastos de Inicio/Licencias")
                    else:
                        cmb_cat.set("Equipamiento / Bienes")
            except:
                pass # Migrations might not affect immediate SELECT if fields missing, handled by defaults
        conn.close()
        
        def save():
            name = entry_name.get()
            try:
                val = float(entry_val.get())
            except ValueError:
                messagebox.showerror("Error", "Valor inválido")
                return
            
            desc = entry_desc.get()
            p_date = date_entry.get_date()
            
            cat_map = {"Equipamiento / Bienes": "equipment", "Gastos de Inicio/Licencias": "startup"}
            category = cat_map.get(cmb_cat.get(), "equipment")
            
            conn = get_db_connection()
            try:
                if asset_id:
                    conn.execute("UPDATE fixed_assets SET name=?, description=?, value=?, purchase_date=?, category=? WHERE id=?", 
                                (name, desc, val, p_date, category, asset_id))
                else:
                    conn.execute("INSERT INTO fixed_assets (name, description, value, purchase_date, category) VALUES (?, ?, ?, ?, ?)", 
                                (name, desc, val, p_date, category))
                conn.commit()
                messagebox.showinfo("Éxito", "Guardado correctamente")
                modal.destroy()
                self.load_fixed_assets()
                self.update_dashboard_summary()
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                conn.close()
        
        tk.Button(modal, text="Guardar", command=save, bg="#4CAF50", fg="white").pack(pady=20)

    # Initial Load
    def tkraise(self, aboveThis=None):
        super().tkraise(aboveThis)
        self.refresh_all()
