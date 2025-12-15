
import tkinter as tk
from tkinter import ttk, messagebox
from ui.modern_window import ModernWindow
from datetime import datetime, date, timedelta
from utils.loan_calculator import obtener_info_prestamo
from tkcalendar import DateEntry
from utils.pdf_generator import PDFGenerator
import webbrowser
import os
import math

class CalculatorWindow(ModernWindow):
    def __init__(self, parent):
        super().__init__(parent, title="Calculadora de Préstamos y Estado", width=900, height=750)
        self.create_widgets()

    def create_widgets(self):
        # Header
        self.create_header("🧮 Calculadora y Verificador de Estado")
        
        # Content frame
        content = self.create_content_frame()
        
        # Two columns: Calculation inputs and Results
        main_container = tk.Frame(content, bg='white')
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left Panel: Input
        left_panel = tk.LabelFrame(main_container, text="Datos del Préstamo (Manual)", font=("Segoe UI", 11, "bold"), bg='white', padx=20, pady=20)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Right Panel: Results
        self.right_panel = tk.LabelFrame(main_container, text="Resultados / Estado Actual", font=("Segoe UI", 11, "bold"), bg='white', padx=20, pady=20)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # --- INPUTS ---
        
        # Loan Type
        tk.Label(left_panel, text="Tipo de Préstamo:", bg='white', font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.combo_loan_type = ttk.Combobox(left_panel, values=["Rapidiario", "Casa de Empeño", "Préstamo Bancario"], state="readonly", font=("Segoe UI", 11))
        self.combo_loan_type.current(0)
        self.combo_loan_type.bind("<<ComboboxSelected>>", self.on_loan_type_change)
        self.combo_loan_type.pack(fill=tk.X, pady=(0, 15), ipady=5)
        
        # Amount
        tk.Label(left_panel, text="Monto Prestado (S/):", bg='white', font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.entry_amount = ttk.Entry(left_panel, font=("Segoe UI", 11))
        self.entry_amount.pack(fill=tk.X, pady=(0, 15), ipady=5)
        
        # Interest Rate
        tk.Label(left_panel, text="Tasa de Interés (%):", bg='white', font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.entry_interest = ttk.Entry(left_panel, font=("Segoe UI", 11))
        self.entry_interest.pack(fill=tk.X, pady=(0, 15), ipady=5)
        
        # Start Date
        tk.Label(left_panel, text="Fecha del Préstamo:", bg='white', font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.date_start = DateEntry(left_panel, width=20, background='darkblue', foreground='white', borderwidth=2, font=("Segoe UI", 10))
        self.date_start.pack(fill=tk.X, pady=(0, 15), ipady=5)
        
        # DYNAMIC INPUTS FRAME
        self.dynamic_frame = tk.Frame(left_panel, bg='white')
        self.dynamic_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Action Buttons
        btn_frame = tk.Frame(left_panel, bg='white')
        btn_frame.pack(fill=tk.X, pady=20)
        
        tk.Button(btn_frame, text="🔄 CALCULAR ESTADO", command=self.calculate_status,
                 bg='#2196F3', fg='white', font=("Segoe UI", 11, "bold"), relief='flat', padx=20, pady=10).pack(fill=tk.X)

        # Initialize
        self.on_loan_type_change(None)

    def on_loan_type_change(self, event):
        # Clear dynamic inputs
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()
            
        loan_type = self.combo_loan_type.get()
        
        if loan_type == "Rapidiario":
            # Rapidiario: Simulator Only
            tk.Label(self.dynamic_frame, text="* El plazo es fijo a 30 días.", bg='white', fg='#666', font=("Segoe UI", 9)).pack(anchor="w", pady=(5, 0))

        elif loan_type == "Casa de Empeño":
            # Empeño: Simulator Only
            tk.Label(self.dynamic_frame, text="* Se calcula interés mensual desde la fecha inicio.", bg='white', fg='#666', font=("Segoe UI", 9)).pack(anchor="w", pady=(5, 0))
            
        elif loan_type == "Préstamo Bancario":
             # Bancario inputs (simpler, maybe just months)
            tk.Label(self.dynamic_frame, text="Plazo (Meses):", bg='white', font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
            self.entry_months = ttk.Entry(self.dynamic_frame, font=("Segoe UI", 11))
            self.entry_months.insert(0, "12")
            self.entry_months.pack(fill=tk.X, ipady=5)

    def calculate_status(self):
        # Clear previous results
        for widget in self.right_panel.winfo_children():
            widget.destroy()
            
        try:
            loan_type = self.combo_loan_type.get()
            amount = float(self.entry_amount.get())
            rate = float(self.entry_interest.get())
            start_date = self.date_start.get_date()
            today = date.today()
            
            def add_result_row(label, value, color='black', font_weight='normal'):
                row = tk.Frame(self.right_panel, bg='white')
                row.pack(fill=tk.X, pady=5)
                tk.Label(row, text=label, bg='white', fg='#555', font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
                tk.Label(row, text=value, bg='white', fg=color, font=("Segoe UI", 11, font_weight)).pack(side=tk.RIGHT)
                return row

            tk.Label(self.right_panel, text=f"Resultados: {loan_type}", bg='white', font=("Segoe UI", 13, "bold"), fg='#2196F3').pack(pady=(0, 20))
            
            if loan_type == "Rapidiario":
                info = obtener_info_prestamo('rapidiario', amount, rate, start_date)
                
                total_debt = info['total_pagar']
                interest_total = info['total_interes']
                due_date = info['fecha_vencimiento']
                working_days = info['dias_laborables']
                first_quota = info['cuotas'][0][2] if info['cuotas'] else 0
                
                add_result_row("Monto Prestado:", f"S/ {amount:.2f}")
                add_result_row("Interés Total:", f"S/ {interest_total:.2f}")
                add_result_row("Días de Pago:", f"{working_days} días (Lun-Sáb)")
                
                tk.Frame(self.right_panel, bg='#eee', height=2).pack(fill=tk.X, pady=10)
                
                add_result_row("TOTAL A DEVOLVER:", f"S/ {total_debt:.2f}", color='#2196F3', font_weight='bold')
                add_result_row("CUOTA DIARIA:", f"S/ {first_quota:.2f}", color='#4CAF50', font_weight='bold')
                
                tk.Frame(self.right_panel, bg='#eee', height=1).pack(fill=tk.X, pady=10)
                
                add_result_row("Fecha de Préstamo:", start_date.strftime("%d/%m/%Y"))
                add_result_row("Fecha de Vencimiento:", due_date.strftime("%d/%m/%Y"))
                
                # Button to Print Schedule
                tk.Button(self.right_panel, text="🖨️ IMPRIMIR CRONOGRAMA", 
                         command=lambda: self.print_schedule(info['cuotas'], amount, total_debt, "Rapidiario", start_date, rate),
                         bg='#607D8B', fg='white', relief='flat', font=("Segoe UI", 9, "bold")).pack(pady=20, fill=tk.X)

            elif loan_type == "Casa de Empeño":
                # Logic: Interest is monthly.
                if today < start_date:
                     months_to_charge = 0
                else:
                    diff = (today.year - start_date.year) * 12 + today.month - start_date.month
                    if today.day > start_date.day:
                        diff += 1
                    months_to_charge = max(1, diff)
                    
                interest_per_month = amount * (rate / 100)
                total_interest_generated = months_to_charge * interest_per_month
                
                # Assume 0 paid
                interest_debt = total_interest_generated
                capital_debt = amount
                total_due = capital_debt + interest_debt
                
                # Next payment date
                next_due_month = today.month
                next_due_year = today.year
                if today.day >= start_date.day:
                    next_due_month += 1
                
                if next_due_month > 12:
                    next_due_month = 1
                    next_due_year += 1
                    
                try:
                    next_due_date = date(next_due_year, next_due_month, start_date.day)
                except ValueError:
                    import calendar
                    last_day = calendar.monthrange(next_due_year, next_due_month)[1]
                    next_due_date = date(next_due_year, next_due_month, last_day)

                add_result_row("Monto Original:", f"S/ {amount:.2f}")
                add_result_row("Interés Mensual:", f"S/ {interest_per_month:.2f}")
                
                tk.Frame(self.right_panel, bg='#eee', height=2).pack(fill=tk.X, pady=10)

                add_result_row("Meses Transcurridos:", f"{months_to_charge}")
                add_result_row("Interés Acumulado:", f"S/ {total_interest_generated:.2f}")
                
                tk.Frame(self.right_panel, bg='#eee', height=1).pack(fill=tk.X, pady=10)
                
                add_result_row("DEUDA TOTAL HOY:", f"S/ {total_due:.2f}", color='#F44336', font_weight='bold')
                
                tk.Frame(self.right_panel, bg='#eee', height=2).pack(fill=tk.X, pady=10)
                add_result_row("Próximo Vencimiento:", next_due_date.strftime("%d/%m/%Y"))
                
                # Construct a logical schedule for printing: 1 item "Pago Total Hoy"
                # Showing the Next Due Date is better for "Cronograma Proyectado"
                
                cuotas_empeno = [
                    (1, next_due_date, total_due) # Payment due on the next expiration date
                ]
                
                tk.Button(self.right_panel, text="🖨️ IMPRIMIR LIQUIDACIÓN (PDF)", 
                         command=lambda: self.print_schedule(cuotas_empeno, amount, total_due, "Casa de Empeño", start_date, rate),
                         bg='#607D8B', fg='white', relief='flat', font=("Segoe UI", 9, "bold")).pack(pady=20, fill=tk.X)

            elif loan_type == "Préstamo Bancario":
                months = int(self.entry_months.get())
                
                info = obtener_info_prestamo('bancario', amount, rate, start_date, meses=months)
                
                total_debt = info['total_pagar']
                total_interest = info['total_interes']
                monthly_quota = info['cuotas'][0][2] if info['cuotas'] else 0
                
                add_result_row("Monto Prestado:", f"S/ {amount:.2f}")
                add_result_row("Plazo:", f"{months} meses")
                add_result_row("Tasa Mensual:", f"{rate}%")
                
                tk.Frame(self.right_panel, bg='#eee', height=2).pack(fill=tk.X, pady=10)
                
                add_result_row("Interés Total:", f"S/ {total_interest:.2f}")
                add_result_row("TOTAL A PAGAR:", f"S/ {total_debt:.2f}", color='#2196F3', font_weight='bold')
                
                tk.Frame(self.right_panel, bg='#eee', height=1).pack(fill=tk.X, pady=10)
                
                add_result_row("CUOTA MENSUAL:", f"S/ {monthly_quota:.2f}", color='#4CAF50', font_weight='bold')
                
                # Button to Print Schedule
                tk.Button(self.right_panel, text="🖨️ IMPRIMIR CRONOGRAMA", 
                         command=lambda: self.print_schedule(info['cuotas'], amount, total_debt, "Préstamo Bancario", start_date, rate),
                         bg='#607D8B', fg='white', relief='flat', font=("Segoe UI", 9, "bold")).pack(pady=20, fill=tk.X)

        except ValueError:
            messagebox.showerror("Error", "Por favor verifique que todos los campos numéricos sean correctos.")

    def print_schedule(self, cuotas, amount, total, type_name, start_date, rate):
        try:
            generator = PDFGenerator()
            
            # Prepare data for generate_simulation_report
            simulation_data = {
                'monto': amount,
                'total_pagar': total,
                'total_interes': total - amount,
                'tipo': type_name,
                'tasa': rate,
                'fecha_inicio': start_date
            }
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cronograma_simulado_{timestamp}.pdf"
            filepath = os.path.join(generator.reports_dir, filename)
            
            # Use existing method
            path = generator.generate_simulation_report(filepath, simulation_data, cuotas)
            os.startfile(path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar cronograma: {e}")
