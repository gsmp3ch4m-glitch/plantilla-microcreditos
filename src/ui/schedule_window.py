import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from database import get_db_connection
from ui.modern_window import ModernWindow
from utils.pdf_generator import generate_payment_schedule
from utils.image_generator import generate_schedule_image

class ScheduleWindow(ModernWindow):
    def __init__(self, parent, loan_id):
        super().__init__(parent, title=f"Cronograma Préstamo #{loan_id}", width=900, height=600)
        self.loan_id = loan_id
        self.pawn_details = []
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        # Header
        self.create_header("📅 Cronograma de Pagos")
        
        # Content
        content = self.create_content_frame()
        
        # Info Frame
        self.info_frame = tk.Frame(content, bg='white', pady=10)
        self.info_frame.pack(fill=tk.X, padx=20)
        
        # Buttons Frame (MOVED TO TOP)
        btn_frame = tk.Frame(content, bg='white', pady=15)
        btn_frame.pack(fill=tk.X, padx=20)
        
        tk.Button(btn_frame, text="🖨️ Imprimir", command=self.print_schedule,
                 bg='#2196F3', fg='white', font=("Segoe UI", 11, "bold"),
                 relief='flat', cursor='hand2', padx=15, pady=10).pack(side=tk.LEFT, padx=5)
                 
        tk.Button(btn_frame, text="💾 Guardar PDF", command=self.save_pdf,
                 bg='#4CAF50', fg='white', font=("Segoe UI", 11, "bold"),
                 relief='flat', cursor='hand2', padx=15, pady=10).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="📤 Compartir", command=self.share_image,
                 bg='#FF9800', fg='white', font=("Segoe UI", 11, "bold"),
                 relief='flat', cursor='hand2', padx=15, pady=10).pack(side=tk.LEFT, padx=5)
                 
        tk.Button(btn_frame, text="Cerrar", command=self.destroy,
                 bg='#757575', fg='white', font=("Segoe UI", 11),
                 relief='flat', cursor='hand2', padx=15, pady=10).pack(side=tk.RIGHT, padx=5)
        
        # Treeview Frame
        tree_frame = tk.Frame(content, bg='white')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        columns = ("num", "due_date", "amount", "status", "pay_date")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        self.tree.heading("num", text="N°")
        self.tree.heading("due_date", text="Vencimiento")
        self.tree.heading("amount", text="Monto (S/)")
        self.tree.heading("status", text="Estado")
        self.tree.heading("pay_date", text="Fecha Pago")
        
        self.tree.column("num", width=50, anchor='center')
        self.tree.column("due_date", width=120, anchor='center')
        self.tree.column("amount", width=120, anchor='e')
        self.tree.column("status", width=100, anchor='center')
        self.tree.column("pay_date", width=120, anchor='center')
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def load_data(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get Loan & Client Info
        cursor.execute("""
            SELECT l.*, c.first_name, c.last_name, c.dni 
            FROM loans l 
            JOIN clients c ON l.client_id = c.id 
            WHERE l.id = ?
        """, (self.loan_id,))
        self.loan_data = cursor.fetchone()
        
        # Get Installments
        cursor.execute("SELECT * FROM installments WHERE loan_id = ? ORDER BY number", (self.loan_id,))
        self.installments = cursor.fetchall()
        
        # Get Pawn Details
        cursor.execute("SELECT * FROM pawn_details WHERE loan_id = ?", (self.loan_id,))
        self.pawn_details = cursor.fetchall()
        
        conn.close()
        
        if not self.loan_data:
            messagebox.showerror("Error", "No se encontró el préstamo")
            self.destroy()
            return
            
        # Display Info
        info_text = f"Cliente: {self.loan_data['first_name']} {self.loan_data['last_name']} | DNI: {self.loan_data['dni']}\n"
        info_text += f"Préstamo: {self.loan_data['loan_type'].capitalize()} | Monto: S/ {self.loan_data['amount']:.2f}"
        
        if self.pawn_details:
            info_text += f"\n\nGarantías ({len(self.pawn_details)}):"
            for item in self.pawn_details:
                info_text += f"\n• {item['item_type']} {item['brand']} - {item['characteristics']}"
        
        tk.Label(self.info_frame, text=info_text, font=("Segoe UI", 10), 
                bg='white', justify=tk.LEFT).pack(anchor='w')
        
        # Populate Tree
        if not self.installments:
            tk.Label(self.tree, text="No hay cuotas registradas para este préstamo.\nPosiblemente fue creado antes de la actualización.", 
                    font=("Segoe UI", 10, "italic"), fg="red", bg='white').place(relx=0.5, rely=0.5, anchor="center")
        
        for inst in self.installments:
            status_map = {'pending': 'Pendiente', 'paid': 'Pagado', 'partial': 'Parcial', 'overdue': 'Vencido'}
            status = status_map.get(inst['status'], inst['status'])
            
            self.tree.insert("", tk.END, values=(
                inst['number'],
                inst['due_date'],
                f"S/ {inst['amount']:.2f}",
                status,
                inst['payment_date'] or '-'
            ))

    def print_schedule(self):
        """Generate PDF and open it"""
        try:
            filename = f"cronograma_{self.loan_id}.pdf"
            filepath = os.path.abspath(filename)
            
            generate_payment_schedule(filepath, self.loan_data, self.loan_data, self.installments, self.pawn_details)
            
            os.startfile(filepath)
        except Exception as e:
            messagebox.showerror("Error", f"Error al imprimir: {e}")

    def save_pdf(self):
        """Generate PDF and save to specific location"""
        filename = f"cronograma_{self.loan_data['first_name']}_{self.loan_id}.pdf"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf")],
            initialfile=filename
        )
        
        if filepath:
            try:
                generate_payment_schedule(filepath, self.loan_data, self.loan_data, self.installments, self.pawn_details)
                messagebox.showinfo("Éxito", "Cronograma guardado correctamente")
                os.startfile(filepath)
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}")

    def share_image(self):
        """Generate Image, save to Downloads, and copy to clipboard"""
        try:
            from pathlib import Path
            from PIL import Image
            import io
            
            # Get Downloads folder
            downloads_path = str(Path.home() / "Downloads")
            filename = f"cronograma_{self.loan_data['first_name']}_{self.loan_id}.png"
            filepath = os.path.join(downloads_path, filename)
            
            # Generate image
            generate_schedule_image(filepath, self.loan_data, self.loan_data, self.installments, self.pawn_details)
            
            # Copy image to clipboard
            try:
                import win32clipboard
                from PIL import Image
                
                image = Image.open(filepath)
                output = io.BytesIO()
                image.convert('RGB').save(output, 'BMP')
                data = output.getvalue()[14:]  # Remove BMP header
                output.close()
                
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                win32clipboard.CloseClipboard()
                
                messagebox.showinfo("✅ Listo para Compartir", 
                                  f"Imagen guardada en:\n{filepath}\n\n"
                                  "✅ Copiada al portapapeles\n"
                                  "Ahora puedes ir a WhatsApp y presionar Ctrl+V para pegarla")
            except ImportError:
                # If win32clipboard not available, just save the file
                messagebox.showinfo("✅ Imagen Guardada", 
                                  f"Imagen guardada en:\n{filepath}\n\n"
                                  "Puedes encontrarla en tu carpeta de Descargas")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar imagen: {e}")
