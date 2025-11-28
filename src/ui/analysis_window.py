import tkinter as tk
from tkinter import ttk
from database import get_db_connection
from ui.modern_window import ModernWindow

class AnalysisWindow(ModernWindow):
    def __init__(self, parent):
        super().__init__(parent, title="Análisis Financiero", width=900, height=650)
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        # Header
        self.create_header("📊 Análisis Financiero")
        
        # Content
        content = self.create_content_frame()
        
        # Stats cards
        stats_frame = tk.Frame(content, bg=self.theme_colors['gradient_end'])
        stats_frame.pack(fill=tk.X, padx=20, pady=20)
        
        self.card_loans = self.create_stat_card(stats_frame, "Total Préstamos", "0", "#4A90E2")
        self.card_loans.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10)
        
        self.card_active = self.create_stat_card(stats_frame, "Activos", "0", "#52C41A")
        self.card_active.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10)
        
        self.card_clients = self.create_stat_card(stats_frame, "Total Clientes", "0", "#9B59B6")
        self.card_clients.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10)

        # Recent Activity
        activity_card = self.create_card_frame(content)
        activity_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        tk.Label(activity_card, text="Actividad Reciente", font=("Segoe UI", 12, "bold"),
                bg=self.card_bg, fg=self.text_color).pack(pady=15, padx=20, anchor="w")
        
        tree_frame = tk.Frame(activity_card, bg=self.card_bg)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        columns = ("date", "type", "amount", "desc")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
        self.tree.heading("date", text="Fecha")
        self.tree.heading("type", text="Tipo")
        self.tree.heading("amount", text="Monto")
        self.tree.heading("desc", text="Descripción")
        self.tree.pack(fill=tk.BOTH, expand=True)

    def create_stat_card(self, parent, title, value, color):
        frame = tk.Frame(parent, bg=color, relief='flat', bd=0)
        frame.pack_propagate(False)
        frame.config(height=100)
        
        tk.Label(frame, text=title, font=("Segoe UI", 10, "bold"), bg=color, fg='white').pack(pady=(15, 5))
        lbl = tk.Label(frame, text=value, font=("Segoe UI", 24, "bold"), bg=color, fg='white')
        lbl.pack()
        
        frame.value_label = lbl
        return frame

    def update_card(self, frame, value):
        frame.value_label.config(text=value)

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
