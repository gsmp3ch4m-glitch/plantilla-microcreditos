import tkinter as tk
from tkinter import ttk, messagebox
from database import get_db_connection
from ui.modern_window import ModernWindow

from utils.analytics_manager import AnalyticsManager

class DatabaseWindow(ModernWindow):
    def __init__(self, parent):
        super().__init__(parent, title="Base de Datos Maestra", width=1100, height=750)
        self.analytics = AnalyticsManager()
        self.create_widgets()
        self.load_data()


            
        # Load Backups
        self.load_backups()

    def load_backups(self):
        if not hasattr(self, 'backup_tree'): return
        
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
            
        from utils.backup_manager import BackupManager
        bm = BackupManager()
        backups = bm.get_available_backups()
        
        for backup in backups:
            self.backup_tree.insert("", tk.END, values=(backup,))


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
        
        # Tabs
        self.notebook = ttk.Notebook(table_card)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab Clientes
        self.tab_clients = tk.Frame(self.notebook, bg=self.card_bg)
        self.notebook.add(self.tab_clients, text="👥 Clientes")
        
        columns = ("id", "dni", "name", "loans_count", "active_loans", "total_debt", "total_generated", "rating")
        self.tree = ttk.Treeview(self.tab_clients, columns=columns, show="headings", height=12)
        
        self.tree.heading("id", text="ID")
        self.tree.heading("dni", text="DNI")
        self.tree.heading("name", text="Cliente")
        self.tree.heading("loans_count", text="Historial")
        self.tree.heading("active_loans", text="Activos")
        self.tree.heading("total_debt", text="Deuda (S/.)")
        self.tree.heading("total_generated", text="Total Generado")
        self.tree.heading("rating", text="Calificación")
        
        self.tree.column("id", width=50)
        self.tree.column("dni", width=100)
        self.tree.column("name", width=250)
        self.tree.column("loans_count", width=80, anchor="center")
        self.tree.column("active_loans", width=80, anchor="center")
        self.tree.column("total_debt", width=100, anchor="e")
        self.tree.column("total_generated", width=100, anchor="e")
        self.tree.column("rating", width=150, anchor="center")
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Tab Prendas
        self.tab_pawn = tk.Frame(self.notebook, bg=self.card_bg)
        self.notebook.add(self.tab_pawn, text="💍 Prendas")
        
        pawn_cols = ("id", "type", "brand", "characteristics", "condition", "market_value", "status", "utility")
        self.pawn_tree = ttk.Treeview(self.tab_pawn, columns=pawn_cols, show="headings", height=12)
        
        self.pawn_tree.heading("id", text="ID")
        self.pawn_tree.heading("type", text="Tipo")
        self.pawn_tree.heading("brand", text="Marca")
        self.pawn_tree.heading("characteristics", text="Características")
        self.pawn_tree.heading("condition", text="Estado")
        self.pawn_tree.heading("market_value", text="Valor Mercado")
        self.pawn_tree.heading("status", text="Estado Préstamo")
        self.pawn_tree.heading("utility", text="Utilidad Est.")
        
        self.pawn_tree.column("id", width=50)
        self.pawn_tree.column("type", width=100)
        self.pawn_tree.column("brand", width=100)
        self.pawn_tree.column("characteristics", width=200)
        self.pawn_tree.column("condition", width=100)
        self.pawn_tree.column("market_value", width=100, anchor="e")
        self.pawn_tree.column("status", width=100, anchor="center")
        self.pawn_tree.column("utility", width=100, anchor="e")
        
        self.pawn_tree.pack(fill=tk.BOTH, expand=True)
        
        # Tab Administración (Backup & Restore)
        self.tab_admin = tk.Frame(self.notebook, bg=self.card_bg)
        self.notebook.add(self.tab_admin, text="🛠️ Administración")
        
        admin_container = tk.Frame(self.tab_admin, bg=self.card_bg)
        admin_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left Side: Backup Controls
        left_frame = tk.LabelFrame(admin_container, text="Copias de Seguridad", bg=self.card_bg, fg=self.text_color, font=("Segoe UI", 10, "bold"))
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        tk.Button(left_frame, text="💾 Crear Copia de Seguridad (JSON)", command=self.create_backup,
                 bg="#4CAF50", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=10, pady=5).pack(pady=(10, 5))
                 
        tk.Button(left_frame, text="📊 Exportar a Excel", command=self.create_excel_backup,
                 bg="#2E7D32", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=10, pady=5).pack(pady=5)
        
        # Show path
        from utils.backup_manager import BackupManager
        bm = BackupManager()
        path_label = tk.Label(left_frame, text=f"Ruta: {bm.local_backup_dir}", 
                             bg=self.card_bg, fg="gray", font=("Segoe UI", 8), wraplength=300)
        path_label.pack(pady=(0, 10), padx=10)

        tk.Label(left_frame, text="Copias Disponibles:", bg=self.card_bg, fg=self.text_color).pack(anchor="w", padx=10)
        
        self.backup_tree = ttk.Treeview(left_frame, columns=("filename",), show="headings", height=8)
        self.backup_tree.heading("filename", text="Archivo de Respaldo")
        self.backup_tree.column("filename", width=300)
        self.backup_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        btn_frame = tk.Frame(left_frame, bg=self.card_bg)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(btn_frame, text="♻️ Restaurar Seleccionado", command=self.restore_selected,
                 bg="#2196F3", fg="white", font=("Segoe UI", 9, "bold"), relief="flat").pack(side=tk.LEFT, padx=5)
                 
        tk.Button(btn_frame, text="📂 Importar Backup...", command=self.import_backup,
                 bg="#607D8B", fg="white", font=("Segoe UI", 9), relief="flat").pack(side=tk.LEFT, padx=5)

        # Right Side: Danger Zone
        right_frame = tk.LabelFrame(admin_container, text="Zona de Peligro", bg=self.card_bg, fg="#F44336", font=("Segoe UI", 10, "bold"))
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        tk.Label(right_frame, text="⚠️ Estas acciones son destructivas e irreversibles.", 
                bg=self.card_bg, fg=self.text_color, wraplength=200).pack(pady=20)
        
        tk.Button(right_frame, text="☢️ FORMATEAR / RESETEAR SISTEMA", command=self.reset_system,
                 bg="#F44336", fg="white", font=("Segoe UI", 11, "bold"), relief="flat", padx=20, pady=10).pack(pady=10)
        
        tk.Label(right_frame, text="Esto borrará TODOS los datos y restaurará el sistema a su estado original de fábrica.", 
                bg=self.card_bg, fg="#F44336", font=("Segoe UI", 9), wraplength=200).pack(pady=10)

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

    def verify_admin_password(self):
        """Asks for admin password and verifies it."""
        from tkinter import simpledialog
        password = simpledialog.askstring("Seguridad", "Ingrese la contraseña de administrador:", show='*', parent=self)
        
        if not password:
            return False
            
        # Verify against current user (assuming they are admin or have permission)
        # Or specifically check for 'admin' user password if strict
        # For this app, we'll check if the entered password matches the current logged in user
        # AND if that user is an admin.
        
        # Since we don't have easy access to current user object here (it's in Main Window),
        # we will fetch the 'admin' user from DB and verify against that for critical system actions.
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = 'admin'")
        result = cursor.fetchone()
        conn.close()
        
        if result and result['password'] == password:
            return True
        else:
            messagebox.showerror("Error", "Contraseña incorrecta.")
            return False

    def restart_application(self):
        """Restarts the application."""
        import sys
        import os
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def create_backup(self):
        from utils.backup_manager import BackupManager
        bm = BackupManager()
        bm.create_backup(trigger='manual')
        messagebox.showinfo("Éxito", "Copia de seguridad (JSON) creada correctamente.")
        self.load_backups()

    def create_excel_backup(self):
        from utils.backup_manager import BackupManager
        bm = BackupManager()
        path = bm.create_excel_backup(trigger='manual')
        if path:
            messagebox.showinfo("Éxito", f"Reporte Excel creado en:\n{path}")
            self.load_backups()
        else:
            messagebox.showerror("Error", "No se pudo crear el archivo Excel.")

    def restore_selected(self):
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("Selección", "Por favor seleccione un archivo de respaldo de la lista.")
            return
            
        filename = self.backup_tree.item(selection[0], "values")[0]
        
        if messagebox.askyesno("Confirmar Restauración", 
                              f"¿Está seguro que desea restaurar la base de datos desde '{filename}'?\n\n"
                              "⚠️ ESTO SOBREESCRIBIRÁ LOS DATOS ACTUALES.\n"
                              "La aplicación se reiniciará después de la restauración."):
            
            if not self.verify_admin_password():
                return

            from utils.backup_manager import BackupManager
            bm = BackupManager()
            success, message = bm.restore_database(filename)
            if success:
                messagebox.showinfo("Restauración Exitosa", "La base de datos ha sido restaurada.\nLa aplicación se reiniciará ahora.")
                self.restart_application()
            else:
                messagebox.showerror("Error", f"Ocurrió un error al restaurar la base de datos:\n{message}")

    def import_backup(self):
        from tkinter import filedialog
        filename = filedialog.askopenfilename(filetypes=[("Backup Files", "*.db *.json *.xlsx"), ("Database", "*.db"), ("JSON", "*.json"), ("Excel", "*.xlsx")])
        if filename:
            if messagebox.askyesno("Confirmar Importación", 
                                  f"¿Está seguro que desea restaurar desde el archivo seleccionado?\n\n"
                                  "⚠️ ESTO SOBREESCRIBIRÁ LOS DATOS ACTUALES.\n"
                                  "La aplicación se reiniciará después de la restauración."):
                
                if not self.verify_admin_password():
                    return

                from utils.backup_manager import BackupManager
                bm = BackupManager()
                success, message = bm.restore_database(filename)
                if success:
                    messagebox.showinfo("Restauración Exitosa", "La base de datos ha sido restaurada.\nLa aplicación se reiniciará ahora.")
                    self.restart_application()
                else:
                    messagebox.showerror("Error", f"Ocurrió un error al restaurar la base de datos:\n{message}")

    def reset_system(self):
        if messagebox.askyesno("⚠️ PELIGRO: RESETEAR SISTEMA", 
                              "¿ESTÁ SEGURO QUE DESEA FORMATEAR EL SISTEMA?\n\n"
                              "❌ SE BORRARÁN TODOS LOS CLIENTES, PRÉSTAMOS Y REGISTROS.\n"
                              "❌ ESTA ACCIÓN NO SE PUEDE DESHACER.\n\n"
                              "¿Desea continuar?", icon='warning'):
            
            if messagebox.askyesno("CONFIRMACIÓN FINAL", 
                                  "¿REALMENTE ESTÁ SEGURO?\n\n"
                                  "Esta acción requiere autorización de ADMINISTRADOR.", icon='warning'):
                
                if not self.verify_admin_password():
                    return

                from utils.backup_manager import BackupManager
                bm = BackupManager()
                
                # Create a safety backup just in case
                bm.create_backup(trigger='pre_reset')
                
                if bm.reset_database():
                    messagebox.showinfo("Sistema Reseteado", "El sistema ha sido formateado correctamente.\nLa aplicación se reiniciará ahora.")
                    self.restart_application()
                else:
                    messagebox.showerror("Error", "Ocurrió un error al resetear el sistema.")

    def load_data(self, *args):
        # Clear Clients Tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Clear Pawn Tree
        for item in self.pawn_tree.get_children():
            self.pawn_tree.delete(item)
            
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
            
            # Calculate Lifetime Value
            total_generated = self.analytics.get_client_lifetime_value(client_id)
            
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
                f"{total_generated:.2f}",
                rating
            ), tags=(tag,))
            
        conn.close()
        
        # Load Pawn Data
        inventory = self.analytics.get_pawn_inventory()
        for item in inventory:
            self.pawn_tree.insert("", tk.END, values=(
                item['id'],
                item['item_type'],
                item['brand'],
                item['characteristics'],
                item['condition'],
                f"{item['market_value']:.2f}",
                item['loan_status'],
                f"{item['estimated_utility']:.2f}"
            ))

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
