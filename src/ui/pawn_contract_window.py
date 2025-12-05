import tkinter as tk
from tkinter import ttk, messagebox
from ui.modern_window import ModernWindow
from database import get_db_connection
from utils.pdf_generator import PDFGenerator
from utils.number_to_text import numero_a_letras
from tkcalendar import DateEntry
from datetime import datetime
import os

class PawnContractWindow(ModernWindow):
    def __init__(self, parent):
        super().__init__(parent, title="Contrato de Préstamo Prendario", width=900, height=700)
        self.loan_data = None
        self.pawn_items = None
        self.create_widgets()

    def create_widgets(self):
        self.create_header("📝 Contrato de Préstamo Prendario")
        
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
        self.entry_search.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.entry_search.bind('<Return>', self.search_client)
        
        # Botón de Lupa
        tk.Button(search_frame, text="🔍", command=self.search_client,
                 bg=self.theme_colors['primary'], fg='white', 
                 font=("Segoe UI", 10, "bold"), relief='flat', width=4, cursor='hand2').pack(side='right')
        
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
        
        # 2. Loan Selection
        loan_card = self.create_card_frame(left_frame)
        loan_card.pack(fill='both', expand=True)
        
        tk.Label(loan_card, text="2. Seleccionar Préstamo (Prendario)", font=("Segoe UI", 12, "bold"), bg=self.card_bg, fg=self.text_color).pack(anchor='w', padx=15, pady=(15, 10))
        
        loan_list_frame = tk.Frame(loan_card, bg=self.card_bg)
        loan_list_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        l_columns = ('ID', 'Monto', 'Fecha', 'Estado')
        self.tree_loans = ttk.Treeview(loan_list_frame, columns=l_columns, show='headings', height=8)
        self.tree_loans.heading('ID', text='ID')
        self.tree_loans.heading('Monto', text='Monto')
        self.tree_loans.heading('Fecha', text='Fecha')
        self.tree_loans.heading('Estado', text='Estado')
        self.tree_loans.column('ID', width=40)
        self.tree_loans.column('Monto', width=80)
        self.tree_loans.column('Fecha', width=80)
        self.tree_loans.column('Estado', width=80)
        
        self.tree_loans.pack(side='left', fill='both', expand=True)
        l_scrollbar = ttk.Scrollbar(loan_list_frame, orient="vertical", command=self.tree_loans.yview)
        l_scrollbar.pack(side='right', fill='y')
        self.tree_loans.configure(yscrollcommand=l_scrollbar.set)
        
        self.tree_loans.bind('<<TreeviewSelect>>', self.on_loan_select)
        
        # --- Right Column: Preview & Action ---
        
        preview_card = self.create_card_frame(right_frame)
        preview_card.pack(fill='both', expand=True)
        
        tk.Label(preview_card, text="3. Datos del Contrato", font=("Segoe UI", 12, "bold"), bg=self.card_bg, fg=self.text_color).pack(anchor='w', padx=15, pady=(15, 10))
        
        # Add Date Field in Preview Card
        date_frame = tk.Frame(preview_card, bg=self.card_bg)
        date_frame.pack(fill='x', padx=15, pady=(0, 10))
        
        tk.Label(date_frame, text="Fecha de Contrato:", font=("Segoe UI", 10, "bold"), 
                bg=self.card_bg, fg=self.text_color).pack(side='left')
                
        self.date_entry = DateEntry(date_frame, width=12, background='darkblue',
                                  foreground='white', borderwidth=2, font=("Segoe UI", 10))
        self.date_entry.pack(side='left', padx=10)
        
        self.info_text = tk.Text(preview_card, height=20, width=40, font=("Consolas", 9), bg="#f5f5f5", relief='flat', padx=10, pady=10)
        self.info_text.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        self.info_text.config(state='disabled')
        
        # Generate Button
        btn_frame = tk.Frame(preview_card, bg=self.card_bg)
        btn_frame.pack(fill='x', padx=15, pady=(0, 20))
        
        self.btn_generate = tk.Button(btn_frame, text="📄 GENERAR CONTRATO", command=self.generate_contract,
                                     bg='#4CAF50', fg='white', font=("Segoe UI", 11, "bold"), 
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
        
        # Filter clients who have at least one 'empeno' loan
        sql = """
            SELECT DISTINCT c.id, c.dni, c.first_name, c.last_name 
            FROM clients c
            JOIN loans l ON c.id = l.client_id
            WHERE (c.first_name LIKE ? OR c.last_name LIKE ? OR c.dni LIKE ?)
            AND LOWER(l.loan_type) IN ('empeno', 'empeño')
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
        
        # Only Pawn Shop loans (empeno)
        sql = """
            SELECT id, amount, start_date, status 
            FROM loans 
            WHERE client_id = ? AND loan_type = 'empeno'
            ORDER BY start_date DESC
        """
        cursor.execute(sql, (client_id,))
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            self.tree_loans.insert('', 'end', values=(row['id'], f"S/ {row['amount']:.2f}", row['start_date'], row['status']))

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
        preview = f"CLIENTE:\n{self.loan_data['first_name']} {self.loan_data['last_name']}\nDNI: {self.loan_data['dni']}\n\n"
        preview += f"PRÉSTAMO:\nMonto: S/ {self.loan_data['amount']:.2f}\n"
        preview += f"Interés: {self.loan_data['interest_rate']}%\n"
        preview += f"Fecha: {self.loan_data['start_date']}\n\n"
        
        preview += "GARANTÍAS:\n"
        if not self.pawn_items:
            preview += "⚠️ NO HAY GARANTÍAS REGISTRADAS\n"
        else:
            for item in self.pawn_items:
                preview += f"- {item['item_type']} {item['brand']}: {item['description']}\n"
        
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, preview)
        self.info_text.config(state='disabled')

    def clear_preview(self):
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.config(state='disabled')
        self.btn_generate.config(state='disabled')
        self.loan_data = None
        self.pawn_items = None

    def generate_contract(self):
        if not self.loan_data:
            return
            
        try:
            # Prepare Data Dictionary
            data = {}
            
            # Dates from DateEntry
            fecha_contrato = self.date_entry.get_date()
            data['dia'] = fecha_contrato.day
            data['mes'] = self.get_month_name(fecha_contrato.month)
            data['anio'] = fecha_contrato.year
            
            # Client
            data['cliente_nombre'] = f"{self.loan_data['first_name']} {self.loan_data['last_name']}"
            data['cliente_dni'] = self.loan_data['dni']
            data['cliente_direccion'] = self.loan_data['address'] or "Dirección no registrada"
            
            # Loan
            monto = self.loan_data['amount']
            data['monto_prestamo'] = f"{monto:,.2f}"
            data['monto_texto'] = numero_a_letras(monto)
            
            # Interest Calculation
            # User request: "si damos prestamo al 5% en el contrado deve salir interes 3% y 2% de gastos administrativos"
            # So DB rate is the TOTAL rate.
            tasa_total = self.loan_data['interest_rate']
            gastos_admin = 2.0
            tasa_base = max(0, tasa_total - gastos_admin)
            
            data['tasa_interes'] = tasa_base
            data['tasa_interes_base'] = tasa_base
            data['tasa_total'] = tasa_total
            
            # Calculate Interest Amount (Monthly) based on TOTAL rate
            interes_monto = monto * (tasa_total / 100)
            data['interes_monto'] = f"{interes_monto:,.2f}"
            data['interes_texto'] = numero_a_letras(interes_monto)
            
            # Total to Pay (Capital + Interest)
            total_pagar = monto + interes_monto
            data['total_pagar'] = f"{total_pagar:,.2f}"
            data['total_texto'] = numero_a_letras(total_pagar)
            
            # Mora (0.1% daily)
            mora_diaria = total_pagar * 0.001
            data['mora_diaria'] = f"{mora_diaria:,.2f}"
            data['mora_texto'] = numero_a_letras(mora_diaria)
            
            # Items
            items_list = []
            for item in self.pawn_items:
                items_list.append({
                    'tipo': item['item_type'],
                    'marca': item['brand'],
                    'descripcion': f"{item['description']} {item['characteristics']}",
                    'estado': item['condition'],
                    'valor': f"{item['market_value']:,.2f}"
                })
            data['items'] = items_list
            
            # Generate PDF
            generator = PDFGenerator()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"contrato_empeno_{self.loan_data['id']}_{timestamp}.pdf"
            filepath = os.path.join(generator.reports_dir, filename)
            
            path = generator.generate_pawn_contract(filepath, data)
            
            messagebox.showinfo("Éxito", f"Contrato generado correctamente:\n{path}")
            os.startfile(path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar contrato: {e}")
            import traceback
            traceback.print_exc()


    def get_month_name(self, month_num):
        months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        return months[month_num - 1]
