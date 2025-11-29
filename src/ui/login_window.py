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
        
        self.resizable(False, False)
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Get current theme
        self.current_theme = get_setting('app_theme') or 'turquesa'
        
        # Apply theme
        apply_styles(self, self.current_theme)
        
        self.create_widgets()
        
    def create_widgets(self):
        company_name = get_setting('company_name') or 'El Canguro Pro'
        
        # Create ORANGE gradient background (naranja)
        gradient_img = create_gradient_image(450, 600, '#FFB74D', '#FF8A65')
        self.bg_photo = ImageTk.PhotoImage(gradient_img)
        
        # Label for background
        bg_label = tk.Label(self, image=self.bg_photo)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Main container - everything on orange background
        main_frame = tk.Frame(self, bg='#FFB74D', bd=0)
        main_frame.place(relx=0.5, rely=0.5, anchor='center', width=360)
        
        # Logo/Icon - Lock icon
        logo_label = tk.Label(main_frame, text="🔐", font=("Segoe UI Emoji", 60), 
                             bg='#FFB74D', fg='white')
        logo_label.pack(pady=(20, 15))
        
        # Company Name - WHITE TEXT on orange background
        company_label = tk.Label(main_frame, text=company_name, 
                                font=("Segoe UI", 18, "bold"), 
                                bg='#FFB74D', fg='white')
        company_label.pack(pady=(0, 10))
        
        # "INICIAR SESIÓN" Title - WHITE TEXT
        title_label = tk.Label(main_frame, text="INICIAR SESIÓN", 
                              font=("Segoe UI", 13, "bold"), 
                              bg='#FFB74D', fg='white')
        title_label.pack(pady=(0, 30))
        
        # Form container
        form_frame = tk.Frame(main_frame, bg='#FFB74D')
        form_frame.pack(padx=30, fill=tk.X)
        
        # Usuario label - WHITE TEXT
        user_label = tk.Label(form_frame, text="Usuario:", 
                             font=("Segoe UI", 11, "bold"), 
                             bg='#FFB74D', fg='white')
        user_label.pack(anchor='w', pady=(0, 5))
        
        # Usuario entry - WHITE BACKGROUND
        self.user_entry = ttk.Entry(form_frame, font=("Segoe UI", 11))
        self.user_entry.pack(fill=tk.X, ipady=8, pady=(0, 20))
        self.user_entry.focus()
        
        # Contraseña label - WHITE TEXT
        pass_label = tk.Label(form_frame, text="Contraseña:", 
                             font=("Segoe UI", 11, "bold"), 
                             bg='#FFB74D', fg='white')
        pass_label.pack(anchor='w', pady=(0, 5))
        
        # Contraseña entry - WHITE BACKGROUND
        self.pass_entry = ttk.Entry(form_frame, show="●", font=("Segoe UI", 11))
        self.pass_entry.pack(fill=tk.X, ipady=8, pady=(0, 30))
        
        # Login button - BLUE
        login_btn = tk.Button(form_frame, text="INICIAR SESIÓN", 
                             command=self.login,
                             bg='#2196F3', fg='white',
                             font=("Segoe UI", 12, "bold"),
                             relief='flat', cursor='hand2',
                             padx=20, pady=12)
        login_btn.pack(fill=tk.X)
        
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
