import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk
from PIL import Image, ImageTk
from ui.ui_utils import apply_styles, create_gradient_image, get_theme_colors, get_module_colors, get_module_icon
from utils.settings_manager import get_setting

from ui.clients_window import ClientsWindow
from ui.loans_window import LoansWindow
from ui.cash_window import CashWindow
from ui.config_window import ConfigWindow
from ui.calculator_window import CalculatorWindow
from ui.analysis_window import AnalysisWindow
from ui.database_window import DatabaseWindow

class ModernButton(tk.Frame):
    """Botón moderno con icono y color personalizado."""
    def __init__(self, parent, text, icon, color, command, **kwargs):
        super().__init__(parent, bg=color, **kwargs)
        self.color = color
        self.hover_color = self.lighten_color(color)
        self.command = command
        
        # Configurar tamaño
        self.config(width=240, height=100, relief='flat', bd=0)
        self.pack_propagate(False)
        
        # Icono
        icon_label = tk.Label(self, text=icon, font=("Segoe UI Emoji", 28), 
                             bg=color, fg='white')
        icon_label.pack(pady=(15, 5))
        
        # Texto
        text_label = tk.Label(self, text=text, font=("Segoe UI", 11, "bold"), 
                             bg=color, fg='white')
        text_label.pack()
        
        # Bind events
        for widget in [self, icon_label, text_label]:
            widget.bind('<Button-1>', lambda e: self.command())
            widget.bind('<Enter>', self.on_enter)
            widget.bind('<Leave>', self.on_leave)
        
        self.icon_label = icon_label
        self.text_label = text_label
    
    def on_enter(self, event):
        self.config(bg=self.hover_color)
        self.icon_label.config(bg=self.hover_color)
        self.text_label.config(bg=self.hover_color)
    
    def on_leave(self, event):
        self.config(bg=self.color)
        self.icon_label.config(bg=self.color)
        self.text_label.config(bg=self.color)
    
    def lighten_color(self, hex_color, factor=0.15):
        """Aclara un color hexadecimal."""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        new_rgb = tuple(min(255, int(c + (255 - c) * factor)) for c in rgb)
        return f'#{new_rgb[0]:02x}{new_rgb[1]:02x}{new_rgb[2]:02x}'

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
            ("Empeño", "mod_loan1_visible", "label_loan1"),
            ("Bancario", "mod_loan2_visible", "label_loan2"),
            ("Rapidiario", "mod_loan3_visible", "label_loan3"),
            ("Caja", "mod_cash_visible", "label_cash"),
            ("Calculadora", "mod_calc_visible", "label_calc"),
            ("Análisis", "mod_analysis_visible", "label_analysis"),
            ("Configuración", "mod_config_visible", "label_config"),
            ("Base de Datos", "mod_db_visible", "label_db"),
            ("Documentos", "mod_docs_visible", "label_docs"),
        ]
        
        # Get module colors
        module_colors = get_module_colors(self.current_theme)
        
        # Grid layout
        row = 0
        col = 0
        max_cols = 3
        
        for default_name, visible_key, label_key in modules:
            is_visible = get_setting(visible_key) == '1'
            if is_visible:
                label = get_setting(label_key) or default_name
                icon = get_module_icon(default_name)
                color = module_colors.get(default_name, '#2196F3')
                
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
        elif module_name == "Empeño":
            LoansWindow(self, "empeno")
        elif module_name == "Bancario":
            LoansWindow(self, "bancario")
        elif module_name == "Rapidiario":
            LoansWindow(self, "rapidiario")
        elif module_name == "Caja":
            CashWindow(self)
        elif module_name == "Configuración":
            ConfigWindow(self, self.user_data)
        elif module_name == "Base de Datos":
            DatabaseWindow(self)
        elif module_name == "Calculadora":
            CalculatorWindow(self)
        elif module_name == "Análisis":
            AnalysisWindow(self)
        elif module_name in ["Loan4", "Loan5"]:
            messagebox.showinfo("Información", f"Módulo '{module_name}' disponible para personalización.")
        elif module_name == "Documentos":
            messagebox.showinfo("Documentos", "Módulo de gestión de documentos (Próximamente).")
        else:
            messagebox.showinfo("Info", f"Módulo {module_name} seleccionado")

    def show_about(self):
        messagebox.showinfo("Acerca de", "Sistema de Casa de Empeño y Microcréditos\\nVersión 1.0")

    def logout(self):
        self.destroy()
        if self.on_logout:
            self.on_logout()
        else:
            self.parent.destroy()

    def on_close(self):
        self.logout()
