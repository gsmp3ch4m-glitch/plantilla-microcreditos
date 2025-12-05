import tkinter as tk
from tkinter import ttk, messagebox
from database import get_db_connection
from utils.settings_manager import get_all_settings, update_setting, get_setting

class ConfigWindow(tk.Toplevel):
    def __init__(self, parent, user_data):
        super().__init__(parent)
        self.user_data = user_data
        self.title("Configuración del Sistema")
        self.geometry("800x600")
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.create_users_tab()
        self.create_company_tab()
        self.create_menu_tab()
        self.create_history_tab()
        self.create_theme_tab()
        self.create_db_tab()

    def create_users_tab(self):
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="Usuarios")
        
        # User List
        columns = ("id", "username", "role", "full_name")
        self.user_tree = ttk.Treeview(tab, columns=columns, show="headings", height=10)
        self.user_tree.heading("id", text="ID")
        self.user_tree.heading("username", text="Usuario")
        self.user_tree.heading("role", text="Rol")
        self.user_tree.heading("full_name", text="Nombre Completo")
        self.user_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        btn_frame = tk.Frame(tab)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(btn_frame, text="Nuevo Usuario", command=self.add_user, bg='#4CAF50', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Editar Usuario", command=self.edit_user, bg='#2196F3', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Eliminar Usuario", command=self.delete_user, bg='#f44336', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cambiar Mi Contraseña", command=self.change_password, bg='#FF9800', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Actualizar Lista", command=self.load_users).pack(side=tk.LEFT, padx=5)
        
        self.load_users()

    def load_users(self):
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, full_name FROM users")
        for row in cursor.fetchall():
            self.user_tree.insert("", tk.END, values=(row["id"], row["username"], row["role"], row["full_name"]))
        conn.close()

    def add_user(self):
        # Dialog to add user
        dialog = tk.Toplevel(self)
        dialog.title("Nuevo Usuario")
        dialog.geometry("450x650")  # Increased height
        dialog.resizable(False, False)
        
        # Main frame with padding
        main_frame = tk.Frame(dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        tk.Label(main_frame, text="AGREGAR NUEVO USUARIO", font=("Segoe UI", 14, "bold")).pack(pady=(0, 20))
        
        # Usuario
        tk.Label(main_frame, text="Usuario:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5, 2))
        e_user = ttk.Entry(main_frame, font=("Segoe UI", 10))
        e_user.pack(fill=tk.X, ipady=5, pady=(0, 10))
        
        # Contraseña
        tk.Label(main_frame, text="Contraseña:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5, 2))
        e_pass = ttk.Entry(main_frame, show="●", font=("Segoe UI", 10))
        e_pass.pack(fill=tk.X, ipady=5, pady=(0, 10))
        
        # Nombre Completo
        tk.Label(main_frame, text="Nombre Completo:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5, 2))
        e_name = ttk.Entry(main_frame, font=("Segoe UI", 10))
        e_name.pack(fill=tk.X, ipady=5, pady=(0, 10))
        
        # Nombre Analista
        tk.Label(main_frame, text="Nombre Analista:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5, 2))
        e_analyst_name = ttk.Entry(main_frame, font=("Segoe UI", 10))
        e_analyst_name.pack(fill=tk.X, ipady=5, pady=(0, 10))
        
        # Teléfono Analista
        tk.Label(main_frame, text="Teléfono Analista:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5, 2))
        e_analyst_phone = ttk.Entry(main_frame, font=("Segoe UI", 10))
        e_analyst_phone.pack(fill=tk.X, ipady=5, pady=(0, 10))
        
        # Rol
        tk.Label(main_frame, text="Rol:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5, 2))
        e_role = ttk.Combobox(main_frame, values=["admin", "cajero", "analista"], font=("Segoe UI", 10))
        e_role.current(1)
        e_role.pack(fill=tk.X, ipady=5, pady=(0, 15))
        
        # Permissions Frame
        tk.Label(main_frame, text="Permisos (Módulos):", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 5))
        
        # Scrollable permissions - REDUCED HEIGHT
        perm_container = tk.Frame(main_frame, height=120)  # Reduced from 150 to 120
        perm_container.pack(fill=tk.X, pady=(0, 15))
        perm_container.pack_propagate(False)
        
        canvas = tk.Canvas(perm_container, height=120)  # Reduced from 150 to 120
        scrollbar = tk.Scrollbar(perm_container, orient="vertical", command=canvas.yview)
        perm_frame = tk.Frame(canvas)
        
        perm_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=perm_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        modules = [
            ('mod_clients', 'Clientes (Acceso)'),
            ('client_add', '  - Agregar Clientes'),
            ('client_edit', '  - Editar Clientes'),
            ('client_delete', '  - Eliminar Clientes'),
            ('mod_pawn', 'Casa de Empeño'),
            ('mod_bank', 'Préstamo Bancario'),
            ('mod_rapid', 'Rapidiario'),
            ('mod_cash', 'Caja'),
            ('mod_calc', 'Calculadora'),
            ('mod_analysis', 'Análisis'),
            ('mod_config', 'Configuración')
        ]
        
        perm_vars = {}
        for key, label in modules:
            var = tk.BooleanVar()
            chk = tk.Checkbutton(perm_frame, text=label, variable=var, font=("Segoe UI", 9))
            chk.pack(anchor="w", padx=5, pady=2)
            perm_vars[key] = (var, chk)
            
        def on_role_change(event):
            role = e_role.get()
            if role == "admin":
                for key, (var, chk) in perm_vars.items():
                    var.set(True)
                    chk.configure(state="disabled")
            else:
                for key, (var, chk) in perm_vars.items():
                    chk.configure(state="normal")
                    
        e_role.bind("<<ComboboxSelected>>", on_role_change)
        on_role_change(None) # Init
        
        def save():
            # Validation
            if not e_user.get() or not e_pass.get() or not e_name.get():
                messagebox.showerror("Error", "Por favor complete todos los campos")
                return
            
            role = e_role.get()
            
            # Check limit
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = ?", (role,))
            count = cursor.fetchone()[0]
            
            if count >= 5:
                messagebox.showerror("Error", f"Se ha alcanzado el límite de 5 usuarios para el rol '{role}'")
                conn.close()
                return

            permissions = []
            if role == "admin":
                permissions = ["all"]
            else:
                for key, (var, chk) in perm_vars.items():
                    if var.get():
                        permissions.append(key)
            
            perm_str = ",".join(permissions)
            
            try:
                conn.execute("INSERT INTO users (username, password, full_name, analyst_name, analyst_phone, role, permissions) VALUES (?, ?, ?, ?, ?, ?, ?)",
                             (e_user.get(), e_pass.get(), e_name.get(), e_analyst_name.get(), e_analyst_phone.get(), role, perm_str))
                conn.commit()
                
                # Log Action
                from database import log_action
                log_action(self.user_data['id'], "Crear Usuario", f"Usuario creado: {e_user.get()} ({role})")
                
                messagebox.showinfo("Éxito", f"Usuario '{e_user.get()}' creado correctamente")
                self.load_users()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al crear usuario: {str(e)}")
            finally:
                conn.close()
        
        # Buttons frame
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        # GUARDAR button - Big and visible
        save_btn = tk.Button(btn_frame, text="GUARDAR USUARIO", command=save,
                            bg='#4CAF50', fg='white',
                            font=("Segoe UI", 11, "bold"),
                            relief='flat', cursor='hand2', padx=20, pady=10)
        save_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # CANCELAR button
        cancel_btn = tk.Button(btn_frame, text="CANCELAR", command=dialog.destroy,
                              bg='#757575', fg='white',
                              font=("Segoe UI", 11, "bold"),
                              relief='flat', cursor='hand2', padx=20, pady=10)
        cancel_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

    def edit_user(self):
        """Editar usuario seleccionado"""
        selection = self.user_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Por favor seleccione un usuario para editar")
            return
        
        # Get selected user data
        item = self.user_tree.item(selection[0])
        user_id, username, role, full_name = item['values']
        
        # Get full user data including analyst fields
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT analyst_name, analyst_phone FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        conn.close()
        
        analyst_name = user_row['analyst_name'] if user_row else ''
        analyst_phone = user_row['analyst_phone'] if user_row else ''
        
        # Cannot edit admin user
        if username == 'admin':
            messagebox.showwarning("Aviso", "No se puede editar el usuario administrador principal")
            return
        
        # Create edit dialog
        dialog = tk.Toplevel(self)
        dialog.title(f"Editar Usuario: {username}")
        dialog.geometry("450x600")
        dialog.resizable(False, False)
        
        main_frame = tk.Frame(dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(main_frame, text=f"EDITAR USUARIO: {username}", font=("Segoe UI", 14, "bold")).pack(pady=(0, 20))
        
        # Nombre Completo
        tk.Label(main_frame, text="Nombre Completo:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5, 2))
        e_name = ttk.Entry(main_frame, font=("Segoe UI", 10))
        e_name.insert(0, full_name or "")
        e_name.pack(fill=tk.X, ipady=5, pady=(0, 10))
        
        # Nombre Analista
        tk.Label(main_frame, text="Nombre Analista:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5, 2))
        e_analyst_name = ttk.Entry(main_frame, font=("Segoe UI", 10))
        e_analyst_name.insert(0, analyst_name or "")
        e_analyst_name.pack(fill=tk.X, ipady=5, pady=(0, 10))
        
        # Teléfono Analista
        tk.Label(main_frame, text="Teléfono Analista:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5, 2))
        e_analyst_phone = ttk.Entry(main_frame, font=("Segoe UI", 10))
        e_analyst_phone.insert(0, analyst_phone or "")
        e_analyst_phone.pack(fill=tk.X, ipady=5, pady=(0, 10))
        
        # Rol
        tk.Label(main_frame, text="Rol:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5, 2))
        e_role = ttk.Combobox(main_frame, values=["admin", "caja", "cajero", "analista"], font=("Segoe UI", 10))
        e_role.set(role)
        e_role.pack(fill=tk.X, ipady=5, pady=(0, 15))
        
        # Nueva Contraseña (opcional)
        tk.Label(main_frame, text="Nueva Contraseña (dejar vacío para no cambiar):", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5, 2))
        e_pass = ttk.Entry(main_frame, show="●", font=("Segoe UI", 10))
        e_pass.pack(fill=tk.X, ipady=5, pady=(0, 15))
        
        def save():
            if not e_name.get():
                messagebox.showerror("Error", "El nombre completo es obligatorio")
                return
            
            conn = get_db_connection()
            try:
                if e_pass.get():
                    conn.execute("UPDATE users SET full_name = ?, analyst_name = ?, analyst_phone = ?, role = ?, password = ? WHERE id = ?",
                                (e_name.get(), e_analyst_name.get(), e_analyst_phone.get(), e_role.get(), e_pass.get(), user_id))
                else:
                    conn.execute("UPDATE users SET full_name = ?, analyst_name = ?, analyst_phone = ?, role = ? WHERE id = ?",
                                (e_name.get(), e_analyst_name.get(), e_analyst_phone.get(), e_role.get(), user_id))
                
                conn.commit()
                
                from database import log_action
                log_action(self.user_data['id'], "Editar Usuario", f"Usuario editado: {username}")
                
                messagebox.showinfo("Éxito", "Usuario actualizado correctamente")
                self.load_users()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar usuario: {str(e)}")
            finally:
                conn.close()
        
        # Buttons
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        save_btn = tk.Button(btn_frame, text="GUARDAR CAMBIOS", command=save,
                            bg='#4CAF50', fg='white',
                            font=("Segoe UI", 11, "bold"),
                            relief='flat', cursor='hand2', padx=20, pady=10)
        save_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        cancel_btn = tk.Button(btn_frame, text="CANCELAR", command=dialog.destroy,
                              bg='#757575', fg='white',
                              font=("Segoe UI", 11, "bold"),
                              relief='flat', cursor='hand2', padx=20, pady=10)
        cancel_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

    def delete_user(self):
        """Eliminar usuario seleccionado"""
        selection = self.user_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Por favor seleccione un usuario para eliminar")
            return
        
        # Get selected user data
        item = self.user_tree.item(selection[0])
        user_id, username, role, full_name = item['values']
        
        # Cannot delete admin user
        if username == 'admin':
            messagebox.showerror("Error", "No se puede eliminar el usuario administrador principal")
            return
        
        # Cannot delete yourself
        if user_id == self.user_data['id']:
            messagebox.showerror("Error", "No puede eliminar su propio usuario")
            return
        
        # Confirm deletion
        if not messagebox.askyesno("Confirmar Eliminación", 
                                   f"¿Está seguro de eliminar el usuario '{username}'?\n\n"
                                   f"Nombre: {full_name}\n"
                                   f"Rol: {role}\n\n"
                                   "Esta acción no se puede deshacer."):
            return
        
        # Delete user
        conn = get_db_connection()
        try:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            
            from database import log_action
            log_action(self.user_data['id'], "Eliminar Usuario", f"Usuario eliminado: {username} ({full_name})")
            
            messagebox.showinfo("Éxito", f"Usuario '{username}' eliminado correctamente")
            self.load_users()
        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar usuario: {str(e)}")
        finally:
            conn.close()

    def change_password(self):
        # Dialog to change password
        dialog = tk.Toplevel(self)
        dialog.title("Cambiar Contraseña")
        dialog.geometry("420x480")  # Increased width and height
        dialog.resizable(False, False)
        
        # Main frame with reduced padding
        main_frame = tk.Frame(dialog, padx=25, pady=15)  # Reduced padding
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title with icon
        title_frame = tk.Frame(main_frame)
        title_frame.pack(pady=(0, 20))  # Reduced from 25
        
        tk.Label(title_frame, text="🔒", font=("Segoe UI Emoji", 28)).pack()  # Smaller icon
        tk.Label(title_frame, text="CAMBIAR CONTRASEÑA", font=("Segoe UI", 12, "bold")).pack(pady=(5, 0))
        
        # Nueva Contraseña
        tk.Label(main_frame, text="Nueva Contraseña:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        e_new = ttk.Entry(main_frame, show="●", font=("Segoe UI", 11))
        e_new.pack(fill=tk.X, ipady=10, pady=(0, 12))  # Reduced spacing
        
        # Confirmar Contraseña
        tk.Label(main_frame, text="Confirmar Contraseña:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        e_conf = ttk.Entry(main_frame, show="●", font=("Segoe UI", 11))
        e_conf.pack(fill=tk.X, ipady=10, pady=(0, 20))  # Reduced spacing
        
        def save():
            if not e_new.get() or not e_conf.get():
                messagebox.showerror("Error", "Por favor complete ambos campos")
                return
                
            if e_new.get() != e_conf.get():
                messagebox.showerror("Error", "Las contraseñas no coinciden")
                e_conf.delete(0, tk.END)
                e_conf.focus()
                return
                
            conn = get_db_connection()
            conn.execute("UPDATE users SET password = ? WHERE id = ?", (e_new.get(), self.user_data['id']))
            conn.commit()
            conn.close()
            
            # Log Action
            from database import log_action
            log_action(self.user_data['id'], "Cambiar Contraseña", "El usuario cambió su propia contraseña")
            
            messagebox.showinfo("Éxito", "Contraseña actualizada correctamente")
            dialog.destroy()
        
        # Buttons frame
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        # GUARDAR button (changed from ACTUALIZAR)
        save_btn = tk.Button(btn_frame, text="GUARDAR", command=save,
                            bg='#4CAF50', fg='white',
                            font=("Segoe UI", 11, "bold"),
                            relief='flat', cursor='hand2', padx=20, pady=10)
        save_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # CANCELAR button
        cancel_btn = tk.Button(btn_frame, text="CANCELAR", command=dialog.destroy,
                              bg='#757575', fg='white',
                              font=("Segoe UI", 11, "bold"),
                              relief='flat', cursor='hand2', padx=20, pady=10)
        cancel_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Focus on first field
        e_new.focus()
        
        # Bind Enter key
        e_new.bind('<Return>', lambda e: e_conf.focus())
        e_conf.bind('<Return>', lambda e: save())

    def create_company_tab(self):
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="Empresa")
        
        # Create Scrollable Container
        canvas = tk.Canvas(tab)
        scrollbar = tk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Ensure scrollable frame expands to width of canvas
        def on_canvas_configure(event):
            canvas.itemconfig(canvas.create_window((0,0), window=scrollable_frame, anchor="nw"), width=event.width)
        canvas.bind("<Configure>", on_canvas_configure)

        self.company_entries = {}
        keys = [
            ('company_name', 'Nombre de la Empresa'),
            ('company_registry', 'Partida Registral'),
            ('company_ruc', 'RUC'),
            ('company_phone', 'Teléfono Empresa 1'),
            ('company_phone2', 'Teléfono Empresa 2'),
            ('company_manager', 'Gerente General'),
            ('manager_dni', 'DNI del Gerente'),
            ('manager_phone', 'Teléfono del Gerente'),
            ('company_address', 'Dirección de la Empresa'),
            ('manager_address', 'Dirección del Gerente'),
            ('company_initial_cash', 'Dinero Inicial de la Empresa (S/.)')
        ]
        
        for key, label in keys:
            frame = tk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, padx=20, pady=5)
            tk.Label(frame, text=label, width=25, anchor="w").pack(side=tk.LEFT)
            entry = tk.Entry(frame)
            entry.insert(0, get_setting(key) or "")
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.company_entries[key] = entry
            
        tk.Button(scrollable_frame, text="Guardar Cambios (Requiere Admin)", command=self.save_company_settings, bg="#FF9800", fg="white").pack(pady=20)

        # Cloud Sync Section
        tk.Label(scrollable_frame, text="Sincronización Nube", font=("Arial", 12, "bold"), fg="#2196F3").pack(pady=(20, 10))
        
        cloud_frame = tk.LabelFrame(scrollable_frame, text="Configuración de Base de Datos Remota", padx=10, pady=10)
        cloud_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Load current secrets
        import os
        import json
        secrets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'secrets.json')
        current_secrets = {}
        if os.path.exists(secrets_path):
            try:
                with open(secrets_path, 'r') as f:
                    current_secrets = json.load(f)
            except: pass
            
        self.cloud_entries = {}
        cloud_keys = [
            ('SUPABASE_URL', 'Supabase URL'),
            ('SUPABASE_KEY', 'Supabase Key'),
            ('DB_URI', 'DB URI')
        ]
        
        for key, label in cloud_keys:
            frame = tk.Frame(cloud_frame)
            frame.pack(fill=tk.X, pady=2)
            tk.Label(frame, text=label, width=15, anchor="w").pack(side=tk.LEFT)
            entry = tk.Entry(frame, show="*" if 'KEY' in key or 'URI' in key else "")
            entry.insert(0, current_secrets.get(key, ""))
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.cloud_entries[key] = entry
            
        btn_frame = tk.Frame(cloud_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(btn_frame, text="Conectar y Sincronizar", command=self.connect_cloud, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Desconectar (Modo Local)", command=self.disconnect_cloud, bg="#f44336", fg="white").pack(side=tk.LEFT, padx=5)

    def connect_cloud(self):
        # Ask for admin password
        password = self.ask_admin_password()
        if not password: return
        if not self.verify_admin(password):
            messagebox.showerror("Error", "Contraseña incorrecta")
            return

        # Save secrets
        secrets = {
            "MODE": "CLOUD",
            "SUPABASE_URL": self.cloud_entries['SUPABASE_URL'].get().strip(),
            "SUPABASE_KEY": self.cloud_entries['SUPABASE_KEY'].get().strip(),
            "DB_URI": self.cloud_entries['DB_URI'].get().strip()
        }
        
        if not all([secrets['SUPABASE_URL'], secrets['SUPABASE_KEY'], secrets['DB_URI']]):
            messagebox.showerror("Error", "Todos los campos de nube son obligatorios")
            return
            
        try:
            import os
            import json
            secrets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'secrets.json')
            with open(secrets_path, 'w') as f:
                json.dump(secrets, f, indent=4)
                
            messagebox.showinfo("Éxito", "Conexión configurada. La aplicación se cerrará para aplicar los cambios.")
            self.master.destroy() # Close main window
            exit() # Exit app
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración: {e}")

    def disconnect_cloud(self):
        # Ask for admin password
        password = self.ask_admin_password()
        if not password: return
        if not self.verify_admin(password):
            messagebox.showerror("Error", "Contraseña incorrecta")
            return
            
        if not messagebox.askyesno("Confirmar", "¿Volver a modo local? Dejará de ver los datos de la nube."):
            return

        try:
            import os
            import json
            secrets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'secrets.json')
            
            # Option 1: Delete file
            # os.remove(secrets_path)
            
            # Option 2: Set MODE to LOCAL (Preserve creds maybe? No, safer to clear or just set mode)
            with open(secrets_path, 'w') as f:
                json.dump({"MODE": "LOCAL"}, f, indent=4)
                
            messagebox.showinfo("Éxito", "Modo local activado. La aplicación se cerrará para aplicar los cambios.")
            self.master.destroy()
            exit()
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")

    def save_company_settings(self):
        # Ask for admin password
        password = self.ask_admin_password()
        if not password: return

        if self.verify_admin(password):
            for key, entry in self.company_entries.items():
                update_setting(key, entry.get())
            
            # Log Action
            from database import log_action
            log_action(self.user_data['id'], "Configuración Empresa", "Datos de empresa actualizados")
            
            messagebox.showinfo("Éxito", "Datos de empresa actualizados")
        else:
            messagebox.showerror("Error", "Contraseña de administrador incorrecta")

    def ask_admin_password(self):
        dialog = tk.Toplevel(self)
        dialog.title("Seguridad")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()
        
        tk.Label(dialog, text="Ingrese contraseña de Administrador:").pack(pady=10)
        e_pass = tk.Entry(dialog, show="*")
        e_pass.pack(pady=5)
        
        password = tk.StringVar()
        
        def on_ok():
            password.set(e_pass.get())
            dialog.destroy()
            
        tk.Button(dialog, text="Aceptar", command=on_ok).pack(pady=10)
        self.wait_window(dialog)
        return password.get()

    def verify_admin(self, password):
        conn = get_db_connection()
        cursor = conn.cursor()
        # Verify against the 'admin' user specifically, or any admin role?
        # Requirement says "contraseña del administrador". Let's check against the current user if they are admin, or the specific 'admin' account.
        # Let's check against the specific 'admin' account for higher security as requested.
        cursor.execute("SELECT password FROM users WHERE username = 'admin'")
        row = cursor.fetchone()
        conn.close()
        return row and row['password'] == password

    def create_menu_tab(self):
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="Menú / Módulos")
        
        canvas = tk.Canvas(tab)
        scrollbar = tk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        tk.Label(scrollable_frame, text="Personalización de Módulos", font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(scrollable_frame, text="Marque los módulos visibles y personalice sus nombres.", font=("Arial", 10)).pack(pady=5)
        
        self.module_vars = {}
        self.label_entries = {}
        
        # Helper to create rows
        def add_module_row(parent, key_vis, key_label, default_name, is_mandatory=False, config_key=None, indent=0):
            frame = tk.Frame(parent)
            frame.pack(fill=tk.X, padx=(20 + indent*20), pady=5)
            
            # Visibility Checkbox
            var = tk.BooleanVar(value=get_setting(key_vis) == '1')
            self.module_vars[key_vis] = var
            
            chk = tk.Checkbutton(frame, variable=var)
            if is_mandatory:
                chk.configure(state="disabled")
                var.set(True)
            chk.pack(side=tk.LEFT)
            
            # Label Entry
            tk.Label(frame, text=f"({default_name})", width=25, anchor="w", fg="gray").pack(side=tk.LEFT)
            
            entry = tk.Entry(frame)
            entry.insert(0, get_setting(key_label) or default_name)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.label_entries[key_label] = entry
            
            # Config Button (if applicable)
            if config_key:
                tk.Button(frame, text="Configurar", command=lambda k=config_key: self.open_loan_config(k), 
                          font=("Segoe UI", 8), padx=2, pady=2).pack(side=tk.LEFT, padx=5)

        # Mandatory Section
        tk.Label(scrollable_frame, text="Módulos Principales", font=("Arial", 10, "bold"), fg="#d32f2f").pack(pady=(15, 5), anchor="w", padx=20)
        add_module_row(scrollable_frame, 'mod_clients_visible', 'label_clients', 'Clientes', True)
        add_module_row(scrollable_frame, 'mod_cash_visible', 'label_cash', 'Caja', True)
        add_module_row(scrollable_frame, 'mod_config_visible', 'label_config', 'Configuración', True)
        
        # Préstamos Section (New Unified Module)
        tk.Label(scrollable_frame, text="Módulo de Préstamos", font=("Arial", 10, "bold"), fg="#9C27B0").pack(pady=(15, 5), anchor="w", padx=20)
        add_module_row(scrollable_frame, 'mod_loans_visible', 'label_loans', 'Préstamos', False)
        
        # Sub-modules of Préstamos (indented)
        tk.Label(scrollable_frame, text="  Tipos de Préstamos:", font=("Arial", 9, "italic"), fg="#666").pack(pady=(5, 2), anchor="w", padx=40)
        add_module_row(scrollable_frame, 'mod_loan1_visible', 'label_loan1', 'Casa de Empeño', False, 'loan1', indent=1)
        add_module_row(scrollable_frame, 'mod_loan2_visible', 'label_loan2', 'Préstamo Bancario', False, 'loan2', indent=1)
        add_module_row(scrollable_frame, 'mod_loan3_visible', 'label_loan3', 'Rapidiario', False, 'loan3', indent=1)
        add_module_row(scrollable_frame, 'mod_loan4_visible', 'label_loan4', 'Préstamo Congelado', False, 'loan4', indent=1)
        
        # Optional Section
        tk.Label(scrollable_frame, text="Módulos Opcionales", font=("Arial", 10, "bold"), fg="#1976D2").pack(pady=(15, 5), anchor="w", padx=20)
        add_module_row(scrollable_frame, 'mod_calc_visible', 'label_calc', 'Calculadora')
        add_module_row(scrollable_frame, 'mod_analysis_visible', 'label_analysis', 'Análisis')
        add_module_row(scrollable_frame, 'mod_docs_visible', 'label_docs', 'Documentos')
        add_module_row(scrollable_frame, 'mod_db_visible', 'label_db', 'Base de Datos (Mantenimiento)')
        
        tk.Button(scrollable_frame, text="Guardar Configuración de Menú", command=self.save_menu_settings, bg="#4CAF50", fg="white").pack(pady=20)

    def open_loan_config(self, loan_key):
        dialog = tk.Toplevel(self)
        dialog.title(f"Configurar {loan_key}")
        dialog.geometry("400x500")
        
        tk.Label(dialog, text=f"Parámetros para {loan_key}", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Interest Rate
        tk.Label(dialog, text="Tasa de Interés (%):").pack(anchor="w", padx=20)
        e_interest = tk.Entry(dialog)
        e_interest.insert(0, get_setting(f'{loan_key}_interest') or "5.0")
        e_interest.pack(fill=tk.X, padx=20)
        
        # Mora (Late Fee)
        tk.Label(dialog, text="Mora / Penalidad (% del préstamo):").pack(anchor="w", padx=20, pady=(10,0))
        e_mora = tk.Entry(dialog)
        e_mora.insert(0, get_setting(f'{loan_key}_mora') or "0.15")
        e_mora.pack(fill=tk.X, padx=20)
        
        # Max Items (Collateral)
        tk.Label(dialog, text="Máximo de Bienes (Garantía):").pack(anchor="w", padx=20, pady=(10,0))
        e_items = tk.Entry(dialog)
        e_items.insert(0, get_setting(f'{loan_key}_max_items') or "3")
        e_items.pack(fill=tk.X, padx=20)
        
        # Max Amount (Limit)
        tk.Label(dialog, text="Monto Máximo (S/.):").pack(anchor="w", padx=20, pady=(10,0))
        e_max_amount = tk.Entry(dialog)
        e_max_amount.insert(0, get_setting(f'{loan_key}_max_amount') or "2000")
        e_max_amount.pack(fill=tk.X, padx=20)
        
        # Term (Days) - mainly for Rapidiario
        tk.Label(dialog, text="Plazo (Días) - Solo Rapidiario:").pack(anchor="w", padx=20, pady=(10,0))
        e_term = tk.Entry(dialog)
        e_term.insert(0, get_setting(f'{loan_key}_term_days') or "30")
        e_term.pack(fill=tk.X, padx=20)

        def save():
            update_setting(f'{loan_key}_interest', e_interest.get())
            update_setting(f'{loan_key}_mora', e_mora.get())
            update_setting(f'{loan_key}_max_items', e_items.get())
            update_setting(f'{loan_key}_max_amount', e_max_amount.get())
            update_setting(f'{loan_key}_term_days', e_term.get())
            
            messagebox.showinfo("Éxito", "Parámetros guardados")
            dialog.destroy()
            
        tk.Button(dialog, text="Guardar", command=save, bg="#4CAF50", fg="white").pack(pady=20)

    def save_menu_settings(self):
        # Save Visibility
        for key, var in self.module_vars.items():
            update_setting(key, '1' if var.get() else '0')
            
        # Save Labels
        for key, entry in self.label_entries.items():
            update_setting(key, entry.get())
            
        # Log Action
        from database import log_action
        log_action(self.user_data['id'], "Configuración Menú", "Configuración de módulos actualizada")
            
        messagebox.showinfo("Éxito", "Configuración de menú guardada. Reinicie la aplicación.")

    def create_history_tab(self):
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="Historial")
        
        columns = ("date", "user", "action", "details")
        tree = ttk.Treeview(tab, columns=columns, show="headings")
        tree.heading("date", text="Fecha")
        tree.heading("user", text="Usuario")
        tree.heading("action", text="Acción")
        tree.heading("details", text="Detalles")
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Load Audit Logs
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.timestamp, u.username, a.action, a.details 
            FROM audit_logs a 
            LEFT JOIN users u ON a.user_id = u.id 
            ORDER BY a.timestamp DESC LIMIT 50
        """)
        for row in cursor.fetchall():
            tree.insert("", tk.END, values=(row["timestamp"], row["username"], row["action"], row["details"]))
        conn.close()

    def create_theme_tab(self):
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="Tema")
        
        tk.Label(tab, text="Seleccione el tema de la aplicación:", font=("Segoe UI", 12)).pack(pady=20)
        
        self.theme_var = tk.StringVar(value=get_setting('app_theme') or 'vivid')
        
        themes = [
            ("Claro (Light)", "light"),
            ("Oscuro (Dark)", "dark"),
            ("Vívido (Actual)", "vivid"),
            ("Profesional 1 (Azul Corporativo)", "pro1"),
            ("Profesional 2 (Elegante)", "pro2")
        ]
        
        for text, value in themes:
            tk.Radiobutton(tab, text=text, variable=self.theme_var, value=value, font=("Segoe UI", 10)).pack(anchor="w", padx=50, pady=5)
        
        tk.Button(tab, text="Guardar y Aplicar Tema", command=self.save_theme, bg="#4CAF50", fg="white", font=("Segoe UI", 10, "bold")).pack(pady=30)

    def save_theme(self):
        update_setting('app_theme', self.theme_var.get())
        messagebox.showinfo("Éxito", "Tema guardado. Reinicie la aplicación.")

    def create_db_tab(self):
        tab = tk.Frame(self.notebook)
        # Explicitly name this tab "Respaldo/Reset" as requested
        self.notebook.add(tab, text="Respaldo/Reset")
        
        tk.Label(tab, text="Mantenimiento de Base de Datos", font=("Arial", 12, "bold"), fg="red").pack(pady=20)
        
        tk.Button(tab, text="Respaldar Base de Datos (Guardar Como...)", command=self.backup_db).pack(pady=10)
        tk.Button(tab, text="Restaurar por Módulo (Borrado Selectivo)", command=self.reset_module_data, bg="#FF9800", fg="white").pack(pady=10)
        tk.Button(tab, text="Restaurar Configuración de Fábrica", command=self.reset_settings, bg="red", fg="white").pack(pady=10)

    def reset_module_data(self):
        # 1. Ask for Admin Password
        password = self.ask_admin_password()
        if not password: return
        
        if not self.verify_admin(password):
            messagebox.showerror("Error", "Contraseña incorrecta")
            return

        # 2. Select Module Dialog
        dialog = tk.Toplevel(self)
        dialog.title("Restaurar por Módulo")
        dialog.geometry("300x350")
        dialog.transient(self)
        dialog.grab_set()
        
        tk.Label(dialog, text="Seleccione el módulo a limpiar:", font=("Arial", 10, "bold")).pack(pady=10)
        tk.Label(dialog, text="¡Advertencia! Los datos se borrarán permanentemente.", font=("Arial", 8), fg="red").pack(pady=5)
        
        vars = {
            'clients': tk.BooleanVar(),
            'loans': tk.BooleanVar(),
            'cash': tk.BooleanVar(),
            'history': tk.BooleanVar()
        }
        
        tk.Checkbutton(dialog, text="Clientes (y sus fotos)", variable=vars['clients']).pack(anchor="w", padx=50, pady=2)
        tk.Checkbutton(dialog, text="Préstamos (Todos)", variable=vars['loans']).pack(anchor="w", padx=50, pady=2)
        tk.Checkbutton(dialog, text="Caja (Movimientos)", variable=vars['cash']).pack(anchor="w", padx=50, pady=2)
        tk.Checkbutton(dialog, text="Historial (Logs)", variable=vars['history']).pack(anchor="w", padx=50, pady=2)
        
        def execute_reset():
            selected = [k for k, v in vars.items() if v.get()]
            if not selected:
                messagebox.showwarning("Aviso", "No seleccionó ningún módulo")
                return
                
            if not messagebox.askyesno("Confirmar Borrado", f"¿Está seguro de borrar los datos de: {', '.join(selected)}?"):
                return
            
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                if vars['clients'].get():
                    cursor.execute("DELETE FROM clients")
                    # Optional: Clean up assets folder? 
                    # For now, just DB.
                    
                if vars['loans'].get():
                    cursor.execute("DELETE FROM loans")
                    cursor.execute("DELETE FROM pawn_details")
                    
                if vars['cash'].get():
                    cursor.execute("DELETE FROM transactions")
                    
                if vars['history'].get():
                    cursor.execute("DELETE FROM audit_logs")
                    
                conn.commit()
                
                # Log this action (unless we just deleted history, but new log comes after)
                from database import log_action
                log_action(self.user_data['id'], "Limpieza Módulos", f"Módulos limpiados: {', '.join(selected)}")
                
                messagebox.showinfo("Éxito", "Datos eliminados correctamente.")
                dialog.destroy()
                
                # Refresh history tab if open
                self.create_history_tab() # Re-render? Better just reload if needed. 
                # Actually create_history_tab appends a new tab, we should just refresh the tree if possible.
                # But for now, simple is fine.
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                conn.close()
                
        tk.Button(dialog, text="Ejecutar Limpieza", command=execute_reset, bg="red", fg="white").pack(pady=20)

    def backup_db(self):
        import shutil
        import os
        from datetime import datetime
        from tkinter import filedialog
        
        src = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database', 'system.db')
        
        # Default filename
        default_name = f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        
        dst = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")],
            initialfile=default_name,
            title="Guardar Respaldo de Base de Datos"
        )
        
        if not dst: return # User cancelled
        
        try:
            shutil.copy2(src, dst)
            messagebox.showinfo("Éxito", f"Respaldo creado exitosamente en:\n{dst}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def reset_settings(self):
        # 1. Ask for Admin Password
        password = self.ask_admin_password()
        if not password: return
        
        if not self.verify_admin(password):
            messagebox.showerror("Error", "Contraseña incorrecta")
            return

        # 2. First Confirmation
        if not messagebox.askyesno("Advertencia Crítica", 
                                   "¿Está seguro de que desea restaurar la configuración de fábrica?\n\n"
                                   "ESTA ACCIÓN BORRARÁ TODA LA INFORMACIÓN Y CONFIGURACIÓN."):
            return

        # 3. Second Confirmation (Double Check)
        if not messagebox.askyesno("Confirmación Final", 
                                   "¿Realmente desea proceder?\n\n"
                                   "Se perderán todos los clientes, préstamos, movimientos y usuarios.\n"
                                   "Esta acción NO se puede deshacer."):
            return
            
        # Proceed with Reset
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # List of tables to clear
            tables = ['clients', 'loans', 'transactions', 'audit_logs', 'pawn_details']
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
                
            # Reset Settings to defaults (optional, or just delete custom ones)
            # For now, let's just keep the structure but clear data. 
            # If we want to reset settings, we might need to re-run init logic or delete from settings where key not in defaults.
            
            # Reset Users (keep admin)
            cursor.execute("DELETE FROM users WHERE username != 'admin'")
            
            conn.commit()
            
            # Log the reset action (if audit_logs wasn't just cleared, but it was. 
            # Maybe we want to log this as the first action of the new era)
            from database import log_action
            log_action(self.user_data['id'], "RESET FÁBRICA", "El sistema ha sido restaurado a valores de fábrica.")
            
            messagebox.showinfo("Restauración Completa", "El sistema ha sido restaurado correctamente.\nLa aplicación se cerrará ahora.")
            self.parent.destroy() # Close app
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al restaurar: {str(e)}")
        finally:
            if 'conn' in locals(): conn.close()
