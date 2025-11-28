import tkinter as tk
from tkinter import ttk

class ScrollableFrame(tk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.cget('bg'))

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Mousewheel scrolling - Bind only when entering the frame
        self.canvas.bind('<Enter>', self._bound_to_mousewheel)
        self.canvas.bind('<Leave>', self._unbound_to_mousewheel)

    def _bound_to_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        try:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except Exception:
            pass

def apply_styles(root, theme_name='light'):
    style = ttk.Style(root)
    style.theme_use('clam')  # Base theme

    # Theme Definitions
    themes = {
        'light': {
            'primary': '#2196F3', 'secondary': '#FFC107', 'bg': '#f5f5f5', 'text': '#333333',
            'btn_bg': '#e0e0e0', 'btn_active': '#bdbdbd',
            'primary_btn_active': '#1976D2', 'danger_bg': '#f44336', 'danger_active': '#d32f2f',
            'success_bg': '#4CAF50', 'success_active': '#388E3C',
            'tree_head_bg': '#e0e0e0', 'tree_head_fg': '#333333',
            'label_fg': '#555555'
        },
        'dark': {
            'primary': '#90CAF9', 'secondary': '#FFD54F', 'bg': '#303030', 'text': '#ffffff',
            'btn_bg': '#424242', 'btn_active': '#616161',
            'primary_btn_active': '#42A5F5', 'danger_bg': '#EF5350', 'danger_active': '#E53935',
            'success_bg': '#66BB6A', 'success_active': '#43A047',
            'tree_head_bg': '#424242', 'tree_head_fg': '#ffffff',
            'label_fg': '#bdbdbd'
        },
        'vivid': { # Cheerful / Vívido
            'primary': '#00796B', 'secondary': '#F57C00', 'bg': '#B2DFDB', 'text': '#333333', # Darker BG
            'btn_bg': '#80CBC4', 'btn_active': '#4DB6AC',
            'primary_btn_active': '#004D40', 'danger_bg': '#D32F2F', 'danger_active': '#B71C1C',
            'success_bg': '#F57C00', 'success_active': '#EF6C00',
            'tree_head_bg': '#80CBC4', 'tree_head_fg': '#004D40',
            'label_fg': '#004D40'
        },
        'pro1': { # Professional 1 (Corporate Blue)
            'primary': '#0D47A1', 'secondary': '#1976D2', 'bg': '#E3F2FD', 'text': '#000000',
            'btn_bg': '#BBDEFB', 'btn_active': '#90CAF9',
            'primary_btn_active': '#002171', 'danger_bg': '#B71C1C', 'danger_active': '#8E0000',
            'success_bg': '#1B5E20', 'success_active': '#003300',
            'tree_head_bg': '#1565C0', 'tree_head_fg': '#ffffff',
            'label_fg': '#0D47A1'
        },
        'pro2': { # Professional 2 (Elegant Slate/Gold)
            'primary': '#455A64', 'secondary': '#D4AF37', 'bg': '#ECEFF1', 'text': '#263238',
            'btn_bg': '#CFD8DC', 'btn_active': '#B0BEC5',
            'primary_btn_active': '#263238', 'danger_bg': '#C62828', 'danger_active': '#8E0000',
            'success_bg': '#D4AF37', 'success_active': '#A88825',
            'tree_head_bg': '#546E7A', 'tree_head_fg': '#ffffff',
            'label_fg': '#37474F'
        }
    }

    colors = themes.get(theme_name, themes['light'])

    # Configure generic styles
    style.configure(".", background=colors['bg'], foreground=colors['text'], font=("Segoe UI", 10, "bold"))
    style.configure("TLabel", background=colors['bg'], foreground=colors['text'], font=("Segoe UI", 10, "bold"))
    style.configure("TButton", padding=8, relief="flat", background=colors['btn_bg'], foreground=colors['text'], font=("Segoe UI", 10, "bold"))
    style.map("TButton", background=[('active', colors['btn_active'])])
    
    # Custom Button Styles
    style.configure("Primary.TButton", background=colors['primary'], foreground="white", font=("Segoe UI", 10, "bold"))
    style.map("Primary.TButton", background=[('active', colors['primary_btn_active'])])
    
    style.configure("Danger.TButton", background=colors['danger_bg'], foreground="white", font=("Segoe UI", 10, "bold"))
    style.map("Danger.TButton", background=[('active', colors['danger_active'])])
    
    style.configure("Success.TButton", background=colors['success_bg'], foreground="white", font=("Segoe UI", 10, "bold"))
    style.map("Success.TButton", background=[('active', colors['success_active'])])

    # Treeview
    style.configure("Treeview", 
                    background="white" if theme_name != 'dark' else '#424242',
                    fieldbackground="white" if theme_name != 'dark' else '#424242',
                    foreground=colors['text'],
                    rowheight=28,
                    font=("Segoe UI", 10, "bold"))
    style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background=colors['tree_head_bg'], foreground=colors['tree_head_fg'])
    style.map("Treeview", background=[('selected', colors['primary'])], foreground=[('selected', 'white')])
    
    # Entry
    style.configure("TEntry", padding=5, fieldbackground="white" if theme_name != 'dark' else '#616161', foreground=colors['text'], font=("Segoe UI", 10, "bold"))
    
    # Labelframe
    style.configure("TLabelframe", background=colors['bg'])
    style.configure("TLabelframe.Label", background=colors['bg'], font=("Segoe UI", 11, "bold"), foreground=colors['label_fg'])

    root.configure(bg=colors['bg'])

def ask_admin_password(parent):
    """Prompts for admin password and verifies it against the database."""
    from tkinter import simpledialog, messagebox
    import sqlite3
    from database import get_db_connection
    
    password = simpledialog.askstring("Seguridad", "Ingrese Contraseña de Administrador:", parent=parent, show='*')
    if not password:
        return False
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE role='admin' LIMIT 1")
    admin_data = cursor.fetchone()
    conn.close()
    
    if admin_data and admin_data['password'] == password:
        return True
    else:
        messagebox.showerror("Error", "Contraseña incorrecta")
        return False
