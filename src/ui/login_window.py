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
        company_name = get_setting('company_name') or "El Canguro Pro"
        
        # Create ORANGE gradient background (naranja)
        # Degradado naranja claro a naranja oscuro
        gradient_img = create_gradient_image(450, 600, '#FFB74D', '#FF8A65')
        self.bg_photo = ImageTk.PhotoImage(gradient_img)
        
        # Label for background
        bg_label = tk.Label(self, image=self.bg_photo)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Main card/container - White card
        card_bg = '#FFFFFF'
        text_color = '#263238'
        
        card_frame = tk.Frame(self, bg=card_bg, relief='flat', bd=0)
        card_frame.place(relx=0.5, rely=0.5, anchor='center', width=360, height=450)
        
        # Logo/Icon - Lock icon
        logo_label = tk.Label(card_frame, text="🔐", font=("Segoe UI Emoji", 48), 
                             bg=card_bg, fg='#FF8A65')
        logo_label.pack(pady=(25, 10))
        
        # Company Name
        company_label = tk.Label(card_frame, text=company_name, 
                                font=("Segoe UI", 17, "bold"), 
                                bg=card_bg, fg=text_color)
        company_label.pack(pady=(0, 5))
        
        # "INICIAR SESIÓN" Title
        title_label = tk.Label(card_frame, text="INICIAR SESIÓN", 
                              font=("Segoe UI", 12, "bold"), 
                              bg=card_bg, fg=text_color)
        title_label.pack(pady=(0, 20))
        
        # Form container
        form_frame = tk.Frame(card_frame, bg=card_bg)
        form_frame.pack(padx=35, fill=tk.X)
        
        # Usuario
        user_label = tk.Label(form_frame, text="Usuario:", 
                             font=("Segoe UI", 10, "bold"), 
                             bg=card_bg, fg=text_color)
        user_label.pack(anchor="w", pady=(0, 5))
        
        self.entry_user = ttk.Entry(form_frame, font=("Segoe UI", 11))
        self.entry_user.pack(fill=tk.X, ipady=8, pady=(0, 15))
        
        # Contraseña
        pass_label = tk.Label(form_frame, text="Contraseña:", 
                             font=("Segoe UI", 10, "bold"), 
                             bg=card_bg, fg=text_color)
        pass_label.pack(anchor="w", pady=(0, 5))
        
        self.entry_pass = ttk.Entry(form_frame, show="●", font=("Segoe UI", 11))
        self.entry_pass.pack(fill=tk.X, ipady=8, pady=(0, 20))
        
        # Login button - BLUE button
        login_btn = tk.Button(form_frame, text="INICIAR SESIÓN", 
                             command=self.login,
                             bg='#2196F3',  # Azul
                             fg='white',
                             font=("Segoe UI", 11, "bold"),
                             relief='flat', 
                             cursor='hand2',
                             activebackground='#1976D2',
                             activeforeground='white',
                             bd=0)
        login_btn.pack(fill=tk.X, ipady=12)
        
        # Hover effects
        def on_enter(e):
            login_btn.config(bg='#1976D2')
        
        def on_leave(e):
            login_btn.config(bg='#2196F3')
        
        login_btn.bind('<Enter>', on_enter)
        login_btn.bind('<Leave>', on_leave)
        
        # Bind Enter key to login
        self.entry_user.bind('<Return>', lambda e: self.entry_pass.focus())
        self.entry_pass.bind('<Return>', lambda e: self.login())
        
        # Focus on username field
        self.entry_user.focus()
        
    def login(self):
        username = self.entry_user.get()
        password = self.entry_pass.get()
        
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
            self.entry_pass.delete(0, tk.END)
            self.entry_user.focus()
            
    def on_close(self):
        self.parent.destroy()
