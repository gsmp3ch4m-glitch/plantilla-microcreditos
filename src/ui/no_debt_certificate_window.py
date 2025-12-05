import tkinter as tk
from tkinter import ttk, messagebox
from ui.modern_window import ModernWindow
from database import get_db_connection
from utils.pdf_generator import PDFGenerator
from datetime import datetime
import os

class NoDebtCertificateWindow(ModernWindow):
    """Ventana para generar Constancias de No Adeudo para préstamos de empeño pagados."""
    
    def __init__(self, parent):
        super().__init__(parent, title="Constancia de No Adeudo", width=900, height=700)
        self.loan_data = None
        self.client_data = None
        self.pawn_items = []
        self.create_widgets()

    def create_widgets(self):
        self.create_header("✅ Constancia de No Adeudo")
        
        content = self.create_content_frame()
        
        # Split into two columns
        left_frame = tk.Frame(content, bg=self.bg_color)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        right_frame = tk.Frame(content, bg=self.bg_color)
        right_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # --- Left Column: Client Search ---
        
        search_card = self.create_card_frame(left_frame)
        search_card.pack(fill='x', pady=(0, 15))
        
        tk.Label(search_card, text="1. Buscar Cliente", font=("Segoe UI", 12, "bold"), 
                bg=self.card_bg, fg=self.text_color).pack(anchor='w', padx=15, pady=(15, 10))
        
        search_frame = tk.Frame(search_card, bg=self.card_bg)
        search_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        tk.Label(search_frame, text="Nombre o DNI:", bg=self.card_bg, 
                fg=self.text_color, font=("Segoe UI", 10)).pack(anchor='w', pady=(0, 5))
        
        entry_frame = tk.Frame(search_frame, bg=self.card_bg)
        entry_frame.pack(fill='x')
        
        self.entry_search = ttk.Entry(entry_frame, font=("Segoe UI", 10))
        self.entry_search.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.entry_search.bind('<Return>', self.search_client)
        
        tk.Button(entry_frame, text="🔍 Buscar", command=self.search_client,
                 bg=self.theme_colors['primary'], fg='white', relief='flat', 
                 padx=15, cursor='hand2').pack(side='right')
        
        # Client List
        tk.Label(search_card, text="Resultados:", font=("Segoe UI", 10, "bold"), 
                bg=self.card_bg, fg=self.text_color).pack(anchor='w', padx=15, pady=(10, 5))
        
        list_frame = tk.Frame(search_card, bg=self.card_bg)
        list_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        columns = ('ID', 'DNI', 'Nombre')
        self.tree_clients = ttk.Treeview(list_frame, columns=columns, show='headings', height=6)
        self.tree_clients.heading('ID', text='ID')
        self.tree_clients.heading('DNI', text='DNI')
        self.tree_clients.heading('Nombre', text='Nombre')
        self.tree_clients.column('ID', width=50)
        self.tree_clients.column('DNI', width=100)
        self.tree_clients.column('Nombre', width=230)
        
        self.tree_clients.pack(side='left', fill='both', expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree_clients.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree_clients.configure(yscrollcommand=scrollbar.set)
        
        self.tree_clients.bind('<<TreeviewSelect>>', self.on_client_select)
        
        # Loan List
        loan_card = self.create_card_frame(left_frame)
        loan_card.pack(fill='both', expand=True)
        
        tk.Label(loan_card, text="2. Préstamos de Empeño Pagados", font=("Segoe UI", 12, "bold"), 
                bg=self.card_bg, fg=self.text_color).pack(anchor='w', padx=15, pady=(15, 10))
        
        loan_list_frame = tk.Frame(loan_card, bg=self.card_bg)
        loan_list_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        l_columns = ('ID', 'Monto', 'Fecha')
        self.tree_loans = ttk.Treeview(loan_list_frame, columns=l_columns, show='headings', height=8)
        self.tree_loans.heading('ID', text='ID')
        self.tree_loans.heading('Monto', text='Monto')
        self.tree_loans.heading('Fecha', text='Fecha Pago')
        self.tree_loans.column('ID', width=40)
        self.tree_loans.column('Monto', width=100)
        self.tree_loans.column('Fecha', width=120)
        
        self.tree_loans.pack(side='left', fill='both', expand=True)
        l_scrollbar = ttk.Scrollbar(loan_list_frame, orient="vertical", command=self.tree_loans.yview)
        l_scrollbar.pack(side='right', fill='y')
        self.tree_loans.configure(yscrollcommand=l_scrollbar.set)
        
        self.tree_loans.bind('<<TreeviewSelect>>', self.on_loan_select)
        
        # --- Right Column: Preview ---
        
        preview_card = self.create_card_frame(right_frame)
        preview_card.pack(fill='both', expand=True)
        
        tk.Label(preview_card, text="3. Vista Previa", font=("Segoe UI", 12, "bold"), 
                bg=self.card_bg, fg=self.text_color).pack(anchor='w', padx=15, pady=(15, 10))
        
        # Info Text
        info_frame = tk.Frame(preview_card, bg=self.card_bg)
        info_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        self.info_text = tk.Text(info_frame, height=22, font=("Consolas", 9), 
                                bg="#f5f5f5", relief='flat', padx=10, pady=10, wrap='word')
        self.info_text.pack(fill='both', expand=True)
        self.info_text.config(state='disabled')
        
        # Generate Button
        btn_frame = tk.Frame(preview_card, bg=self.card_bg)
        btn_frame.pack(fill='x', padx=15, pady=(0, 20))
        
        self.btn_generate = tk.Button(btn_frame, text="📄 GENERAR CONSTANCIA", 
                                      command=self.generate_certificate,
                                      bg='#4CAF50', fg='white', font=("Segoe UI", 11, "bold"), 
                                      relief='flat', cursor='hand2', state='disabled')
        self.btn_generate.pack(fill='x', ipady=10)

    def search_client(self, event=None):
        """Busca clientes que tienen préstamos de empeño pagados."""
        query = self.entry_search.get().strip()
        if not query:
            messagebox.showwarning("Advertencia", "Por favor ingrese un nombre o DNI.")
            return
            
        # Clear previous
        for item in self.tree_clients.get_children():
            self.tree_clients.delete(item)
        self.tree_loans.delete(*self.tree_loans.get_children())
        self.clear_preview()
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Only clients with paid pawn loans
        sql = """
            SELECT DISTINCT c.id, c.dni, c.first_name, c.last_name
            FROM clients c
            JOIN loans l ON c.id = l.client_id
            JOIN pawn_details pd ON l.id = pd.loan_id
            WHERE l.loan_type = 'pawn' AND l.status = 'paid'
              AND (c.first_name LIKE ? OR c.last_name LIKE ? OR c.dni LIKE ?)
            ORDER BY c.first_name, c.last_name
        """
        param = f"%{query}%"
        cursor.execute(sql, (param, param, param))
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            messagebox.showinfo("Sin Resultados", 
                              "No se encontraron clientes con préstamos de empeño pagados.")
            return
        
        for row in rows:
            self.tree_clients.insert('', 'end', values=(
                row['id'], 
                row['dni'], 
                f"{row['first_name']} {row['last_name']}"
            ))

    def on_client_select(self, event):
        """Carga los préstamos de empeño pagados del cliente seleccionado."""
        selection = self.tree_clients.selection()
        if not selection:
            return
            
        client_id = self.tree_clients.item(selection[0])['values'][0]
        self.load_paid_loans(client_id)
        self.clear_preview()

    def load_paid_loans(self, client_id):
        """Carga los préstamos de empeño pagados del cliente."""
        for item in self.tree_loans.get_children():
            self.tree_loans.delete(item)
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get paid pawn loans
        sql = """
            SELECT DISTINCT l.id, l.amount, l.end_date
            FROM loans l
            JOIN pawn_details pd ON l.id = pd.loan_id
            WHERE l.client_id = ? AND l.loan_type = 'pawn' AND l.status = 'paid'
            ORDER BY l.end_date DESC
        """
        cursor.execute(sql, (client_id,))
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            fecha = row['end_date'] if row['end_date'] else 'N/A'
            self.tree_loans.insert('', 'end', values=(
                row['id'], 
                f"S/ {row['amount']:.2f}",
                fecha
            ))
        
        # Auto-select if only one loan
        if len(rows) == 1:
            item_id = self.tree_loans.get_children()[0]
            self.tree_loans.selection_set(item_id)
            self.on_loan_select(None)

    def on_loan_select(self, event):
        """Carga los datos del préstamo seleccionado."""
        selection = self.tree_loans.selection()
        if not selection:
            self.btn_generate.config(state='disabled')
            return
            
        loan_id = self.tree_loans.item(selection[0])['values'][0]
        self.load_loan_data(loan_id)
        self.btn_generate.config(state='normal')

    def load_loan_data(self, loan_id):
        """Carga todos los datos necesarios para generar la constancia."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get Loan + Client
        cursor.execute("""
            SELECT l.*, c.first_name, c.last_name, c.dni, c.address
            FROM loans l
            JOIN clients c ON l.client_id = c.id
            WHERE l.id = ?
        """, (loan_id,))
        loan = cursor.fetchone()
        self.loan_data = loan
        
        if not loan:
            conn.close()
            return
        
        self.client_data = {
            'first_name': loan['first_name'],
            'last_name': loan['last_name'],
            'dni': loan['dni'],
            'address': loan['address']
        }
        
        # Get Pawn Items
        cursor.execute("SELECT * FROM pawn_details WHERE loan_id = ?", (loan_id,))
        self.pawn_items = cursor.fetchall()
        
        conn.close()
        
        # Prepare Preview
        preview = "═" * 50 + "\n"
        preview += "CONSTANCIA DE NO ADEUDO\n"
        preview += "PRÉSTAMO CON GARANTÍA PRENDARIA\n"
        preview += "═" * 50 + "\n\n"
        
        preview += f"Cliente: {self.client_data['first_name']} {self.client_data['last_name']}\n"
        preview += f"DNI: {self.client_data['dni']}\n"
        preview += f"Dirección: {self.client_data['address'] or 'No registrada'}\n\n"
        
        preview += f"Préstamo ID: {loan['id']}\n"
        preview += f"Monto: S/ {loan['amount']:.2f}\n"
        preview += f"Fecha de Pago: {loan['end_date'] or 'N/A'}\n\n"
        
        preview += "Garantía Prendaria:\n"
        for item in self.pawn_items:
            preview += f"  • {item['item_type']} {item['brand']}\n"
            preview += f"    Características: {item['characteristics']}\n"
            if item.get('description'):
                preview += f"    Descripción: {item['description']}\n"
            preview += f"    Valor: S/ {item['market_value']:.2f}\n"
        
        preview += "\n" + "─" * 50 + "\n"
        preview += "✅ El préstamo ha sido cancelado en su totalidad.\n"
        preview += "   La garantía prendaria será liberada.\n"
        
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, preview)
        self.info_text.config(state='disabled')

    def generate_certificate(self):
        """Genera la constancia de no adeudo en PDF."""
        if not self.loan_data or not self.client_data or not self.pawn_items:
            messagebox.showerror("Error", "Debe seleccionar un préstamo válido.")
            return
            
        try:
            # Convert amount to text (simple version)
            amount = self.loan_data['amount']
            amount_text = self.number_to_text(amount)
            
            # Create collateral description
            collateral_desc = ", ".join([f"{item['item_type']} {item['brand']}" for item in self.pawn_items])
            
            # Create collateral items list
            collateral_items = []
            for item in self.pawn_items:
                item_desc = f"{item['item_type']} {item['brand']} - {item['characteristics']}"
                if item.get('description'):
                    item_desc += f" - {item['description']}"
                collateral_items.append(item_desc)
            
            # Prepare Data
            data = {
                'client_name': f"{self.client_data['first_name']} {self.client_data['last_name']}",
                'client_dni': self.client_data['dni'],
                'loan_amount': amount,
                'loan_amount_text': amount_text,
                'collateral_description': collateral_desc,
                'collateral_items': collateral_items,
                'date': datetime.now()
            }
            
            # Generate PDF
            generator = PDFGenerator()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"constancia_no_adeudo_{self.loan_data['id']}_{timestamp}.pdf"
            filepath = os.path.join(generator.reports_dir, filename)
            
            path = generator.generate_no_debt_certificate(filepath, data)
            
            messagebox.showinfo("✅ Éxito", 
                              f"Constancia generada correctamente:\n\n{os.path.basename(path)}\n\nEl archivo se abrirá automáticamente.")
            os.startfile(path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar constancia:\n\n{str(e)}")
            import traceback
            traceback.print_exc()

    def number_to_text(self, number):
        """Convierte un número a texto (versión simple en español)."""
        # Esta es una versión simplificada, podrías mejorarla
        unidades = ["", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"]
        decenas = ["", "diez", "veinte", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]
        especiales = ["diez", "once", "doce", "trece", "catorce", "quince", "dieciséis", "diecisiete", "dieciocho", "diecinueve"]
        centenas = ["", "ciento", "doscientos", "trescientos", "cuatrocientos", "quinientos", "seiscientos", "setecientos", "ochocientos", "novecientos"]
        
        # Convertir a entero y decimales
        entero = int(number)
        decimales = int((number - entero) * 100)
        
        if entero < 10:
            texto = unidades[entero]
        elif entero < 20:
            texto = especiales[entero - 10]
        elif entero < 100:
            d = entero // 10
            u = entero % 10
            texto = decenas[d]
            if u > 0:
                if d == 2:
                    texto = "veinti" + unidades[u]
                else:
                    texto += " y " + unidades[u]
        elif entero < 1000:
            c = entero // 100
            resto = entero % 100
            if c == 1 and resto == 0:
                texto = "cien"
            else:
                texto = centenas[c]
                if resto > 0:
                    texto += " " + self.number_to_text(resto)
        elif entero < 1000000:
            miles = entero // 1000
            resto = entero % 1000
            if miles == 1:
                texto = "mil"
            else:
                texto = self.number_to_text(miles) + " mil"
            if resto > 0:
                texto += " " + self.number_to_text(resto)
        else:
            texto = str(entero)  # Fallback para números muy grandes
        
        # Agregar "soles"
        if decimales > 0:
            return f"{texto} con {decimales}/100 soles"
        else:
            return f"{texto} soles"

    def clear_preview(self):
        """Limpia la vista previa."""
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.config(state='disabled')
        self.btn_generate.config(state='disabled')
        self.loan_data = None
        self.client_data = None
        self.pawn_items = []
