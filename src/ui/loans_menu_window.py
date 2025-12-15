import tkinter as tk
from tkinter import ttk
from ui.modern_window import ModernWindow
from ui.ui_utils import get_module_colors, get_module_icon
from utils.settings_manager import get_setting

class ModernButton(tk.Frame):
    """Botón moderno con icono y color personalizado."""
    def __init__(self, parent, text, icon, color, command):
        super().__init__(parent, bg=color, cursor='hand2')
        self.color = color
        self.command = command
        
        # Fixed size
        self.config(width=220, height=100)
        self.pack_propagate(False)
        
        # Icon
        icon_label = tk.Label(self, text=icon, font=("Segoe UI Emoji", 28), 
                             bg=color, fg='white')
        icon_label.pack(pady=(15, 5))
        
        # Text
        text_label = tk.Label(self, text=text, font=("Segoe UI", 11, "bold"), 
                             bg=color, fg='white')
        text_label.pack()
        
        # Bind click events
        self.bind('<Button-1>', lambda e: self.command())
        icon_label.bind('<Button-1>', lambda e: self.command())
        text_label.bind('<Button-1>', lambda e: self.command())
        
        # Hover effects
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        icon_label.bind('<Enter>', self.on_enter)
        icon_label.bind('<Leave>', self.on_leave)
        text_label.bind('<Enter>', self.on_enter)
        text_label.bind('<Leave>', self.on_leave)
        
    def on_enter(self, e):
        lighter = self.lighten_color(self.color)
        self.config(bg=lighter)
        for widget in self.winfo_children():
            widget.config(bg=lighter)
    
    def on_leave(self, e):
        self.config(bg=self.color)
        for widget in self.winfo_children():
            widget.config(bg=self.color)
    
    def lighten_color(self, hex_color, factor=0.2):
        """Aclara un color hexadecimal."""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        new_rgb = tuple(min(255, int(c + (255 - c) * factor)) for c in rgb)
        return f'#{new_rgb[0]:02x}{new_rgb[1]:02x}{new_rgb[2]:02x}'

class LoansMenuWindow(ModernWindow):
    """Ventana de menú de préstamos con los 3 tipos."""
    def __init__(self, parent, user_data):
        super().__init__(parent, title="Préstamos", width=800, height=500)
        self.user_data = user_data
        self.create_content()
        
    def create_content(self):
        # Header
        self.create_header("💰 Módulo de Préstamos")
        
        # Content
        content = self.create_content_frame()
        
        # Container for buttons
        container = tk.Frame(content, bg=self.theme_colors['gradient_end'])
        container.pack(expand=True)
        
        # Get module colors
        module_colors = get_module_colors(self.current_theme)
        
        # Define loan types
        loan_types = [
            ("Empeño", "Casa de Empeño", "mod_loan1_visible", "label_loan1"),
            ("Bancario", "Préstamo Bancario", "mod_loan2_visible", "label_loan2"),
            ("Rapidiario", "Rapidiario", "mod_loan3_visible", "label_loan3"),
            ("Congelado", "Préstamos Congelados", "mod_loan4_visible", "label_loan4"),
        ]
        
        # Create buttons in a grid (2x2)
        row = 0
        col = 0
        max_cols = 2  # 2 columns for better layout
        
        for default_name, display_name, visible_key, label_key in loan_types:
            # Default to visible if setting is missing (None) or '1'. Only hide if explicitly '0'.
            setting_val = get_setting(visible_key)
            is_visible = setting_val != '0'
            
            # FORCE VISIBILITY for Congelado
            if default_name == "Congelado":
                is_visible = True
                
            if is_visible:
                label = get_setting(label_key) or display_name
                icon = get_module_icon(default_name)
                color = module_colors.get(default_name, '#2196F3')
                
                # Create button
                btn = ModernButton(container, label, icon, color, 
                                  lambda n=default_name: self.open_loan_module(n))
                btn.grid(row=row, column=col, padx=15, pady=20)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
    
    def open_loan_module(self, module_name):
        """Abre el módulo de préstamo correspondiente."""
        from ui.loans_window import LoansWindow
        
        # Determine loan type
        loan_type_map = {
            "Empeño": "pawn",
            "Bancario": "bank", 
            "Rapidiario": "rapid",
            "Congelado": "frozen"
        }
        
        loan_type = loan_type_map.get(module_name, "pawn")
        
        # Open loans window with specific type
        LoansWindow(self, self.user_data, loan_type)
