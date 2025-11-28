import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk
from PIL import Image, ImageTk
import sqlite3
from database import get_db_connection
from ui.ui_utils import apply_styles, create_gradient_image, get_theme_colors
from utils.settings_manager import get_setting

class LoginWindow(tk.Toplevel):
    def __init__(self, parent, on_login_success):
        super().__init__(parent)
        self.parent = parent
        self.on_login_success = on_login_success
        self.title("Iniciar Sesión")
        
        # Center the window
        window_width = 450
        window_height = 550
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
        
        # Create gradient background
        theme_colors = get_theme_colors(self.current_theme)
        gradient_img = create_gradient_image(450, 550, 
                                            theme_colors['gradient_start'], 
                                            theme_colors['gradient_end'])
        self.bg_photo = ImageTk.PhotoImage(gradient_img)
        
        # Label for background
        bg_label = tk.Label(self, image=self.bg_photo)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Determine text color based on theme
        if self.current_theme in ['oscuro', 'morado']:
            text_color = '#FFFFFF'
            card_bg = '#37474F' if self.current_theme == 'oscuro' else '#8E24AA'
        else:
            text_color = '#263238'
            card_bg = '#FFFFFF'
        
        # Main card/container
        card_frame = tk.Frame(self, bg=card_bg, relief='flat', bd=0)
        card_frame.place(relx=0.5, rely=0.5, anchor='center', width=350, height=420)
        
        # Logo/Icon
        logo_label = tk.Label(card_frame, text="🔐", font=("Segoe UI Emoji", 48), 
                             bg=card_bg, fg=theme_colors['gradient_end'])
        logo_label.pack(pady=(30, 10))
        
        # Company Name
        company_label = tk.Label(card_frame, text=company_name, 
                                font=("Segoe UI", 20, "bold"), 
                                bg=card_bg, fg=text_color)
        company_label.pack(pady=(0, 5))
        
        # "INGRESAR" Title
        title_label = tk.Label(card_frame, text="INICIAR SESIÓN", 
                              font=("Segoe UI", 12, "bold"), 
                              bg=card_bg, fg=text_color)
        title_label.pack(pady=(0, 25))
        
        # Form container
        form_frame = tk.Frame(card_frame, bg=card_bg)
        form_frame.pack(padx=30, fill=tk.X)
        
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
        self.entry_pass.pack(fill=tk.X, ipady=8, pady=(0, 25))
        
        # Login button - Modern style
        login_btn = tk.Button(form_frame, text="INGRESAR", 
                             command=self.login,
                             bg=theme_colors['gradient_end'], 
                             fg='white',
                             font=("Segoe UI", 11, "bold"),
                             relief='flat', 
                             cursor='hand2',
                             activebackground=self.darken_color(theme_colors['gradient_end']),
                             activeforeground='white')
        login_btn.pack(fill=tk.X, ipady=12)
        
        # Bind Enter key to login
        self.entry_user.bind('<Return>', lambda e: self.entry_pass.focus())
        self.entry_pass.bind('<Return>', lambda e: self.login())
        
        # Focus on username field
        self.entry_user.focus()
        
    def darken_color(self, hex_color, factor=0.2):
        """Oscurece un color hexadecimal."""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        new_rgb = tuple(max(0, int(c * (1 - factor))) for c in rgb)
        return f'#{new_rgb[0]:02x}{new_rgb[1]:02x}{new_rgb[2]:02x}'
        
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
