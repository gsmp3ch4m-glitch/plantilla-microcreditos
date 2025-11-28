import tkinter as tk
from tkinter import ttk, messagebox
from ui.modern_window import ModernWindow

class CalculatorWindow(ModernWindow):
    def __init__(self, parent):
        super().__init__(parent, title="Calculadora de Préstamos", width=500, height=600)
        self.create_widgets()

    def create_widgets(self):
        # Header
        self.create_header("🧮 Calculadora de Préstamos")
        
        # Content frame
        content = self.create_content_frame()
        
        # Card for calculator
        card = self.create_card_frame(content)
        card.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Form inside card
        form_frame = tk.Frame(card, bg=self.card_bg)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Monto
        tk.Label(form_frame, text="Monto del Préstamo:", bg=self.card_bg, fg=self.text_color, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.entry_amount = ttk.Entry(form_frame, font=("Segoe UI", 11))
        self.entry_amount.pack(fill=tk.X, ipady=8, pady=(0, 15))
        
        # Tasa
        tk.Label(form_frame, text="Tasa de Interés (%):", bg=self.card_bg, fg=self.text_color, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.entry_interest = ttk.Entry(form_frame, font=("Segoe UI", 11))
        self.entry_interest.pack(fill=tk.X, ipady=8, pady=(0, 15))
        
        # Periodo
        tk.Label(form_frame, text="Periodo (días/meses):", bg=self.card_bg, fg=self.text_color, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.entry_period = ttk.Entry(form_frame, font=("Segoe UI", 11))
        self.entry_period.pack(fill=tk.X, ipady=8, pady=(0, 15))
        
        # Tipo
        tk.Label(form_frame, text="Tipo de Interés:", bg=self.card_bg, fg=self.text_color, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.combo_type = ttk.Combobox(form_frame, values=["Simple", "Compuesto"], font=("Segoe UI", 11))
        self.combo_type.current(0)
        self.combo_type.pack(fill=tk.X, ipady=8, pady=(0, 20))
        
        # Button
        calc_btn = tk.Button(form_frame, text="CALCULAR", command=self.calculate,
                            bg=self.theme_colors['gradient_end'], fg='white',
                            font=("Segoe UI", 11, "bold"), relief='flat', cursor='hand2')
        calc_btn.pack(fill=tk.X, ipady=12, pady=(0, 20))
        
        # Results
        result_card = tk.Frame(form_frame, bg=self.theme_colors['gradient_start'], relief='flat', bd=0)
        result_card.pack(fill=tk.X, pady=(10, 0))
        
        result_inner = tk.Frame(result_card, bg=self.theme_colors['gradient_start'])
        result_inner.pack(padx=15, pady=15)
        
        tk.Label(result_inner, text="Resultados", bg=self.theme_colors['gradient_start'], 
                fg=self.text_color, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))
        
        self.lbl_total_interest = tk.Label(result_inner, text="Interés Total: S/ 0.00",
                                          bg=self.theme_colors['gradient_start'], fg=self.text_color,
                                          font=("Segoe UI", 11))
        self.lbl_total_interest.pack(anchor="w", pady=3)
        
        self.lbl_total_payment = tk.Label(result_inner, text="Total a Pagar: S/ 0.00",
                                         bg=self.theme_colors['gradient_start'], fg=self.text_color,
                                         font=("Segoe UI", 11, "bold"))
        self.lbl_total_payment.pack(anchor="w", pady=3)

    def calculate(self):
        try:
            amount = float(self.entry_amount.get())
            rate = float(self.entry_interest.get()) / 100
            period = float(self.entry_period.get())
            type_int = self.combo_type.get()
            
            if type_int == "Simple":
                interest = amount * rate * period
            else:
                interest = amount * ((1 + rate) ** period - 1)
                
            total = amount + interest
            
            self.lbl_total_interest.config(text=f"Interés Total: S/ {interest:.2f}")
            self.lbl_total_payment.config(text=f"Total a Pagar: S/ {total:.2f}")
            
        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese valores numéricos válidos")
