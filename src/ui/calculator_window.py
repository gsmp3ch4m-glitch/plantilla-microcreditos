
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
            # Rapidiario: Ask for total paid so far
            tk.Label(self.dynamic_frame, text="Monto Total ya Pagado (S/):", bg='white', font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
            self.entry_paid = ttk.Entry(self.dynamic_frame, font=("Segoe UI", 11))
            self.entry_paid.insert(0, "0")
            self.entry_paid.pack(fill=tk.X, ipady=5)
            
            tk.Label(self.dynamic_frame, text="* El plazo es fijo a 30 días.", bg='white', fg='#666', font=("Segoe UI", 9)).pack(anchor="w", pady=(5, 0))

        elif loan_type == "Casa de Empeño":
            # Empeño: Ask for how many times interest was paid
            tk.Label(self.dynamic_frame, text="Veces que ha pagado interés:", bg='white', font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
            self.entry_interest_times = ttk.Entry(self.dynamic_frame, font=("Segoe UI", 11))
            self.entry_interest_times.insert(0, "0")
            self.entry_interest_times.pack(fill=tk.X, ipady=5)
            
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
                paid = float(self.entry_paid.get())
                
                # Logic:
                # 1. Total Debt = Amount + (Amount * Rate / 100)
                interest_total = amount * (rate / 100)
                total_debt_original = amount + interest_total
                
                # 2. Balance
                balance = total_debt_original - paid
                
                # 3. Capital vs Interest Split
                # Assuming simple priority: Pay Interest first? Or Proportional?
                # User asked: "separando el capital e interes por pagar"
                # Usually: Interest is prioritized.
                interest_pending = max(0, interest_total - paid) # If paid < interest, rest is pending interest
                # If paid > interest, interest is covered, rest goes to capital
                capital_paid = max(0, paid - interest_total)
                capital_pending = amount - capital_paid
                
                # 4. Dates
                due_date = start_date + timedelta(days=30)
                days_remaining = (due_date - today).days
                
                add_result_row("Monto Prestado:", f"S/ {amount:.2f}")
                add_result_row("Interés Total Generado:", f"S/ {interest_total:.2f}")
                add_result_row("Deuda Total Inicial:", f"S/ {total_debt_original:.2f}", font_weight='bold')
                
                tk.Frame(self.right_panel, bg='#eee', height=2).pack(fill=tk.X, pady=10)
                
                add_result_row("Total Pagado:", f"S/ {paid:.2f}", color='#4CAF50')
                add_result_row("Saldo Pendiente:", f"S/ {balance:.2f}", color='#F44336', font_weight='bold')
                
                tk.Frame(self.right_panel, bg='#eee', height=1).pack(fill=tk.X, pady=10)
                
                tk.Label(self.right_panel, text="Desglose del Saldo:", bg='white', fg='#888', font=("Segoe UI", 9, "bold")).pack(anchor='w')
                add_result_row("Interés por Pagar:", f"S/ {interest_pending:.2f}", color='#FF9800')
                add_result_row("Capital por Pagar:", f"S/ {capital_pending:.2f}", color='#FF9800')
                
                tk.Frame(self.right_panel, bg='#eee', height=2).pack(fill=tk.X, pady=10)
                
                add_result_row("Fecha Pago (30 días):", due_date.strftime("%d/%m/%Y"))
                
                if days_remaining > 0:
                    add_result_row("Días Faltantes:", f"{days_remaining} días", color='#2196F3')
                elif days_remaining == 0:
                    add_result_row("Estado:", "Vence Hoy", color='#FF9800', font_weight='bold')
                else:
                    add_result_row("Estado:", f"Vencido hace {abs(days_remaining)} días", color='#F44336', font_weight='bold')

            elif loan_type == "Casa de Empeño":
                times_paid = int(self.entry_interest_times.get())
                
                # Logic:
                # Interest is monthly.
                # Months elapsed = ceil((Today - Start) / 30) ? Or simply calendar months?
                # User says: "si se presta un 10 de julio paga el 10 de agosto".
                # Calculate full months elapsed since start.
                
                # Exact calculation of months elapsed
                months_elapsed = (today.year - start_date.year) * 12 + today.month - start_date.month
                
                # If day of month is passed, add 1 month?
                # E.g. Start Jan 10. Today Feb 11. That's 1 month fully passed, entering 2nd.
                # User wants "sumar hasta la fecha cuanto ya debe en intereses".
                # Usually this means accrued interest.
                # Let's count full periods passed + current running period.
                
                # Simple logic: If today > start_date, at least 1 month interest is running/due eventually.
                # But for accrued debt:
                # If we are in month 1 (day 1 to 29), owe 1 month interest? Or daily?
                # Empeño usually is "Mes cumplido" or "Mes adelantado"?
                # Let's assume proportional or full month logic. "sumar hasta la fecha cuanto ya debe".
                
                # Let's use exact float months for precision or ceiling for "periods started".
                # Standard pawn shop: 1 day into new month = full month interest.
                # Let's calculate months started.
                
                if today < start_date:
                     months_to_charge = 0
                else:
                    # Calculate exact difference in months
                    diff = (today.year - start_date.year) * 12 + today.month - start_date.month
                    if today.day > start_date.day:
                        diff += 1
                    # If today is same day, it's exactly that many months.
                    # But usually if you pay ON the day, you pay for the past month.
                    # If you pay day after, new month starts.
                    months_to_charge = max(1, diff) # At least 1 month if started
                    
                    # Wait, if I borrow today, do I owe interest immediately? Usually yes (deducted) or at end.
                    # Assuming payment at end.
                    
                interest_per_month = amount * (rate / 100)
                total_interest_generated = months_to_charge * interest_per_month
                
                total_interest_paid = times_paid * interest_per_month
                interest_debt = total_interest_generated - total_interest_paid
                
                # Capital is usually constant until end
                capital_debt = amount 
                
                # Next payment date
                # Start: 10 July.
                # If today is 20 July. Next pay: 10 Aug.
                # If today is 15 Aug. Next pay: 10 Sept.
                # Logic: Find next day matching start_date.day
                
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
                    # Handle Feb 30 etc
                    import calendar
                    last_day = calendar.monthrange(next_due_year, next_due_month)[1]
                    next_due_date = date(next_due_year, next_due_month, last_day)

                add_result_row("Monto Original:", f"S/ {amount:.2f}")
                add_result_row("Interés Mensual:", f"S/ {interest_per_month:.2f}")
                
                tk.Frame(self.right_panel, bg='#eee', height=2).pack(fill=tk.X, pady=10)

                add_result_row("Meses Transcurridos:", f"{months_to_charge}")
                add_result_row("Interés Total Generado:", f"S/ {total_interest_generated:.2f}")
                add_result_row("Interés Ya Pagado:", f"S/ {total_interest_paid:.2f} ({times_paid} veces)", color='#4CAF50')
                
                tk.Frame(self.right_panel, bg='#eee', height=1).pack(fill=tk.X, pady=10)
                
                add_result_row("DEUDA INTERÉS ACTUAL:", f"S/ {interest_debt:.2f}", color='#F44336', font_weight='bold')
                add_result_row("DEUDA CAPITAL:", f"S/ {capital_debt:.2f}", font_weight='bold')
                
                total_to_liquidate = capital_debt + interest_debt
                add_result_row("TOTAL PARA RETIRAR:", f"S/ {total_to_liquidate:.2f}", color='#2196F3', font_weight='bold')
                
                tk.Frame(self.right_panel, bg='#eee', height=2).pack(fill=tk.X, pady=10)
                add_result_row("Próximo Vencimiento:", next_due_date.strftime("%d/%m/%Y"))

            elif loan_type == "Préstamo Bancario":
                # Basic info
                pass

        except ValueError:
            messagebox.showerror("Error", "Por favor verifique que todos los campos numéricos sean correctos.")

