import tkinter as tk
from ui.modern_window import ModernWindow
from ui.main_window import ModernButton
from ui.ui_utils import get_module_icon

class DocumentsMenuWindow(ModernWindow):
    def __init__(self, parent):
        super().__init__(parent, title="Gestión de Documentos", width=800, height=600)
        self.create_widgets()

    def create_widgets(self):
        self.create_header("📂 Gestión de Documentos")
        
        content = self.create_content_frame()
        
        # Container for buttons
        btn_container = tk.Frame(content, bg=self.bg_color)
        btn_container.place(relx=0.5, rely=0.5, anchor='center')
        
        # Define available contracts
        contracts = [
            ("Contrato de Empeño", "📄", "#FF9800", self.open_pawn_contract),
            ("Contrato Rapidiario", "⚡", "#9C27B0", self.open_rapidiario_contract),
            ("Empeño Programado", "📅", "#2196F3", self.open_scheduled_pawn_contract),
            ("Notificaciones", "📢", "#F44336", self.open_notifications),
            ("Declaración Jurada", "📜", "#607D8B", self.open_affidavit),
            ("Constancia de No Adeudo", "✅", "#4CAF50", self.open_no_debt_certificate),
        ]
        
        row = 0
        col = 0
        max_cols = 2
        
        for text, icon, color, command in contracts:
            btn = ModernButton(btn_container, text, icon, color, command)
            btn.grid(row=row, column=col, padx=15, pady=15)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def open_pawn_contract(self):
        from ui.pawn_contract_window import PawnContractWindow
        PawnContractWindow(self)

    def open_rapidiario_contract(self):
        from ui.rapidiario_contract_window import RapidiarioContractWindow
        RapidiarioContractWindow(self)

    def open_scheduled_pawn_contract(self):
        from ui.scheduled_pawn_contract_window import ScheduledPawnContractWindow
        ScheduledPawnContractWindow(self)

    def open_notifications(self):
        from ui.notifications_window import NotificationsWindow
        NotificationsWindow(self)

    def open_affidavit(self):
        from ui.affidavit_window import AffidavitWindow
        AffidavitWindow(self)

    def open_no_debt_certificate(self):
        from ui.no_debt_certificate_window import NoDebtCertificateWindow
        NoDebtCertificateWindow(self)

