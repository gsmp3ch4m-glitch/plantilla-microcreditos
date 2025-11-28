import tkinter as tk
from tkinter import ttk, messagebox

class CalculatorWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Calculadora de Préstamos")
        self.geometry("400x500")
        
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Monto del Préstamo:").pack(pady=(20, 5))
        self.entry_amount = tk.Entry(self)
        self.entry_amount.pack()
        
        tk.Label(self, text="Tasa de Interés (%):").pack(pady=(10, 5))
        self.entry_interest = tk.Entry(self)
        self.entry_interest.pack()
        
        tk.Label(self, text="Periodo (días/meses):").pack(pady=(10, 5))
        self.entry_period = tk.Entry(self)
        self.entry_period.pack()
        
        tk.Label(self, text="Tipo de Interés:").pack(pady=(10, 5))
        self.combo_type = ttk.Combobox(self, values=["Simple", "Compuesto"])
        self.combo_type.current(0)
        self.combo_type.pack()
        
        tk.Button(self, text="Calcular", command=self.calculate).pack(pady=20)
        
        self.result_frame = tk.LabelFrame(self, text="Resultados", padx=10, pady=10)
        self.result_frame.pack(fill=tk.X, padx=20)
        
        self.lbl_total_interest = tk.Label(self.result_frame, text="Interés Total: S/ 0.00")
        self.lbl_total_interest.pack(anchor="w")
        
        self.lbl_total_payment = tk.Label(self.result_frame, text="Total a Pagar: S/ 0.00")
        self.lbl_total_payment.pack(anchor="w")

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
