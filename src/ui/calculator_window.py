import tkinter as tk
from tkinter import ttk, messagebox
from ui.modern_window import ModernWindow
from datetime import datetime, date
from utils.loan_calculator import obtener_info_prestamo
from tkcalendar import DateEntry
from utils.pdf_generator import PDFGenerator
import webbrowser
import os
import pyperclip

class CalculatorWindow(ModernWindow):
    def __init__(self, parent):
        super().__init__(parent, title="Calculadora de Préstamos", width=600, height=750)
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
        
        # Tipo de Préstamo (PRIMERO)
        tk.Label(form_frame, text="Tipo de Préstamo:", bg=self.card_bg, fg=self.text_color, 
                font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.combo_loan_type = ttk.Combobox(form_frame, 
                                            values=["Rapidiario", "Casa de Empeño", "Préstamo Bancario"], 
                                            font=("Segoe UI", 11), state="readonly")
        self.combo_loan_type.current(0)
        self.combo_loan_type.bind("<<ComboboxSelected>>", self.on_loan_type_change)
        self.combo_loan_type.pack(fill=tk.X, ipady=8, pady=(0, 15))
        
        # Monto
        tk.Label(form_frame, text="Monto del Préstamo:", bg=self.card_bg, fg=self.text_color, 
                font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.entry_amount = ttk.Entry(form_frame, font=("Segoe UI", 11))
        self.entry_amount.pack(fill=tk.X, ipady=8, pady=(0, 15))
        
        # Tasa de Interés
        tk.Label(form_frame, text="Tasa de Interés (%):", bg=self.card_bg, fg=self.text_color, 
                font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.entry_interest = ttk.Entry(form_frame, font=("Segoe UI", 11))
        # Default empty as requested
        self.entry_interest.pack(fill=tk.X, ipady=8, pady=(0, 15))
        
        # Fecha de Inicio (para simulación)
        tk.Label(form_frame, text="Fecha de Inicio:", bg=self.card_bg, fg=self.text_color, 
                font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        self.date_start = DateEntry(form_frame, width=20, background='darkblue', 
                                    foreground='white', borderwidth=2, 
                                    font=("Segoe UI", 10))
        self.date_start.pack(fill=tk.X, ipady=5, pady=(0, 15))
        
        # Frame dinámico para campos específicos
        self.dynamic_frame = tk.Frame(form_frame, bg=self.card_bg)
        self.dynamic_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Inicializar campos dinámicos
        self.on_loan_type_change(None)
        
        # Button - GREEN
        calc_btn = tk.Button(form_frame, text="VER CRONOGRAMA", command=self.calculate,
                            bg='#4CAF50', fg='white',
                            font=("Segoe UI", 11, "bold"), relief='flat', cursor='hand2')
        calc_btn.pack(fill=tk.X, ipady=12, pady=(0, 20))
        
        # Hover effect for button
        def on_enter(e):
            calc_btn.config(bg='#45a049')
        def on_leave(e):
            calc_btn.config(bg='#4CAF50')
        
        calc_btn.bind('<Enter>', on_enter)
        calc_btn.bind('<Leave>', on_leave)
        
        # Results Frame (summary only)
        self.result_frame = tk.Frame(form_frame, bg=self.theme_colors['gradient_start'], relief='flat', bd=0)
        self.result_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

    def on_loan_type_change(self, event):
        """Actualiza los campos dinámicos según el tipo de préstamo"""
        # Limpiar frame dinámico
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()
        
        loan_type = self.combo_loan_type.get()
        
        if loan_type == "Rapidiario":
            # Campo de frecuencia
            tk.Label(self.dynamic_frame, text="Frecuencia de Pago:", bg=self.card_bg, 
                    fg=self.text_color, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
            self.combo_frequency = ttk.Combobox(self.dynamic_frame, 
                                               values=["Diario", "Semanal"], 
                                               font=("Segoe UI", 11), state="readonly")
            self.combo_frequency.current(0)
            self.combo_frequency.pack(fill=tk.X, ipady=8)
            
            # Información
            info_text = "📌 Préstamo a 30 días (excluyendo domingos)\n   25-26 días laborables según día de inicio"
            tk.Label(self.dynamic_frame, text=info_text, bg=self.card_bg, 
                    fg="#666", font=("Segoe UI", 9), justify=tk.LEFT).pack(anchor="w", pady=(10, 0))
        
        elif loan_type == "Casa de Empeño":
            # Información
            info_text = "📌 Préstamo a 1 mes calendario\n   Pago: mismo día del mes siguiente"
            tk.Label(self.dynamic_frame, text=info_text, bg=self.card_bg, 
                    fg="#666", font=("Segoe UI", 9), justify=tk.LEFT).pack(anchor="w", pady=(5, 0))
        
        elif loan_type == "Préstamo Bancario":
            # Campo de meses
            tk.Label(self.dynamic_frame, text="Número de Meses:", bg=self.card_bg, 
                    fg=self.text_color, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
            self.entry_months = ttk.Entry(self.dynamic_frame, font=("Segoe UI", 11))
            self.entry_months.insert(0, "3")
            self.entry_months.pack(fill=tk.X, ipady=8)
            
            # Información
            info_text = "📌 Cuotas mensuales (capital + interés)\n   Interés se aplica mensualmente"
            tk.Label(self.dynamic_frame, text=info_text, bg=self.card_bg, 
                    fg="#666", font=("Segoe UI", 9), justify=tk.LEFT).pack(anchor="w", pady=(10, 0))

    def calculate(self):
        """Calcula el préstamo y muestra el cronograma en una nueva ventana"""
        try:
            # Obtener valores
            monto = float(self.entry_amount.get())
            tasa = float(self.entry_interest.get())
            loan_type_display = self.combo_loan_type.get()
            
            # Mapear tipo de préstamo
            loan_type_map = {
                "Rapidiario": "rapidiario",
                "Casa de Empeño": "empeno",
                "Préstamo Bancario": "bancario"
            }
            loan_type = loan_type_map[loan_type_display]
            
            # Fecha de inicio (desde el selector de fecha)
            fecha_inicio = self.date_start.get_date()
            
            # Parámetros adicionales según tipo
            kwargs = {}
            if loan_type == "rapidiario":
                kwargs['frecuencia'] = self.combo_frequency.get()
            elif loan_type == "bancario":
                kwargs['meses'] = int(self.entry_months.get())
            
            # Calcular
            resultado = obtener_info_prestamo(loan_type, monto, tasa, fecha_inicio, **kwargs)
            
            # Mostrar cronograma en nueva ventana
            self.mostrar_cronograma_ventana(loan_type_display, resultado, fecha_inicio, monto, tasa, kwargs)
            
        except ValueError as e:
            messagebox.showerror("Error", f"Por favor ingrese valores numéricos válidos\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al calcular: {str(e)}")

    def mostrar_cronograma_ventana(self, loan_type, resultado, fecha_inicio, monto, tasa, kwargs):
        """Muestra el cronograma en una ventana nueva con scroll"""
        # Crear ventana nueva
        cronograma_win = tk.Toplevel(self)
        cronograma_win.title(f"Cronograma de Pagos - {loan_type}")
        cronograma_win.geometry("800x600")
        
        # Header
        header = tk.Frame(cronograma_win, bg=self.theme_colors['gradient_start'], height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text=f"📋 Cronograma de Pagos", 
                font=("Segoe UI", 16, "bold"), 
                bg=self.theme_colors['gradient_start'], 
                fg='white').pack(pady=10)
        
        tk.Label(header, text=f"{loan_type}", 
                font=("Segoe UI", 12), 
                bg=self.theme_colors['gradient_start'], 
                fg='white').pack()
        
        # Main container with scroll
        main_container = tk.Frame(cronograma_win)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Canvas and scrollbar
        canvas = tk.Canvas(main_container, bg='white')
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Resumen del préstamo
        resumen_frame = tk.LabelFrame(scrollable_frame, text="Resumen del Préstamo", 
                                     font=("Segoe UI", 11, "bold"), bg='white', padx=15, pady=10)
        resumen_frame.pack(fill=tk.X, padx=10, pady=10)
        
        info_data = [
            ("Monto Prestado:", f"S/ {monto:.2f}"),
            ("Tasa de Interés:", f"{tasa}% mensual"),
            ("Fecha Inicio:", fecha_inicio.strftime('%d/%m/%Y')),
        ]
        
        if 'fecha_vencimiento' in resultado:
            info_data.append(("Fecha Vencimiento:", resultado['fecha_vencimiento'].strftime('%d/%m/%Y')))
        
        if loan_type == "Rapidiario" and 'dias_laborables' in resultado:
            info_data.append(("Días Laborables:", f"{resultado['dias_laborables']} días"))
            info_data.append(("Frecuencia:", kwargs.get('frecuencia', 'Diario')))
        
        if loan_type == "Préstamo Bancario":
            # Para bancario, mostrar información más clara
            info_data.append(("Plazo:", f"{kwargs.get('meses', 3)} meses"))
            if 'interes_por_cuota' in resultado:
                info_data.append(("Interés Mensual:", f"S/ {resultado['interes_por_cuota']:.2f}"))
            if 'capital_por_cuota' in resultado:
                info_data.append(("Capital por Cuota:", f"S/ {resultado['capital_por_cuota']:.2f}"))
        
        info_data.extend([
            ("", ""),  # Separador
            ("Interés Total:", f"S/ {resultado['total_interes']:.2f}"),
            ("TOTAL A PAGAR:", f"S/ {resultado['total_pagar']:.2f}"),
        ])
        
        for i, (label, value) in enumerate(info_data):
            if label == "":
                continue
            
            is_total = "TOTAL" in label
            label_widget = tk.Label(resumen_frame, text=label, 
                                   font=("Segoe UI", 10, "bold" if is_total else "normal"), 
                                   bg='white', anchor='w')
            label_widget.grid(row=i, column=0, sticky='w', pady=3, padx=(0, 20))
            
            value_widget = tk.Label(resumen_frame, text=value, 
                                   font=("Segoe UI", 10, "bold" if is_total else "normal"), 
                                   bg='white', anchor='e',
                                   fg='#4CAF50' if is_total else 'black')
            value_widget.grid(row=i, column=1, sticky='e', pady=3)
        
        # Cronograma de cuotas
        cronograma_frame = tk.LabelFrame(scrollable_frame, text="Detalle de Cuotas", 
                                        font=("Segoe UI", 11, "bold"), bg='white', padx=15, pady=10)
        cronograma_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview para el cronograma
        columns = ("Cuota", "Fecha Vencimiento", "Monto", "Estado")
        tree = ttk.Treeview(cronograma_frame, columns=columns, show="headings", height=15)
        
        # Configurar columnas
        tree.heading("Cuota", text="N° Cuota")
        tree.heading("Fecha Vencimiento", text="Fecha Vencimiento")
        tree.heading("Monto", text="Monto")
        tree.heading("Estado", text="Estado")
        
        tree.column("Cuota", width=80, anchor='center')
        tree.column("Fecha Vencimiento", width=150, anchor='center')
        tree.column("Monto", width=120, anchor='e')
        tree.column("Estado", width=100, anchor='center')
        
        # Scrollbar para el treeview
        tree_scroll = ttk.Scrollbar(cronograma_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=tree_scroll.set)
        
        # Insertar datos
        for num, fecha, monto_cuota in resultado['cuotas']:
            tree.insert("", tk.END, values=(
                f"Cuota {num}",
                fecha.strftime('%d/%m/%Y'),
                f"S/ {monto_cuota:.2f}",
                "Pendiente"
            ))
        
        tree.pack(side='left', fill=tk.BOTH, expand=True)
        tree_scroll.pack(side='right', fill='y')
        
        # Botón cerrar
        btn_frame = tk.Frame(cronograma_win, bg='white')
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        close_btn = tk.Button(btn_frame, text="Cerrar", command=cronograma_win.destroy,
                             bg='#f44336', fg='white', font=("Segoe UI", 10, "bold"),
                             relief='flat', cursor='hand2', padx=20, pady=8)
        close_btn.pack(side='right', padx=5)

        # Botones de Acción (PDF, WhatsApp, Copiar)
        
        # Botones de Acción (PDF, WhatsApp, Copiar)
        
        def generar_pdf():
            generator = PDFGenerator()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simulacion_{timestamp}.pdf"
            filepath = os.path.join(generator.reports_dir, filename)
            
            # Preparar datos
            sim_data = {
                'monto': monto,
                'tasa': tasa,
                'tipo': loan_type,
                'fecha_inicio': fecha_inicio,
                'total_interes': resultado['total_interes'],
                'total_pagar': resultado['total_pagar']
            }
            
            try:
                path = generator.generate_simulation_report(filepath, sim_data, resultado['cuotas'])
                messagebox.showinfo("Éxito", f"PDF generado correctamente:\n{path}")
                os.startfile(path)
            except Exception as e:
                messagebox.showerror("Error", f"Error al generar PDF: {e}")

        def generar_y_copiar_imagen():
            try:
                from utils.image_generator import ImageGenerator
                img_gen = ImageGenerator()
                
                sim_data = {
                    'monto': monto,
                    'tasa': tasa,
                    'tipo': loan_type,
                    'fecha_inicio': fecha_inicio,
                    'total_interes': resultado['total_interes'],
                    'total_pagar': resultado['total_pagar']
                }
                
                # Generar imagen
                img = img_gen.generate_simulation_image(sim_data, resultado['cuotas'])
                
                # Copiar al portapapeles
                img_gen.copy_to_clipboard(img)
                return True
            except Exception as e:
                messagebox.showerror("Error", f"Error al generar imagen: {e}")
                return False

        def compartir_whatsapp():
            if generar_y_copiar_imagen():
                # Abrir WhatsApp Web
                webbrowser.open("https://web.whatsapp.com")
                messagebox.showinfo("WhatsApp", "Imagen copiada al portapapeles.\n\n1. Espera a que cargue WhatsApp Web.\n2. Selecciona el chat.\n3. Presiona Ctrl+V para pegar la imagen.")

        def copiar_imagen():
            if generar_y_copiar_imagen():
                messagebox.showinfo("Copiado", "Imagen de la simulación copiada al portapapeles.")

        # Botones
        tk.Button(btn_frame, text="📱 WhatsApp", command=compartir_whatsapp,
                 bg='#25D366', fg='white', font=("Segoe UI", 10, "bold"),
                 relief='flat', cursor='hand2', padx=15, pady=8).pack(side='left', padx=5)
                 
        tk.Button(btn_frame, text="📄 PDF", command=generar_pdf,
                 bg='#FF9800', fg='white', font=("Segoe UI", 10, "bold"),
                 relief='flat', cursor='hand2', padx=15, pady=8).pack(side='left', padx=5)

        tk.Button(btn_frame, text="📋 Copiar Img", command=copiar_imagen,
                 bg='#2196F3', fg='white', font=("Segoe UI", 10, "bold"),
                 relief='flat', cursor='hand2', padx=15, pady=8).pack(side='left', padx=5)
        
        # Bind mouse wheel for scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Proper cleanup on window close
        def on_close():
            try:
                canvas.unbind_all("<MouseWheel>")
            except:
                pass
            cronograma_win.destroy()
        
        cronograma_win.protocol("WM_DELETE_WINDOW", on_close)
