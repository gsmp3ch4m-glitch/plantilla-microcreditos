import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk
from PIL import Image, ImageTk
import sqlite3
from database import get_db_connection
from ui.ui_utils import apply_styles, create_gradient_image
from utils.settings_manager import get_setting

class LoginWindow(tk.Toplevel):
    def __init__(self, parent, on_login_success):
        super().__init__(parent)
        self.parent = parent
        self.on_login_success = on_login_success
        self.title("Iniciar Sesión")
        
        # Center the window
        window_width = 450
        window_height = 600
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_cordinate = int((screen_width/2) - (window_width/2))
        y_cordinate = int((screen_height/2) - (window_height/2))
        self.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")
        self.attributes('-topmost', True) # Force to top
        
        self.resizable(False, False)
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Get current theme
        try:
            self.current_theme = get_setting('app_theme') or 'turquesa'
        except Exception:
            self.current_theme = 'turquesa'
        
        # Apply theme
        try:
            apply_styles(self, self.current_theme)
        except Exception:
            pass
        
        self.create_widgets()
        self.lift()
        self.focus_force()
        self.attributes('-topmost', False) # Disable topmost after showing so it doesn't block other windows
        
    def create_widgets(self):
        company_name = get_setting('company_name') or 'El Canguro Pro'
        
        # Create ORANGE gradient background (naranja)
        gradient_img = create_gradient_image(450, 600, '#FFB74D', '#FF8A65')
        self.bg_photo = ImageTk.PhotoImage(gradient_img)
        
        # Label for background
        bg_label = tk.Label(self, image=self.bg_photo)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Logo/Icon - Lock icon - directly on gradient background
        logo_label = tk.Label(self, text="🔐", font=("Segoe UI Emoji", 60), 
                             bg='#FFB74D', fg='white')
        logo_label.place(relx=0.5, y=80, anchor='center')
        
        # Company Name - WHITE TEXT - directly on gradient background
        company_label = tk.Label(self, text=company_name, 
                                font=("Segoe UI", 18, "bold"), 
                                bg='#FFB74D', fg='white',
                                wraplength=400)  # Allow text wrapping for long names
        company_label.place(relx=0.5, y=180, anchor='center')
        
        # "INICIAR SESIÓN" Title - WHITE TEXT
        title_label = tk.Label(self, text="INICIAR SESIÓN", 
                              font=("Segoe UI", 13, "bold"), 
                              bg='#FFB74D', fg='white')
        title_label.place(relx=0.5, y=230, anchor='center')
        
        # Usuario label - WHITE TEXT
        user_label = tk.Label(self, text="Usuario:", 
                             font=("Segoe UI", 11, "bold"), 
                             bg='#FFB74D', fg='white')
        user_label.place(x=45, y=280, anchor='w')
        
        # Usuario entry - WHITE BACKGROUND
        self.user_entry = ttk.Entry(self, font=("Segoe UI", 11))
        self.user_entry.place(x=45, y=310, width=360, height=35)
        self.user_entry.focus()
        
        # Contraseña label - WHITE TEXT
        pass_label = tk.Label(self, text="Contraseña:", 
                             font=("Segoe UI", 11, "bold"), 
                             bg='#FFB74D', fg='white')
        pass_label.place(x=45, y=365, anchor='w')
        
        # Contraseña entry - WHITE BACKGROUND
        self.pass_entry = ttk.Entry(self, show="●", font=("Segoe UI", 11))
        self.pass_entry.place(x=45, y=395, width=360, height=35)
        
        # Login button - BLUE
        login_btn = tk.Button(self, text="INICIAR SESIÓN", 
                             command=self.login,
                             bg='#2196F3', fg='white',
                             font=("Segoe UI", 12, "bold"),
                             relief='flat', cursor='hand2',
                             padx=20, pady=12)
        login_btn.place(x=45, y=460, width=360, height=50)
        
        # Bind Enter key
        self.user_entry.bind('<Return>', lambda e: self.pass_entry.focus())
        self.pass_entry.bind('<Return>', lambda e: self.login())
        
        # Hover effects for button
        def on_enter(e):
            login_btn.config(bg='#1976D2')
        
        def on_leave(e):
            login_btn.config(bg='#2196F3')
        
        login_btn.bind('<Enter>', on_enter)
        login_btn.bind('<Leave>', on_leave)
    
    def login(self):
        username = self.user_entry.get()
        password = self.pass_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Por favor ingrese usuario y contraseña")
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            self.destroy()
            # Convert sqlite3.Row to dict to avoid AttributeError
            user_dict = dict(user)
            self.on_login_success(user_dict)
        else:
            messagebox.showerror("Error", "Credenciales incorrectas")
            self.pass_entry.delete(0, tk.END)
            self.user_entry.focus()
            
    def on_close(self):
        self.parent.destroy()
