import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ui.modern_window import ModernWindow
from utils.analytics_manager import AnalyticsManager

class AnalysisWindow(ModernWindow):
    def __init__(self, parent):
        super().__init__(parent, title="Análisis Financiero Avanzado", width=1100, height=750)
        self.manager = AnalyticsManager()
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        # Header
        self.create_header("📊 Tablero de Control Financiero")
        
        # Main Content
        content = self.create_content_frame()
        
        # Tabs
        self.notebook = ttk.Notebook(content)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Tab 1: Resultados (Utilidad)
        self.tab_results = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.tab_results, text="💰 Resultados (Utilidad)")
        self.setup_results_tab()
        
        # Tab 2: Calidad de Cartera
        self.tab_quality = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.tab_quality, text="👥 Calidad de Cartera")
        self.setup_quality_tab()
        
        # Tab 3: Distribución
        self.tab_dist = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.tab_dist, text="📈 Distribución de Inversión")
        self.setup_dist_tab()

    def setup_results_tab(self):
        # Controls
        controls = tk.Frame(self.tab_results, bg='white')
        controls.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(controls, text="Desde:", bg='white', font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=5)
        self.date_start = DateEntry(controls, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='y-mm-dd')
        self.date_start.pack(side=tk.LEFT, padx=5)
        
        tk.Label(controls, text="Hasta:", bg='white', font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=5)
        self.date_end = DateEntry(controls, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='y-mm-dd')
        self.date_end.pack(side=tk.LEFT, padx=5)
        
        tk.Label(controls, text="Agrupar:", bg='white', font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=5)
        self.combo_period = ttk.Combobox(controls, values=["Diario", "Mensual", "Anual"], state="readonly", width=10)
        self.combo_period.current(1)
        self.combo_period.pack(side=tk.LEFT, padx=5)
        
        btn_update = tk.Button(controls, text="Actualizar", command=self.update_results_chart,
                             bg='#2196F3', fg='white', relief='flat', font=("Segoe UI", 9, "bold"))
        btn_update.pack(side=tk.LEFT, padx=10)
        
        # Chart Area
        # Main Container (Horizontal)
        container = tk.Frame(self.tab_results, bg='white')
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left Side: Chart
        left_frame = tk.Frame(container, bg='white')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.fig_results = Figure(figsize=(6, 5), dpi=100)
        self.ax_results = self.fig_results.add_subplot(111)
        self.canvas_results = FigureCanvasTkAgg(self.fig_results, master=left_frame)
        self.canvas_results.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Right Side: Summary
        right_frame = tk.Frame(container, bg='#f5f5f5', width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))
        right_frame.pack_propagate(False)
        
        tk.Label(right_frame, text="Resumen de Utilidad", font=("Segoe UI", 12, "bold"), bg='#f5f5f5').pack(pady=15)
        
        # Total
        self.lbl_total_profit = tk.Label(right_frame, text="Total: S/ 0.00", 
                                         font=("Segoe UI", 14, "bold"), bg='#f5f5f5', fg='#4CAF50')
        self.lbl_total_profit.pack(pady=(0, 20))
        
        # Details Container
        self.profit_details_frame = tk.Frame(right_frame, bg='#f5f5f5')
        self.profit_details_frame.pack(fill=tk.BOTH, expand=True, padx=10)

    def setup_quality_tab(self):
        # Main Container (Horizontal)
        container = tk.Frame(self.tab_quality, bg='white')
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left Side: Chart
        left_frame = tk.Frame(container, bg='white')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="Evolución de Calidad de Cartera", 
                font=("Segoe UI", 12, "bold"), bg='white').pack(pady=(0, 10))
                
        self.fig_quality = Figure(figsize=(6, 5), dpi=100)
        self.ax_quality = self.fig_quality.add_subplot(111)
        self.canvas_quality = FigureCanvasTkAgg(self.fig_quality, master=left_frame)
        self.canvas_quality.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Right Side: Stats
        right_frame = tk.Frame(container, bg='#f5f5f5', width=250)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))
        right_frame.pack_propagate(False) # Fixed width
        
        tk.Label(right_frame, text="Estado Actual", font=("Segoe UI", 12, "bold"), bg='#f5f5f5').pack(pady=15)
        
        # Stats Containers
        self.stats_labels = {}
        categories = [
            ("Bueno", "#4CAF50", "Pagos Puntuales"),
            ("Regular", "#FFC107", "Atraso Leve"),
            ("Riesgoso", "#FF9800", "Atraso > 15d"),
            ("Malo", "#F44336", "Morosos")
        ]
        
        for cat, color, desc in categories:
            frame = tk.Frame(right_frame, bg='white', relief='flat', bd=1)
            frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Color indicator strip
            tk.Frame(frame, bg=color, width=5).pack(side=tk.LEFT, fill=tk.Y)
            
            content = tk.Frame(frame, bg='white', padx=10, pady=5)
            content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            tk.Label(content, text=cat, font=("Segoe UI", 10, "bold"), bg='white', fg='#555').pack(anchor='w')
            tk.Label(content, text=desc, font=("Segoe UI", 8), bg='white', fg='#888').pack(anchor='w')
            
            count_lbl = tk.Label(frame, text="0", font=("Segoe UI", 16, "bold"), bg='white', fg=color)
            count_lbl.pack(side=tk.RIGHT, padx=15)
            
            self.stats_labels[cat] = count_lbl

    def setup_dist_tab(self):
        # Main Container
        container = tk.Frame(self.tab_dist, bg='white')
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left: Chart
        left_frame = tk.Frame(container, bg='white')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="Distribución del Capital Invertido", 
                font=("Segoe UI", 12, "bold"), bg='white').pack(pady=(0, 10))
                
        self.fig_dist = Figure(figsize=(6, 5), dpi=100)
        self.ax_dist = self.fig_dist.add_subplot(111)
        self.canvas_dist = FigureCanvasTkAgg(self.fig_dist, master=left_frame)
        self.canvas_dist.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Right: Summary
        right_frame = tk.Frame(container, bg='#f5f5f5', width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))
        right_frame.pack_propagate(False)
        
        tk.Label(right_frame, text="Resumen de Inversión", font=("Segoe UI", 12, "bold"), bg='#f5f5f5').pack(pady=15)
        
        # Total
        self.lbl_total_invested = tk.Label(right_frame, text="Total: S/ 0.00", 
                                         font=("Segoe UI", 14, "bold"), bg='#f5f5f5', fg='#2196F3')
        self.lbl_total_invested.pack(pady=(0, 20))
        
        # Details Container
        self.dist_details_frame = tk.Frame(right_frame, bg='#f5f5f5')
        self.dist_details_frame.pack(fill=tk.BOTH, expand=True, padx=10)

    def load_data(self):
        self.update_results_chart()
        self.update_quality_chart()
        self.update_dist_chart()

    def update_results_chart(self, event=None):
        period_map = {"Diario": "daily", "Mensual": "monthly", "Anual": "yearly"}
        period = period_map.get(self.combo_period.get(), "monthly")
        
        start_date = self.date_start.get_date().strftime("%Y-%m-%d")
        end_date = self.date_end.get_date().strftime("%Y-%m-%d")
        
        x, y = self.manager.get_profit_loss(period, start_date, end_date)
        
        self.ax_results.clear()
        self.ax_results.plot(x, y, marker='o', linestyle='-', color='#4CAF50', linewidth=2)
        self.ax_results.set_title("Utilidad Neta Estimada")
        self.ax_results.set_ylabel("Monto (S/)")
        self.ax_results.grid(True, linestyle='--', alpha=0.7)
        self.ax_results.tick_params(axis='x', rotation=45)
        self.fig_results.tight_layout()
        self.canvas_results.draw()
        
        # Update Side Panel
        breakdown = self.manager.get_profit_breakdown(start_date, end_date)
        gross_profit = sum(breakdown.values())
        expenses = self.manager.get_general_expenses(start_date, end_date)
        net_profit = gross_profit - expenses
        
        self.lbl_total_profit.config(text=f"Utilidad Neta: S/ {net_profit:,.2f}")
        
        # Clear details
        for widget in self.profit_details_frame.winfo_children():
            widget.destroy()
            
        # Summary Section (Gross, Expenses, Net)
        summary_frame = tk.Frame(self.profit_details_frame, bg='white', pady=10)
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        def add_summary_row(label, value, color='black', bold=False):
            font_style = ("Segoe UI", 10, "bold") if bold else ("Segoe UI", 10)
            row = tk.Frame(summary_frame, bg='white')
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label, font=font_style, bg='white', fg='#555').pack(side=tk.LEFT, padx=10)
            tk.Label(row, text=f"S/ {value:,.2f}", font=font_style, bg='white', fg=color).pack(side=tk.RIGHT, padx=10)

        add_summary_row("Utilidad Bruta", gross_profit, '#2196F3', True)
        add_summary_row("Gastos Generales", expenses, '#F44336')
        tk.Frame(summary_frame, bg='#ddd', height=1).pack(fill=tk.X, pady=5)
        add_summary_row("Utilidad Neta", net_profit, '#4CAF50', True)

        tk.Label(self.profit_details_frame, text="Desglose por Producto", font=("Segoe UI", 10, "bold"), bg='#f5f5f5', fg='#777').pack(anchor='w', pady=(10, 5))

        # Populate breakdown details
        categories = [
            ("Rapidiario", "#FF9800"),
            ("Empeño", "#9C27B0"),
            ("Bancario", "#2196F3"),
            ("Congelado", "#607D8B")
        ]
        
        for cat, color in categories:
            val = breakdown.get(cat, 0)
            pct = (val / gross_profit * 100) if gross_profit > 0 else 0
            
            row = tk.Frame(self.profit_details_frame, bg='white', relief='flat', bd=1)
            row.pack(fill=tk.X, pady=5)
            
            tk.Frame(row, bg=color, width=5).pack(side=tk.LEFT, fill=tk.Y)
            
            content = tk.Frame(row, bg='white', padx=10, pady=5)
            content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            tk.Label(content, text=cat, font=("Segoe UI", 10, "bold"), bg='white').pack(anchor='w')
            tk.Label(content, text=f"{pct:.1f}%", font=("Segoe UI", 9), bg='white', fg='#777').pack(anchor='w')
            
            tk.Label(row, text=f"S/ {val:,.2f}", font=("Segoe UI", 10, "bold"), bg='white', fg='#333').pack(side=tk.RIGHT, padx=10)

    def update_quality_chart(self):
        stats = self.manager.get_client_quality_evolution()
        fechas = stats['fechas']
        
        self.ax_quality.clear()
        
        # Plot Lines
        self.ax_quality.plot(fechas, stats['Bueno'], marker='o', label='Bueno', color='#4CAF50', linewidth=2)
        self.ax_quality.plot(fechas, stats['Regular'], marker='o', label='Regular', color='#FFC107', linewidth=2)
        self.ax_quality.plot(fechas, stats['Riesgoso'], marker='o', label='Riesgoso', color='#FF9800', linewidth=2)
        self.ax_quality.plot(fechas, stats['Malo'], marker='o', label='Malo', color='#F44336', linewidth=2)
        
        self.ax_quality.set_title("Evolución de Calidad de Cartera")
        self.ax_quality.set_ylabel("Cantidad de Clientes")
        self.ax_quality.grid(True, linestyle='--', alpha=0.5)
        self.ax_quality.legend()
        self.fig_quality.tight_layout()
        self.canvas_quality.draw()
        
        # Update Stats Labels (Last value in series)
        if stats['Bueno']:
            self.stats_labels['Bueno'].config(text=str(stats['Bueno'][-1]))
            self.stats_labels['Regular'].config(text=str(stats['Regular'][-1]))
            self.stats_labels['Riesgoso'].config(text=str(stats['Riesgoso'][-1]))
            self.stats_labels['Malo'].config(text=str(stats['Malo'][-1]))

    def update_dist_chart(self):
        data = self.manager.get_investment_distribution()
        labels = list(data.keys())
        values = list(data.values())
        total = sum(values)
        
        self.ax_dist.clear()
        
        # Clear details frame
        for widget in self.dist_details_frame.winfo_children():
            widget.destroy()
            
        self.lbl_total_invested.config(text=f"Total: S/ {total:,.2f}")
        
        if values:
            wedges, texts, autotexts = self.ax_dist.pie(values, labels=labels, autopct='%1.1f%%', 
                                                      startangle=90, pctdistance=0.85,
                                                      colors=['#2196F3', '#9C27B0', '#FF9800', '#607D8B'])
            
            # Draw Donut Circle
            centre_circle = matplotlib.patches.Circle((0,0),0.70,fc='white')
            self.ax_dist.add_artist(centre_circle)
            
            self.ax_dist.axis('equal')
            
            # Populate Side Panel
            colors = ['#2196F3', '#9C27B0', '#FF9800', '#607D8B']
            for i, (label, value) in enumerate(zip(labels, values)):
                color = colors[i % len(colors)]
                pct = (value / total * 100) if total > 0 else 0
                
                row = tk.Frame(self.dist_details_frame, bg='white', relief='flat', bd=1)
                row.pack(fill=tk.X, pady=5)
                
                tk.Frame(row, bg=color, width=5).pack(side=tk.LEFT, fill=tk.Y)
                
                content = tk.Frame(row, bg='white', padx=10, pady=5)
                content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                
                tk.Label(content, text=label, font=("Segoe UI", 10, "bold"), bg='white').pack(anchor='w')
                tk.Label(content, text=f"{pct:.1f}%", font=("Segoe UI", 9), bg='white', fg='#777').pack(anchor='w')
                
                tk.Label(row, text=f"S/ {value:,.2f}", font=("Segoe UI", 10, "bold"), bg='white', fg='#333').pack(side=tk.RIGHT, padx=10)
                
        else:
            self.ax_dist.text(0.5, 0.5, "Sin datos de inversión", ha='center')
            
        self.canvas_dist.draw()
