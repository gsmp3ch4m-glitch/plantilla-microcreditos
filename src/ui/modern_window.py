"""
Clase base para ventanas modernas con tema aplicado.
Todas las ventanas de módulos deben heredar de esta clase.
"""
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from ui.ui_utils import apply_styles, create_gradient_image, get_theme_colors
from utils.settings_manager import get_setting

class ModernWindow(tk.Toplevel):
    """Clase base para ventanas modernas con tema."""
    
    def __init__(self, parent, title="Ventana", width=1000, height=700, use_gradient=True):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        
        # Get current theme
        self.current_theme = get_setting('app_theme') or 'turquesa'
        self.theme_colors = get_theme_colors(self.current_theme)
        
        # Apply theme
        apply_styles(self, self.current_theme)
        
        # Window size and position
        self.setup_window(width, height)
        
        # Create gradient background if requested
        if use_gradient:
            self.create_gradient_background(width, height)
        
        # Determine text colors based on theme
        self.setup_colors()
        
    def setup_window(self, width, height):
        """Configura el tamaño y posición de la ventana."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_gradient_background(self, width, height):
        """Crea un fondo degradado para la ventana."""
        gradient_img = create_gradient_image(width, height,
                                            self.theme_colors['gradient_start'],
                                            self.theme_colors['gradient_end'])
        self.bg_photo = ImageTk.PhotoImage(gradient_img)
        
        # Label for background
        bg_label = tk.Label(self, image=self.bg_photo)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        
    def setup_colors(self):
        """Configura los colores de texto y fondo según el tema."""
        if self.current_theme in ['oscuro', 'morado']:
            self.text_color = '#FFFFFF'
            self.card_bg = '#37474F' if self.current_theme == 'oscuro' else '#8E24AA'
            self.header_bg = self.theme_colors['gradient_start']
        else:
            self.text_color = '#263238'
            self.card_bg = '#FFFFFF'
            self.header_bg = self.theme_colors['gradient_start']
    
    def create_header(self, title, show_back_button=True, back_command=None):
        """Crea un header moderno para la ventana."""
        header_frame = tk.Frame(self, bg=self.header_bg, height=60)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        header_frame.pack_propagate(False)
        
        # Back button
        if show_back_button:
            back_btn = tk.Button(header_frame, text="← Volver",
                                command=back_command or self.destroy,
                                bg=self.theme_colors['gradient_end'],
                                fg='white',
                                font=("Segoe UI", 10, "bold"),
                                relief='flat',
                                cursor='hand2',
                                padx=15, pady=5)
            back_btn.pack(side=tk.LEFT, padx=5)
        
        # Title
        title_label = tk.Label(header_frame, text=title,
                              font=("Segoe UI", 16, "bold"),
                              fg=self.text_color,
                              bg=self.header_bg)
        title_label.pack(side=tk.LEFT, padx=20)
        
        return header_frame
    
    def create_content_frame(self):
        """Crea un frame para el contenido principal."""
        content_frame = tk.Frame(self, bg=self.theme_colors['gradient_end'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        return content_frame
    
    def create_card_frame(self, parent, width=None, height=None):
        """Crea una tarjeta/card moderna."""
        card = tk.Frame(parent, bg=self.card_bg, relief='flat', bd=0)
        if width and height:
            card.config(width=width, height=height)
            card.pack_propagate(False)
        return card
