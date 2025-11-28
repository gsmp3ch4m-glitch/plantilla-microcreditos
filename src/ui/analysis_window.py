import tkinter as tk
from tkinter import ttk
from database import get_db_connection

class AnalysisWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Análisis Financiero")
        self.geometry("800x600")
        
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        tk.Label(self, text="Resumen General", font=("Arial", 16, "bold")).pack(pady=20)
        
        self.stats_frame = tk.Frame(self)
        self.stats_frame.pack(fill=tk.X, padx=20)
        
        # Cards
        self.card_loans = self.create_card(self.stats_frame, "Total Préstamos", "0")
        self.card_loans.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)
        
        self.card_active = self.create_card(self.stats_frame, "Activos", "0")
        self.card_active.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)
        
        self.card_clients = self.create_card(self.stats_frame, "Total Clientes", "0")
        self.card_clients.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)

        # Recent Activity
        tk.Label(self, text="Actividad Reciente", font=("Arial", 12, "bold")).pack(pady=(30, 10))
        
        columns = ("date", "type", "amount", "desc")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        self.tree.heading("date", text="Fecha")
        self.tree.heading("type", text="Tipo")
        self.tree.heading("amount", text="Monto")
        self.tree.heading("desc", text="Descripción")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    def create_card(self, parent, title, value):
        frame = tk.LabelFrame(parent, text=title, font=("Arial", 10))
        lbl = tk.Label(frame, text=value, font=("Arial", 20, "bold"), fg="blue")
        lbl.pack(pady=10, padx=20)
        return frame

    def update_card(self, frame, value):
        for widget in frame.winfo_children():
            widget.config(text=value)

    def load_data(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Stats
        cursor.execute("SELECT COUNT(*) FROM loans")
        total_loans = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM loans WHERE status='active'")
        active_loans = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM clients")
        total_clients = cursor.fetchone()[0]
        
        self.update_card(self.card_loans, str(total_loans))
        self.update_card(self.card_active, str(active_loans))
        self.update_card(self.card_clients, str(total_clients))
        
        # Recent Transactions
        cursor.execute("SELECT date, type, amount, description FROM transactions ORDER BY date DESC LIMIT 10")
        rows = cursor.fetchall()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for row in rows:
            self.tree.insert("", tk.END, values=(row["date"], row["type"], f"{row['amount']:.2f}", row["description"]))
            
        conn.close()
