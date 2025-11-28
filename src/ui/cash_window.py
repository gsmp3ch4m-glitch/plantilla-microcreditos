import tkinter as tk
from tkinter import ttk, messagebox
from database import get_db_connection
from datetime import datetime

class CashWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Caja - Movimientos")
        self.geometry("900x600")
        
        self.create_widgets()
        self.load_transactions()

    def create_widgets(self):
        # Summary Frame
        summary_frame = tk.Frame(self, bg="#f0f0f0", pady=10)
        summary_frame.pack(fill=tk.X)
        
        self.lbl_balance = tk.Label(summary_frame, text="Balance: S/ 0.00", font=("Arial", 16, "bold"), bg="#f0f0f0")
        self.lbl_balance.pack()

        # Toolbar
        toolbar = tk.Frame(self, bg="#e0e0e0")
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(toolbar, text="Registrar Ingreso", command=lambda: self.open_transaction_dialog("income")).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Registrar Egreso", command=lambda: self.open_transaction_dialog("expense")).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Actualizar", command=self.load_transactions).pack(side=tk.LEFT, padx=5)

        # Treeview
        columns = ("id", "type", "category", "amount", "description", "date")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("type", text="Tipo")
        self.tree.heading("category", text="Categoría")
        self.tree.heading("amount", text="Monto")
        self.tree.heading("description", text="Descripción")
        self.tree.heading("date", text="Fecha")
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def load_transactions(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
        rows = cursor.fetchall()
        
        balance = 0
        for row in rows:
            amount = row["amount"]
            if row["type"] == "income":
                balance += amount
                tags = ("income",)
            else:
                balance -= amount
                tags = ("expense",)
                
            self.tree.insert("", tk.END, values=(row["id"], row["type"], row["category"], f"{amount:.2f}", row["description"], row["date"]), tags=tags)
            
        self.lbl_balance.config(text=f"Balance: S/ {balance:.2f}")
        
        self.tree.tag_configure("income", foreground="green")
        self.tree.tag_configure("expense", foreground="red")
        
        conn.close()

    def open_transaction_dialog(self, trans_type):
        TransactionForm(self, self.load_transactions, trans_type)

class TransactionForm(tk.Toplevel):
    def __init__(self, parent, callback, trans_type):
        super().__init__(parent)
        self.callback = callback
        self.trans_type = trans_type
        self.title("Registrar " + ("Ingreso" if trans_type == "income" else "Egreso"))
        self.geometry("400x300")
        
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Categoría:").pack(pady=(10, 0))
        self.combo_category = ttk.Combobox(self, values=["payment", "loan_disbursement", "operational", "other"])
        self.combo_category.current(0)
        self.combo_category.pack()
        
        tk.Label(self, text="Monto:").pack()
        self.entry_amount = tk.Entry(self)
        self.entry_amount.pack()
        
        tk.Label(self, text="Descripción:").pack()
        self.entry_desc = tk.Entry(self)
        self.entry_desc.pack()
        
        tk.Button(self, text="Guardar", command=self.save).pack(pady=20)

    def save(self):
        amount = self.entry_amount.get()
        category = self.combo_category.get()
        description = self.entry_desc.get()
        
        if not amount:
            messagebox.showerror("Error", "Monto es obligatorio")
import tkinter as tk
from tkinter import ttk, messagebox
from database import get_db_connection, log_action # Added log_action
from datetime import datetime

class CashWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent # Store parent to access user_data
        self.title("Caja - Movimientos")
        self.geometry("900x600")
        
        self.create_widgets()
        self.load_transactions()

    def create_widgets(self):
        # Summary Frame
        summary_frame = tk.Frame(self, bg="#f0f0f0", pady=10)
        summary_frame.pack(fill=tk.X)
        
        self.lbl_balance = tk.Label(summary_frame, text="Balance: S/ 0.00", font=("Arial", 16, "bold"), bg="#f0f0f0")
        self.lbl_balance.pack()

        # Toolbar
        toolbar = tk.Frame(self, bg="#e0e0e0")
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(toolbar, text="Registrar Ingreso", command=lambda: self.open_transaction_dialog("income")).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Registrar Egreso", command=lambda: self.open_transaction_dialog("expense")).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Actualizar", command=self.load_transactions).pack(side=tk.LEFT, padx=5)

        # Treeview
        columns = ("id", "type", "category", "amount", "description", "date")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("type", text="Tipo")
        self.tree.heading("category", text="Categoría")
        self.tree.heading("amount", text="Monto")
        self.tree.heading("description", text="Descripción")
        self.tree.heading("date", text="Fecha")
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def load_transactions(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
        rows = cursor.fetchall()
        
        balance = 0
        for row in rows:
            amount = row["amount"]
            if row["type"] == "income":
                balance += amount
                tags = ("income",)
            else:
                balance -= amount
                tags = ("expense",)
                
            self.tree.insert("", tk.END, values=(row["id"], row["type"], row["category"], f"{amount:.2f}", row["description"], row["date"]), tags=tags)
            
        self.lbl_balance.config(text=f"Balance: S/ {balance:.2f}")
        
        self.tree.tag_configure("income", foreground="green")
        self.tree.tag_configure("expense", foreground="red")
        
        conn.close()

    def open_transaction_dialog(self, trans_type):
        TransactionForm(self, self.load_transactions, trans_type)

class TransactionForm(tk.Toplevel):
    def __init__(self, parent, callback, trans_type):
        super().__init__(parent)
        self.parent = parent # Store parent (CashWindow) to access its parent (main app)
        self.callback = callback
        self.trans_type = trans_type
        self.title("Registrar " + ("Ingreso" if trans_type == "income" else "Egreso"))
        self.geometry("400x300")
        
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Categoría:").pack(pady=(10, 0))
        self.combo_category = ttk.Combobox(self, values=["payment", "loan_disbursement", "operational", "other"])
        self.combo_category.current(0)
        self.combo_category.pack()
        
        tk.Label(self, text="Monto:").pack()
        self.entry_amount = tk.Entry(self)
        self.entry_amount.pack()
        
        tk.Label(self, text="Descripción:").pack()
        self.entry_desc = tk.Entry(self)
        self.entry_desc.pack()
        
        tk.Button(self, text="Guardar", command=self.save).pack(pady=20)

    def save(self):
        amount_str = self.entry_amount.get()
        category = self.combo_category.get()
        description = self.entry_desc.get()
        
        if not amount_str:
            messagebox.showerror("Error", "Monto es obligatorio")
            return
        
        try:
            amount = float(amount_str)
        except ValueError:
            messagebox.showerror("Error", "Monto debe ser un número válido")
            return
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Assuming 'user_id' is available from the main application's user_data
            # The CashWindow's parent is the main app, which should have user_data
            user_id = self.parent.parent.user_data['id'] if hasattr(self.parent.parent, 'user_data') else None

            cursor.execute("""
                INSERT INTO transactions (type, category, amount, description, user_id)
                VALUES (?, ?, ?, ?, ?)
            """, (self.trans_type, category, amount, description, user_id))
            
            conn.commit()
            
            # Log Action
            if user_id:
                log_action(user_id, "Movimiento de Caja", f"{self.trans_type} - {category}: {amount:.2f}")
            
            messagebox.showinfo("Éxito", "Movimiento registrado")
            self.callback() # This calls load_transactions in CashWindow
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()
