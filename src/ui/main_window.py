import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk
from PIL import Image, ImageTk
from ui.ui_utils import apply_styles, create_gradient_image, get_theme_colors, get_module_colors, get_module_icon, ModernButton
from utils.settings_manager import get_setting
from ui.notifications_window import NotificationsWindow
from database import get_db_connection
import threading
import time
from datetime import datetime

from ui.clients_window import ClientsWindow
from ui.loans_window import LoansWindow
from ui.cash_window import CashWindow
from ui.config_window import ConfigWindow
from ui.calculator_window import CalculatorWindow
from ui.analysis_window import AnalysisWindow
from ui.database_window import DatabaseWindow


class MainWindow(tk.Toplevel):
    def __init__(self, parent, user_data, on_logout=None):
        super().__init__(parent)
        self.parent = parent
        self.user_data = user_data
        self.on_logout = on_logout
        
        self.title(f"Sistema - {get_setting('company_name') or 'El Canguro Pro'}")
        
        # Centrar la ventana en la pantalla
        window_width = 1000
        window_height = 700
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Get current theme
        self.current_theme = get_setting('app_theme') or 'turquesa'
        
        # Apply theme
        apply_styles(self, self.current_theme)
        
        self.create_widgets()
        
        # Notification System
        self.pending_notifications = []
        self.current_notif_index = 0
        self.toast_frame = None
        self.check_notifications() # Initial check
        self.start_notification_timer() # Start 30min loop
        
    def create_widgets(self):
        # Create gradient background
        theme_colors = get_theme_colors(self.current_theme)
        gradient_img = create_gradient_image(1000, 700, 
                                            theme_colors['gradient_start'], 
                                            theme_colors['gradient_end'])
        self.bg_photo = ImageTk.PhotoImage(gradient_img)
        
        # Label for background
        bg_label = tk.Label(self, image=self.bg_photo)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Determine text color and bg based on theme
        if self.current_theme in ['oscuro', 'morado']:
            text_color = '#FFFFFF'
            header_bg = theme_colors['gradient_start']
        else:
            text_color = '#263238'
            header_bg = theme_colors['gradient_start']
        
        # Header frame
        header_frame = tk.Frame(self, bg=header_bg, height=60)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        header_frame.pack_propagate(False)
        
        # Welcome text
        welcome_text = f"Bienvenido, {self.user_data.get('full_name', 'Usuario')} ({self.user_data.get('role', 'user')})"
        welcome_label = tk.Label(header_frame, text=welcome_text, 
                                font=("Segoe UI", 13, "bold"), 
                                fg=text_color, bg=header_bg)
        welcome_label.pack(side=tk.LEFT, padx=10)
        
        # Logout button
        logout_btn = tk.Button(header_frame, text="Cerrar Sesión 🔒", 
                              command=self.logout,
                              bg='#E74C3C', fg='white', 
                              font=("Segoe UI", 10, "bold"),
                              relief='flat', padx=15, pady=8,
                              cursor='hand2')
        logout_btn.pack(side=tk.RIGHT, padx=10)
        
        # Main container for buttons
        main_container = tk.Frame(self, bg=theme_colors['gradient_end'])
        main_container.place(relx=0.5, rely=0.55, anchor='center')
        
        self.create_menu_buttons(main_container)
        
    def create_menu_buttons(self, container):
        # Define modules based on settings
        modules = [
            ("Clientes", "mod_clients_visible", "label_clients"),
            ("Préstamos", "mod_loans_visible", "label_loans"),  # New unified module
            ("Caja", "mod_cash_visible", "label_cash"),
            ("Calculadora", "mod_calc_visible", "label_calc"),
            ("Análisis", "mod_analysis_visible", "label_analysis"),
            ("Configuración", "mod_config_visible", "label_config"),
            ("Base de Datos", "mod_db_visible", "label_db"),
            ("Activos", "mod_assets_visible", "label_assets"),
            ("Notificaciones", "mod_notif_visible", "label_notif"),
            ("Documentos", "mod_docs_visible", "label_docs"),
        ]
        
        # Get user role and permissions
        user_role = self.user_data.get('role', 'user')
        
        # Define role-based permissions
        role_permissions = {
            'admin': ['all'],  # Admin tiene acceso a todo
            'caja': ['Caja', 'Clientes', 'Calculadora', 'Documentos', 'Notificaciones'],  # Cajero
            'cajero': ['Caja', 'Clientes', 'Calculadora', 'Documentos', 'Notificaciones'],  # Cajero (alias)
            'analista': ['Préstamos', 'Clientes', 'Calculadora', 'Documentos', 'Notificaciones', 'Activos'],  # Analista
        }
        
        # Get allowed modules for this user
        allowed_modules = role_permissions.get(user_role, [])
        
        # Get module colors
        module_colors = get_module_colors(self.current_theme)
        
        # Grid layout
        row = 0
        col = 0
        max_cols = 3
        
        for default_name, visible_key, label_key in modules:
            is_visible = get_setting(visible_key) == '1'
            
            # Check if user has permission to see this module
            has_permission = 'all' in allowed_modules or default_name in allowed_modules
            
            if is_visible and has_permission:
                label = get_setting(label_key) or default_name
                icon = get_module_icon(default_name)
                if default_name == "Notificaciones" and icon == "📦": icon = "🔔"
                
                color = module_colors.get(default_name, '#2196F3')
                if default_name == "Notificaciones": color = "#FF9800"
                
                # Create button
                btn = ModernButton(container, label, icon, color, 
                                  lambda n=default_name: self.show_module(n))
                btn.grid(row=row, column=col, padx=12, pady=12)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

    def show_module(self, module_name):
        if module_name == "Clientes":
            ClientsWindow(self)
        elif module_name == "Préstamos":
            from ui.loans_menu_window import LoansMenuWindow
            LoansMenuWindow(self, self.user_data)
        elif module_name == "Caja":
            CashWindow(self, self.user_data)
        elif module_name == "Configuración":
            ConfigWindow(self, self.user_data)
        elif module_name == "Base de Datos":
            DatabaseWindow(self)
        elif module_name == "Calculadora":
            CalculatorWindow(self)
        elif module_name == "Análisis":
            AnalysisWindow(self)
        elif module_name == "Notificaciones":
            NotificationsWindow(self, self.user_data)
        elif module_name == "Documentos":
            from ui.documents_menu_window import DocumentsMenuWindow
            DocumentsMenuWindow(self)
        elif module_name == "Activos":
            from ui.assets_window import AssetsWindow
            AssetsWindow(self, self.user_data)
        else:
            messagebox.showinfo("Info", f"Módulo {module_name} seleccionado")

    def show_about(self):
        messagebox.showinfo("Acerca de", "Sistema de Casa de Empeño y Microcréditos\\nVersión 2.1")

    def logout(self):
        self.destroy()
        if self.on_logout:
            self.on_logout()
        else:
            self.parent.destroy()

    def on_close(self):
        self.logout()

    # --- Notification Logic ---
    def start_notification_timer(self):
        # Check every 30 minutes (1800000 ms)
        self.after(1800000, self.notification_loop)

    def notification_loop(self):
        self.check_notifications()
        self.start_notification_timer()

    def check_notifications(self):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            # Fetch pending notifications
            cursor.execute("""
                SELECT n.id, n.notify_date, n.description, u.username 
                FROM notifications n
                LEFT JOIN users u ON n.created_by = u.id
                WHERE n.is_done = 0 OR n.is_done = FALSE
            """)
            rows = cursor.fetchall()
            
            self.pending_notifications = []
            now = datetime.now()
            
            for row in rows:
                if isinstance(row, dict):
                    ndate = row['notify_date']
                    if isinstance(ndate, str):
                        try:
                            ndate = datetime.strptime(ndate, "%Y-%m-%d %H:%M:%S")
                        except: pass
                    
                    if ndate <= now:
                        self.pending_notifications.append(row)
                else:
                    # Tuple
                    ndate = row[1]
                    if isinstance(ndate, str):
                        try:
                            ndate = datetime.strptime(ndate, "%Y-%m-%d %H:%M:%S")
                        except: pass
                    
                    if ndate <= now:
                        self.pending_notifications.append({
                            'id': row[0],
                            'notify_date': row[1],
                            'description': row[2],
                            'username': row[3]
                        })
            
            if self.pending_notifications:
                self.current_notif_index = 0
                self.show_next_notification()
                
        except Exception as e:
            print(f"Error checking notifications: {e}")
        finally:
            conn.close()

    def show_next_notification(self):
        if not self.pending_notifications:
            return
            
        if self.current_notif_index >= len(self.pending_notifications):
            self.current_notif_index = 0
            
        notif = self.pending_notifications[self.current_notif_index]
        self.show_toast(notif)
        
        # Schedule next one after 5 seconds + small buffer
        self.current_notif_index += 1
        self.after(6000, self.show_next_notification)

    def show_toast(self, notif):
        if self.toast_frame:
            self.toast_frame.destroy()
            
        # Create Toast Frame (Top Right)
        self.toast_frame = tk.Frame(self, bg="#333333", padx=15, pady=10, relief="raised", bd=2)
        
        # Position: Top Right, below header
        self.toast_frame.place(relx=1.0, y=80, anchor="ne", x=-20)
        
        # Content
        tk.Label(self.toast_frame, text="🔔 Recordatorio", font=("Arial", 10, "bold"), fg="#FF9800", bg="#333333").pack(anchor="w")
        tk.Label(self.toast_frame, text=f"{notif['description']}", font=("Arial", 11), fg="white", bg="#333333", wraplength=250).pack(anchor="w", pady=5)
        
        meta_text = f"Fecha: {notif['notify_date']} | Por: {notif['username']}"
        tk.Label(self.toast_frame, text=meta_text, font=("Arial", 8), fg="#AAAAAA", bg="#333333").pack(anchor="w")
        
        # Mark Done Button (Small)
        tk.Button(self.toast_frame, text="Ya lo realicé", command=lambda: self.mark_toast_done(notif['id']), 
                 bg="#4CAF50", fg="white", font=("Arial", 8), bd=0, padx=5).pack(anchor="e", pady=(5,0))
        
        # Auto hide after 5 seconds
        self.after(5000, self.hide_toast)

    def hide_toast(self):
        if self.toast_frame:
            self.toast_frame.destroy()
            self.toast_frame = None

    def mark_toast_done(self, notif_id):
        conn = get_db_connection()
        try:
            conn.execute("UPDATE notifications SET is_done = ? WHERE id = ?", (1, notif_id))
            conn.commit()
            
            # Remove from local list so it doesn't show again in this cycle
            self.pending_notifications = [n for n in self.pending_notifications if n['id'] != notif_id]
            
            self.hide_toast()
        except Exception as e:
            print(f"Error marking toast done: {e}")
        finally:
            conn.close()
