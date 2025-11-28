import tkinter as tk
from tkinter import ttk, messagebox
from database import get_db_connection
from ui.modern_window import ModernWindow

class DatabaseWindow(ModernWindow):
    def __init__(self, parent):
        super().__init__(parent, title="Base de Datos Maestra", width=1100, height=750)
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        # Header
        self.create_header("🗄️ Base de Datos - Información Total")
        
        # Content
        content = self.create_content_frame()
        
        # Search toolbar
        toolbar_card = self.create_card_frame(content)
        toolbar_card.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        toolbar = tk.Frame(toolbar_card, bg=self.card_bg)
        toolbar.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(toolbar, text="Buscar Cliente (DNI/Nombre):", bg=self.card_bg, fg=self.text_color,
                font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.load_data())
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=30, font=("Segoe UI", 10))
        search_entry.pack(side=tk.LEFT, padx=5)
        
        refresh_btn = tk.Button(toolbar, text="🔄 Actualizar", command=self.load_data,
                               bg=self.theme_colors['gradient_end'], fg='white',
                               font=("Segoe UI", 9, "bold"), relief='flat', cursor='hand2', padx=10, pady=5)
        refresh_btn.pack(side=tk.LEFT, padx=10)

        # Main table card
        table_card = self.create_card_frame(content)
        table_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
        
        table_frame = tk.Frame(table_card, bg=self.card_bg)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        columns = ("id", "dni", "name", "loans_count", "active_loans", "total_debt", "rating")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        
        self.tree.heading("id", text="ID")
        self.tree.heading("dni", text="DNI")
        self.tree.heading("name", text="Cliente")
        self.tree.heading("loans_count", text="Historial")
        self.tree.heading("active_loans", text="Activos")
        self.tree.heading("total_debt", text="Deuda (S/.)")
        self.tree.heading("rating", text="Calificación")
        
        self.tree.column("id", width=50)
        self.tree.column("dni", width=100)
        self.tree.column("name", width=250)
        self.tree.column("loans_count", width=80, anchor="center")
        self.tree.column("active_loans", width=80, anchor="center")
        self.tree.column("total_debt", width=120, anchor="e")
        self.tree.column("rating", width=150, anchor="center")
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Tags for coloring
        self.tree.tag_configure("buen_pagador", background="#C8E6C9")
        self.tree.tag_configure("regular", background="#FFF9C4")
        self.tree.tag_configure("moroso", background="#FFCDD2")
        self.tree.tag_configure("nuevo", background="white")

        # Detail card
        detail_card = self.create_card_frame(content)
        detail_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
        
        tk.Label(detail_card, text="Préstamos del Cliente Seleccionado", bg=self.card_bg, fg=self.text_color,
                font=("Segoe UI", 11, "bold")).pack(pady=10, padx=15, anchor="w")
        
        detail_frame = tk.Frame(detail_card, bg=self.card_bg)
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.detail_tree = ttk.Treeview(detail_frame, columns=("id", "type", "date", "amount", "status"), show="headings", height=5)
        self.detail_tree.heading("id", text="ID")
        self.detail_tree.heading("type", text="Tipo")
        self.detail_tree.heading("date", text="Fecha")
        self.detail_tree.heading("amount", text="Monto")
        self.detail_tree.heading("status", text="Estado")
        
        self.detail_tree.pack(fill=tk.BOTH, expand=True)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_select_client)

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        search = self.search_var.get()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM clients WHERE 1=1"
        params = []
        if search:
            query += " AND (first_name LIKE ? OR last_name LIKE ? OR dni LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
            
        cursor.execute(query, params)
        clients = cursor.fetchall()
        
        for client in clients:
            client_id = client['id']
            
            cursor.execute("SELECT * FROM loans WHERE client_id = ?", (client_id,))
            loans = cursor.fetchall()
            
            loans_count = len(loans)
            active_loans = sum(1 for l in loans if l['status'] == 'active')
            total_debt = sum(l['amount'] for l in loans if l['status'] == 'active')
            
            rating = "Nuevo"
            tag = "nuevo"
            
            if loans_count > 0:
                overdue_count = sum(1 for l in loans if l['status'] == 'overdue')
                
                if overdue_count > 0:
                    rating = "Moroso"
                    tag = "moroso"
                elif loans_count > 2 and overdue_count == 0:
                    rating = "Buen Pagador"
                    tag = "buen_pagador"
                else:
                    rating = "Regular"
                    tag = "regular"
            
            self.tree.insert("", tk.END, values=(
                client['id'],
                client['dni'],
                f"{client['first_name']} {client['last_name']}",
                loans_count,
                active_loans,
                f"{total_debt:.2f}",
                rating
            ), tags=(tag,))
            
        conn.close()

    def on_select_client(self, event):
        for item in self.detail_tree.get_children():
            self.detail_tree.delete(item)
            
        selection = self.tree.selection()
        if not selection: return
        
        client_id = self.tree.item(selection[0], "values")[0]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM loans WHERE client_id = ?", (client_id,))
        loans = cursor.fetchall()
        conn.close()
        
        for loan in loans:
            self.detail_tree.insert("", tk.END, values=(
                loan['id'],
                loan['loan_type'],
                loan['start_date'],
                f"{loan['amount']:.2f}",
                loan['status']
            ))
