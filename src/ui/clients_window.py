import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
import shutil
from PIL import Image, ImageTk
from database import get_db_connection
from ui.ui_utils import ScrollableFrame, ask_admin_password

class ClientsWindow(tk.Toplevel):
    def __init__(self, parent, filter_loan_type=None, on_select_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.filter_loan_type = filter_loan_type
        self.on_select_callback = on_select_callback
        
        title = "Gestión de Clientes"
        if filter_loan_type == 'empeno':
            title += " - Casa de Empeño"
        elif filter_loan_type == 'rapidiario':
            title += " - Rapidiario"
        elif filter_loan_type == 'bancario':
            title += " - Préstamo Bancario"
        elif filter_loan_type == 'congelado': # or 'frozen' depending on internal name
            title += " - Préstamo Congelado"
            
        self.title(title)
        self.geometry("1100x750")
        
        # Check permissions
        self.user_perms = parent.user_data.get('permissions', '')
        self.can_add = 'all' in self.user_perms or 'client_add' in self.user_perms
        self.can_edit = 'all' in self.user_perms or 'client_edit' in self.user_perms
        self.can_delete = 'all' in self.user_perms or 'client_delete' in self.user_perms
        
        self.selected_item = None
        self.photo_path = None
        
        self.create_widgets()
        self.load_clients()

    def create_widgets(self):
        # Main Container with ScrollableFrame
        self.scroll_container = ScrollableFrame(self, bg="#E0F2F1") # Light Teal BG
        self.scroll_container.pack(fill=tk.BOTH, expand=True)
        
        main_frame = self.scroll_container.scrollable_frame
        
        # Title
        header_text = "Gestión de Clientes"
        if self.filter_loan_type == 'empeno':
            header_text = "Clientes - Casa de Empeño"
        elif self.filter_loan_type == 'rapidiario':
            header_text = "Clientes - Rapidiario"
        elif self.filter_loan_type == 'bancario':
            header_text = "Clientes - Préstamo Bancario"
        elif self.filter_loan_type == 'congelado':
            header_text = "Clientes - Préstamo Congelado"
            
        tk.Label(main_frame, text=header_text, font=("Segoe UI", 20, "bold"), bg="#E0F2F1", fg="#00695C").pack(pady=(20, 10))

        # Content Area (Form + List)
        content_frame = tk.Frame(main_frame, bg="#E0F2F1")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # --- Left Side: Form ---
        form_frame = ttk.LabelFrame(content_frame, text="Datos del Cliente", padding=10)
        form_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20), anchor="n")
        
        # Grid layout for form
        ttk.Label(form_frame, text="DNI:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_dni = ttk.Entry(form_frame, width=25)
        self.entry_dni.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Nombres:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.entry_name = ttk.Entry(form_frame, width=35)
        self.entry_name.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Apellidos:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.entry_lastname = ttk.Entry(form_frame, width=35)
        self.entry_lastname.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Teléfono:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.entry_phone = ttk.Entry(form_frame, width=25)
        self.entry_phone.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Email:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.entry_email = ttk.Entry(form_frame, width=35)
        self.entry_email.grid(row=4, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Ocupación:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        self.entry_occupation = ttk.Entry(form_frame, width=35)
        self.entry_occupation.grid(row=5, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Dir. Domicilio:").grid(row=6, column=0, padx=5, pady=5, sticky="ne")
        self.entry_address = tk.Text(form_frame, width=35, height=3, font=("Segoe UI", 9))
        self.entry_address.grid(row=6, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Dir. Trabajo:").grid(row=7, column=0, padx=5, pady=5, sticky="ne")
        self.entry_work_address = tk.Text(form_frame, width=35, height=3, font=("Segoe UI", 9))
        self.entry_work_address.grid(row=7, column=1, padx=5, pady=5)
        
        # Photo Section
        ttk.Label(form_frame, text="Foto:").grid(row=8, column=0, padx=5, pady=5, sticky="ne")
        self.lbl_photo = tk.Label(form_frame, text="Sin Foto", relief="groove", width=40, height=20, bg="#B2DFDB")
        self.lbl_photo.grid(row=8, column=1, padx=5, pady=5)
        
        ttk.Button(form_frame, text="Subir Foto", command=self.upload_photo).grid(row=9, column=1, padx=5, pady=5)

        # Buttons
        btn_frame = tk.Frame(form_frame, bg="#E0F2F1")
        btn_frame.grid(row=10, column=0, columnspan=2, pady=20)
        
        self.btn_add = ttk.Button(btn_frame, text="Agregar", command=self.add_client, style="Success.TButton")
        self.btn_add.grid(row=0, column=0, padx=5)
        
        self.btn_update = ttk.Button(btn_frame, text="Actualizar", command=self.update_client, style="Primary.TButton")
        self.btn_update.grid(row=0, column=1, padx=5)
        self.btn_update.config(state="disabled")
        
        self.btn_delete = ttk.Button(btn_frame, text="Eliminar", command=self.delete_client, style="Danger.TButton")
        self.btn_delete.grid(row=1, column=0, padx=5, pady=5)
        self.btn_delete.config(state="disabled")
        
        ttk.Button(btn_frame, text="Limpiar", command=self.clear_form).grid(row=1, column=1, padx=5, pady=5)

        # --- Right Side: List ---
        list_frame = tk.Frame(content_frame, bg="#E0F2F1")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Search
        search_frame = tk.Frame(list_frame, bg="#E0F2F1")
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Buscar:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        # Remove auto-trace to use button instead, or keep both? User asked for "lupa". Let's keep trace + button.
        self.search_var.trace("w", lambda name, index, mode: self.load_clients()) 
        self.entry_search = ttk.Entry(search_frame, textvariable=self.search_var)
        self.entry_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.entry_search.bind('<Return>', lambda e: self.load_clients())
        
        # Search Button (Lupa)
        self.btn_search = ttk.Button(search_frame, text="🔍", command=self.load_clients, width=3)
        self.btn_search.pack(side=tk.LEFT, padx=5)

        # Treeview
        columns = ("id", "dni", "fullname", "phone", "occupation")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("dni", text="DNI")
        self.tree.heading("fullname", text="Nombre Completo")
        self.tree.heading("phone", text="Teléfono")
        self.tree.heading("occupation", text="Ocupación")
        
        self.tree.column("id", width=40)
        self.tree.column("dni", width=80)
        self.tree.column("fullname", width=200)
        self.tree.column("phone", width=100)
        self.tree.column("occupation", width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        if self.on_select_callback:
            self.tree.bind("<Double-1>", self.on_double_click)

    def on_double_click(self, event):
        selected = self.tree.selection()
        if not selected: return
        
        item = self.tree.item(selected[0])
        client_id = item['values'][0]
        
        if self.on_select_callback:
            self.on_select_callback(client_id)
            self.destroy() # Close window after selection

    def upload_photo(self):
        file_path = filedialog.askopenfilename(filetypes=[("Imágenes", "*.jpg;*.jpeg;*.png")])
        if file_path:
            # Copy to assets
            assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'clients')
            os.makedirs(assets_dir, exist_ok=True)
            
            dni = self.entry_dni.get() or "temp"
            filename = f"client_{dni}_{os.path.basename(file_path)}"
            dest_path = os.path.join(assets_dir, filename)
            
            try:
                shutil.copy(file_path, dest_path)
                self.photo_path = dest_path
                self.load_photo_preview(dest_path)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar la imagen: {e}")

    def load_photo_preview(self, path):
        try:
            img = Image.open(path)
            img = img.resize((300, 300), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.lbl_photo.config(image=photo, text="", width=300, height=300)
            self.lbl_photo.image = photo # Keep reference
        except Exception:
            self.lbl_photo.config(image="", text="Error al cargar", width=40, height=20)

    def add_client(self):
        if not self.can_add:
            messagebox.showwarning("Permiso Denegado", "No tiene permiso para agregar clientes.")
            return
            
        dni = self.entry_dni.get()
        name = self.entry_name.get()
        lastname = self.entry_lastname.get()
        
        if not dni or not name or not lastname:
            messagebox.showwarning("Advertencia", "DNI, Nombre y Apellido son obligatorios")
            return
            
        # Save photo if exists
        if self.photo_path and not os.path.dirname(self.photo_path).endswith('assets\\clients'):
             # Logic to save photo is handled in upload_photo but we might want to ensure it's in the right place or just use the path
             pass

        conn = get_db_connection()
        try:
            # Get current user ID to assign as analyst
            user_id = self.parent.user_data['id']
            
            conn.execute("""
                INSERT INTO clients (dni, first_name, last_name, address, phone, email, work_address, occupation, photo_path, analyst_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (dni, name, lastname, self.entry_address.get("1.0", tk.END).strip(), self.entry_phone.get(), self.entry_email.get(),
                  self.entry_work_address.get("1.0", tk.END).strip(), self.entry_occupation.get(), self.photo_path, user_id))
            conn.commit()
            
            # Log Action
            from database import log_action
            log_action(user_id, "Crear Cliente", f"Cliente creado: {dni} - {name} {lastname}")

            messagebox.showinfo("Éxito", "Cliente agregado correctamente")
            self.clear_form()
            self.load_clients()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "El DNI ya está registrado")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    def update_client(self):
        if not self.can_edit:
            messagebox.showwarning("Permiso Denegado", "No tiene permiso para editar clientes.")
            return

        if not self.selected_item: return
        
        # Security Check: Admin Password
        if not ask_admin_password(self):
            return

        client_id = self.tree.item(self.selected_item)['values'][0]
        
        conn = get_db_connection()
        try:
            conn.execute("""
                UPDATE clients SET dni=?, first_name=?, last_name=?, address=?, phone=?, email=?, work_address=?, occupation=?, photo_path=?
                WHERE id=?
            """, (self.entry_dni.get(), self.entry_name.get(), self.entry_lastname.get(), 
                  self.entry_address.get("1.0", tk.END).strip(), self.entry_phone.get(), self.entry_email.get(),
                  self.entry_work_address.get("1.0", tk.END).strip(), self.entry_occupation.get(), self.photo_path,
                  client_id))
            conn.commit()
            
            # Log Action
            from database import log_action
            user_id = self.parent.user_data['id']
            log_action(user_id, "Actualizar Cliente", f"Cliente actualizado: {self.entry_dni.get()} - {self.entry_name.get()} {self.entry_lastname.get()}")

            messagebox.showinfo("Éxito", "Cliente actualizado")
            self.clear_form()
            self.load_clients()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    def delete_client(self):
        if not self.can_delete:
            messagebox.showwarning("Permiso Denegado", "No tiene permiso para eliminar clientes.")
            return

        if not self.selected_item: return
        
        # Security Check: Admin Password
        if not ask_admin_password(self):
            return

        if not messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este cliente?"):
            return
            
        client_id = self.tree.item(self.selected_item)['values'][0]
        conn = get_db_connection()
        try:
            conn.execute("DELETE FROM clients WHERE id=?", (client_id,))
            conn.commit()
            
            # Log Action
            from database import log_action
            user_id = self.parent.user_data['id']
            log_action(user_id, "Eliminar Cliente", f"Cliente eliminado: ID {client_id}")

            messagebox.showinfo("Éxito", "Cliente eliminado")
            self.clear_form()
            self.load_clients()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected: return
        self.selected_item = selected[0]
        values = self.tree.item(self.selected_item)['values']
        client_id = values[0]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        client = cursor.fetchone()
        conn.close()
        
        if client:
            self.entry_dni.delete(0, tk.END)
            self.entry_dni.insert(0, client['dni'])
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, client['first_name'])
            self.entry_lastname.delete(0, tk.END)
            self.entry_lastname.insert(0, client['last_name'])
            
            self.entry_address.delete("1.0", tk.END)
            self.entry_address.insert("1.0", client['address'] or "")
            
            self.entry_phone.delete(0, tk.END)
            self.entry_phone.insert(0, client['phone'] or "")
            self.entry_email.delete(0, tk.END)
            self.entry_email.insert(0, client['email'] or "")
            
            self.entry_work_address.delete("1.0", tk.END)
            self.entry_work_address.insert("1.0", client['work_address'] or "")
            
            self.entry_occupation.delete(0, tk.END)
            self.entry_occupation.insert(0, client['occupation'] or "")
            
            self.photo_path = client['photo_path']
            if self.photo_path and os.path.exists(self.photo_path):
                self.load_photo_preview(self.photo_path)
            else:
                self.lbl_photo.config(image="", text="Sin Foto", width=40, height=20)
                self.lbl_photo.image = None

            self.btn_add.config(state="disabled")
            self.btn_update.config(state="normal" if self.can_edit else "disabled")
            self.btn_delete.config(state="normal" if self.can_delete else "disabled")

    def clear_form(self):
        self.entry_dni.delete(0, tk.END)
        self.entry_name.delete(0, tk.END)
        self.entry_lastname.delete(0, tk.END)
        self.entry_address.delete("1.0", tk.END)
        self.entry_phone.delete(0, tk.END)
        self.entry_email.delete(0, tk.END)
        self.entry_work_address.delete("1.0", tk.END)
        self.entry_occupation.delete(0, tk.END)
        self.photo_path = None
        self.lbl_photo.config(image="", text="Sin Foto", width=40, height=20)
        self.lbl_photo.image = None
        
        self.selected_item = None
        self.btn_add.config(state="normal" if self.can_add else "disabled")
        self.btn_update.config(state="disabled")
        self.btn_delete.config(state="disabled")

    def load_clients(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        search_term = self.search_var.get()
        params = []
        
        # Removed strict filtering by loan type to show all clients
        query = "SELECT * FROM clients WHERE 1=1"
            
        if search_term:
            query += " AND (dni LIKE ? OR first_name LIKE ? OR last_name LIKE ?)"
            params.extend([f'%{search_term}%'] * 3)
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            fullname = f"{row['first_name']} {row['last_name']}"
            # Convert row to dict to safely use .get()
            row_dict = dict(row)
            self.tree.insert("", tk.END, values=(row["id"], row["dni"], fullname, row["phone"], row_dict.get("occupation", "")))
