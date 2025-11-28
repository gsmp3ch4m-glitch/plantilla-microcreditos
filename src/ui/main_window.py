import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk
from ui.ui_utils import apply_styles
from utils.settings_manager import get_setting

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
        self.geometry("1024x768")
        self.state('zoomed') # Maximize
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Apply theme
        apply_styles(self, get_setting('app_theme') or 'light')
        
        self.create_widgets()
        
    def create_widgets(self):
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        welcome_text = f"Bienvenido, {self.user_data.get('full_name', 'Usuario')} ({self.user_data.get('role', 'user')})"
        ttk.Label(header_frame, text=welcome_text, font=("Segoe UI", 12)).pack(side=tk.LEFT)
        
        ttk.Button(header_frame, text="Cerrar Sesión", command=self.logout, style="Danger.TButton").pack(side=tk.RIGHT)
        
        # Main Menu Container - Centered
        container = tk.Frame(self, bg=self.cget('bg'))
        container.pack(fill=tk.BOTH, expand=True)
        
        # Center frame using place or pack with expand/fill
        self.main_frame = ttk.Frame(container)
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        self.create_menu_buttons()
        
    def create_menu_buttons(self):
        # Define modules based on settings
        # (Default Name, Visibility Key, Label Key)
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
        
        # Grid layout
        row = 0
        col = 0
        max_cols = 3 # Reduced to 3 for better aspect ratio
        
        for default_name, visible_key, label_key in modules:
            is_visible = get_setting(visible_key) == '1'
            if is_visible:
                label = get_setting(label_key) or default_name
                
                # Create button with fixed size to avoid distortion
                # width is in characters, roughly.
                btn = ttk.Button(self.main_frame, text=label, command=lambda n=default_name: self.show_module(n), width=25)
                btn.grid(row=row, column=col, padx=15, pady=15, ipady=15)
                
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
            # Open the Master View
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
        messagebox.showinfo("Acerca de", "Sistema de Casa de Empeño y Microcréditos\nVersión 1.0")

    def logout(self):
        self.destroy()
        if self.on_logout:
            self.on_logout()
        else:
            self.parent.destroy()

    def on_close(self):
        # User requested: Closing main window returns to login
        self.logout()
