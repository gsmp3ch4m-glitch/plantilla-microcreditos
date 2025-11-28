import tkinter as tk
from tkinter import ttk, messagebox
from database import get_db_connection

class DatabaseWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Base de Datos Maestra - Información Total")
        self.geometry("1100x700")
        
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        # Toolbar / Filter
        toolbar = tk.Frame(self, bg="#e0e0e0")
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(toolbar, text="Buscar Cliente (DNI/Nombre):", bg="#e0e0e0").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.load_data())
        tk.Entry(toolbar, textvariable=self.search_var, width=30).pack(side=tk.LEFT, padx=5)
        
        tk.Button(toolbar, text="Actualizar", command=self.load_data).pack(side=tk.LEFT, padx=10)

        # Main Treeview (Clients + Summary)
        columns = ("id", "dni", "name", "loans_count", "active_loans", "total_debt", "rating")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        
        self.tree.heading("id", text="ID")
        self.tree.heading("dni", text="DNI")
        self.tree.heading("name", text="Cliente")
        self.tree.heading("loans_count", text="Historial Préstamos")
        self.tree.heading("active_loans", text="Activos")
        self.tree.heading("total_debt", text="Deuda Total (S/.)")
        self.tree.heading("rating", text="Calificación")
        
        self.tree.column("id", width=50)
        self.tree.column("dni", width=100)
        self.tree.column("name", width=250)
        self.tree.column("loans_count", width=100, anchor="center")
        self.tree.column("active_loans", width=80, anchor="center")
        self.tree.column("total_debt", width=120, anchor="e")
        self.tree.column("rating", width=150, anchor="center")
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tags for coloring rows
        self.tree.tag_configure("buen_pagador", background="#C8E6C9") # Green tint
        self.tree.tag_configure("regular", background="#FFF9C4")      # Yellow tint
        self.tree.tag_configure("moroso", background="#FFCDD2")       # Red tint
        self.tree.tag_configure("nuevo", background="white")

        # Detail Section (Bottom)
        detail_frame = tk.LabelFrame(self, text="Detalle de Préstamos del Cliente Seleccionado")
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.detail_tree = ttk.Treeview(detail_frame, columns=("id", "type", "date", "amount", "status"), show="headings")
        self.detail_tree.heading("id", text="ID Préstamo")
        self.detail_tree.heading("type", text="Tipo")
        self.detail_tree.heading("date", text="Fecha")
        self.detail_tree.heading("amount", text="Monto")
        self.detail_tree.heading("status", text="Estado")
        
        self.detail_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_select_client)

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        search = self.search_var.get()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all clients
        query = "SELECT * FROM clients WHERE 1=1"
        params = []
        if search:
            query += " AND (first_name LIKE ? OR last_name LIKE ? OR dni LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
            
        cursor.execute(query, params)
        clients = cursor.fetchall()
        
        for client in clients:
            client_id = client['id']
            
            # Calculate Stats
            cursor.execute("SELECT * FROM loans WHERE client_id = ?", (client_id,))
            loans = cursor.fetchall()
            
            loans_count = len(loans)
            active_loans = sum(1 for l in loans if l['status'] == 'active')
            total_debt = sum(l['amount'] for l in loans if l['status'] == 'active') # Simplified debt (principal only)
            
            # Calculate Rating
            rating = "Nuevo"
            tag = "nuevo"
            
            if loans_count > 0:
                # Check for overdue loans
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
