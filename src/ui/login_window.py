import tkinter as tk
from tkinter import messagebox
import sqlite3
from database import get_db_connection

class LoginWindow(tk.Toplevel):
    def __init__(self, parent, on_login_success):
        super().__init__(parent)
        self.parent = parent
        self.on_login_success = on_login_success
        self.title("Iniciar Sesión")
        # Center the window
        window_width = 400
        window_height = 450
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_cordinate = int((screen_width/2) - (window_width/2))
        y_cordinate = int((screen_height/2) - (window_height/2))
        self.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")
        
        self.resizable(False, False)
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.create_widgets()
        
    def create_widgets(self):
        from utils.settings_manager import get_setting
        from ui.ui_utils import apply_styles
        import tkinter.ttk as ttk
        
        # Apply global styles to this window
        current_theme = get_setting('app_theme') or 'vivid'
        apply_styles(self, current_theme)
        
        company_name = get_setting('company_name') or "Sistema de Gestión"
        
        # Main Frame - Background color depends on theme, but we can just use the root bg
        bg_color = self.cget('bg')
        main_frame = tk.Frame(self, bg=bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Company Name
        ttk.Label(main_frame, text=company_name, font=("Segoe UI", 18, "bold"), foreground=ttk.Style().lookup("TLabel", "foreground")).pack(pady=(0, 10))
        
        # "INGRESAR" Title
        ttk.Label(main_frame, text="INGRESAR", font=("Segoe UI", 14, "bold"), foreground=ttk.Style().lookup("TLabel", "foreground")).pack(pady=(0, 20))
        
        ttk.Label(main_frame, text="Usuario:").pack(anchor="w")
        self.entry_user = ttk.Entry(main_frame, font=("Segoe UI", 11))
        self.entry_user.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(main_frame, text="Contraseña:").pack(anchor="w")
        self.entry_pass = ttk.Entry(main_frame, show="*", font=("Segoe UI", 11))
        self.entry_pass.pack(fill=tk.X, pady=(0, 30))
        
        ttk.Button(main_frame, text="INGRESAR", command=self.login, style="Primary.TButton").pack(fill=tk.X, ipady=5)
        
    def login(self):
        username = self.entry_user.get()
        password = self.entry_pass.get()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            self.destroy()
            # Convert sqlite3.Row to dict to avoid AttributeError: 'sqlite3.Row' object has no attribute 'get'
            user_dict = dict(user)
            self.on_login_success(user_dict)
        else:
            messagebox.showerror("Error", "Credenciales incorrectas")
            
    def on_close(self):
        self.parent.destroy()
