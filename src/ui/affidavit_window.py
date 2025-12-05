import tkinter as tk
from tkinter import ttk, messagebox
from ui.modern_window import ModernWindow
from database import get_db_connection
from utils.pdf_generator import PDFGenerator
from datetime import datetime
import os

class AffidavitWindow(ModernWindow):
    def __init__(self, parent):
        super().__init__(parent, title="Declaración Jurada", width=900, height=700)
        self.loan_data = None
        self.pawn_items = None
        self.create_widgets()

    def create_widgets(self):
        self.create_header("📜 Declaración Jurada")
        
        content = self.create_content_frame()
        
        # Split into two columns
        left_frame = tk.Frame(content, bg=self.bg_color)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        right_frame = tk.Frame(content, bg=self.bg_color)
        right_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # --- Left Column: Selection ---
        
        # 1. Client Search
        search_card = self.create_card_frame(left_frame)
        search_card.pack(fill='x', pady=(0, 20))
        
        tk.Label(search_card, text="1. Buscar Cliente", font=("Segoe UI", 12, "bold"), bg=self.card_bg, fg=self.text_color).pack(anchor='w', padx=15, pady=(15, 10))
        
        search_frame = tk.Frame(search_card, bg=self.card_bg)
        search_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        self.entry_search = ttk.Entry(search_frame, font=("Segoe UI", 10))
        self.entry_search.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.entry_search.bind('<Return>', self.search_client)
        
        tk.Button(search_frame, text="🔍 Buscar", command=self.search_client,
                 bg=self.theme_colors['primary'], fg='white', relief='flat', padx=10).pack(side='right')
        
        # Client List
        list_frame = tk.Frame(search_card, bg=self.card_bg)
        list_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        columns = ('ID', 'DNI', 'Nombre')
        self.tree_clients = ttk.Treeview(list_frame, columns=columns, show='headings', height=6)
        self.tree_clients.heading('ID', text='ID')
        self.tree_clients.heading('DNI', text='DNI')
        self.tree_clients.heading('Nombre', text='Nombre')
        self.tree_clients.column('ID', width=40)
        self.tree_clients.column('DNI', width=80)
        self.tree_clients.column('Nombre', width=200)
        
        self.tree_clients.pack(side='left', fill='both', expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree_clients.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree_clients.configure(yscrollcommand=scrollbar.set)
        
        self.tree_clients.bind('<<TreeviewSelect>>', self.on_client_select)
        
        # 2. Loan Selection (Only with Collateral)
        loan_card = self.create_card_frame(left_frame)
        loan_card.pack(fill='both', expand=True)
        
        tk.Label(loan_card, text="2. Seleccionar Préstamo (Con Garantía)", font=("Segoe UI", 12, "bold"), bg=self.card_bg, fg=self.text_color).pack(anchor='w', padx=15, pady=(15, 10))
        
        loan_list_frame = tk.Frame(loan_card, bg=self.card_bg)
        loan_list_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        l_columns = ('ID', 'Tipo', 'Monto', 'Estado')
        self.tree_loans = ttk.Treeview(loan_list_frame, columns=l_columns, show='headings', height=8)
        self.tree_loans.heading('ID', text='ID')
        self.tree_loans.heading('Tipo', text='Tipo')
        self.tree_loans.heading('Monto', text='Monto')
        self.tree_loans.heading('Estado', text='Estado')
        self.tree_loans.column('ID', width=40)
        self.tree_loans.column('Tipo', width=80)
        self.tree_loans.column('Monto', width=80)
        self.tree_loans.column('Estado', width=80)
        
        self.tree_loans.pack(side='left', fill='both', expand=True)
        l_scrollbar = ttk.Scrollbar(loan_list_frame, orient="vertical", command=self.tree_loans.yview)
        l_scrollbar.pack(side='right', fill='y')
        self.tree_loans.configure(yscrollcommand=l_scrollbar.set)
        
        self.tree_loans.bind('<<TreeviewSelect>>', self.on_loan_select)
        
        # --- Right Column: Preview & Action ---
        
        preview_card = self.create_card_frame(right_frame)
        preview_card.pack(fill='both', expand=True)
        
        tk.Label(preview_card, text="3. Vista Previa", font=("Segoe UI", 12, "bold"), bg=self.card_bg, fg=self.text_color).pack(anchor='w', padx=15, pady=(15, 10))
        
        self.info_text = tk.Text(preview_card, height=20, width=40, font=("Consolas", 9), bg="#f5f5f5", relief='flat', padx=10, pady=10)
        self.info_text.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        self.info_text.config(state='disabled')
        
        # Generate Button
        btn_frame = tk.Frame(preview_card, bg=self.card_bg)
        btn_frame.pack(fill='x', padx=15, pady=(0, 20))
        
        self.btn_generate = tk.Button(btn_frame, text="📄 GENERAR DECLARACIÓN", command=self.generate_affidavit,
                                     bg='#607D8B', fg='white', font=("Segoe UI", 11, "bold"), 
                                     relief='flat', cursor='hand2', state='disabled')
        self.btn_generate.pack(fill='x', ipady=10)

    def search_client(self, event=None):
        query = self.entry_search.get().strip()
        if not query:
            return
            
        # Clear previous
        for item in self.tree_clients.get_children():
            self.tree_clients.delete(item)
        self.tree_loans.delete(*self.tree_loans.get_children())
        self.clear_preview()
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Filter clients who have loans with collateral
        sql = """
            SELECT DISTINCT c.id, c.dni, c.first_name, c.last_name 
            FROM clients c
            JOIN loans l ON c.id = l.client_id
            JOIN pawn_details pd ON l.id = pd.loan_id
            WHERE (c.first_name LIKE ? OR c.last_name LIKE ? OR c.dni LIKE ?)
        """
        param = f"%{query}%"
        cursor.execute(sql, (param, param, param))
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            self.tree_clients.insert('', 'end', values=(row['id'], row['dni'], f"{row['first_name']} {row['last_name']}"))

    def on_client_select(self, event):
        selection = self.tree_clients.selection()
        if not selection:
            return
            
        client_id = self.tree_clients.item(selection[0])['values'][0]
        self.load_loans(client_id)
        self.clear_preview()

    def load_loans(self, client_id):
        for item in self.tree_loans.get_children():
            self.tree_loans.delete(item)
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Only loans with collateral
        sql = """
            SELECT DISTINCT l.id, l.loan_type, l.amount, l.status 
            FROM loans l
            JOIN pawn_details pd ON l.id = pd.loan_id
            WHERE l.client_id = ?
            ORDER BY l.start_date DESC
        """
        cursor.execute(sql, (client_id,))
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            self.tree_loans.insert('', 'end', values=(row['id'], row['loan_type'].capitalize(), f"S/ {row['amount']:.2f}", row['status']))

        # Auto-select if only one loan
        if len(rows) == 1:
            item_id = self.tree_loans.get_children()[0]
            self.tree_loans.selection_set(item_id)
            self.on_loan_select(None)

    def on_loan_select(self, event):
        selection = self.tree_loans.selection()
        if not selection:
            self.btn_generate.config(state='disabled')
            return
            
        loan_id = self.tree_loans.item(selection[0])['values'][0]
        self.load_contract_data(loan_id)
        self.btn_generate.config(state='normal')

    def load_contract_data(self, loan_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get Loan + Client
        cursor.execute("""
            SELECT l.*, c.first_name, c.last_name, c.dni, c.address 
            FROM loans l 
            JOIN clients c ON l.client_id = c.id 
            WHERE l.id = ?
        """, (loan_id,))
        self.loan_data = cursor.fetchone()
        
        # Get Pawn Items
        cursor.execute("SELECT * FROM pawn_details WHERE loan_id = ?", (loan_id,))
        self.pawn_items = cursor.fetchall()
        
        conn.close()
        
        # Prepare Preview Text
        preview = "DECLARACIÓN JURADA DE PROCEDENCIA LÍCITA\n\n"
        preview += f"YO: {self.loan_data['first_name']} {self.loan_data['last_name']}\n"
        preview += f"DNI: {self.loan_data['dni']}\n"
        preview += f"DIRECCIÓN: {self.loan_data['address']}\n\n"
        
        preview += "Declaro bajo juramento que los siguientes bienes son de mi exclusiva propiedad y tienen procedencia lícita:\n\n"
        
        for item in self.pawn_items:
            preview += f"- {item['item_type']} {item['brand']}: {item['description']}\n"
            
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, preview)
        self.info_text.config(state='disabled')

    def generate_affidavit(self):
        if not self.loan_data or not self.pawn_items:
            return
            
        try:
            # Prepare Data
            data = {
                'client_name': f"{self.loan_data['first_name']} {self.loan_data['last_name']}",
                'client_dni': self.loan_data['dni'],
                'client_address': self.loan_data['address'] or "Dirección no registrada",
                'items': self.pawn_items,
                'date': datetime.now().strftime("%d de %B del %Y")
            }
            
            # Generate PDF
            generator = PDFGenerator()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"declaracion_jurada_{self.loan_data['id']}_{timestamp}.pdf"
            filepath = os.path.join(generator.reports_dir, filename)
            
            path = generator.generate_affidavit(filepath, data)
            
            messagebox.showinfo("Éxito", f"Declaración generada correctamente:\n{path}")
            os.startfile(path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar declaración: {e}")
            import traceback
            traceback.print_exc()

    def clear_preview(self):
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.config(state='disabled')
        self.btn_generate.config(state='disabled')
        self.loan_data = None
        self.pawn_items = None
