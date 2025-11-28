from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import os
from datetime import datetime

def generate_contract(loan_data, client_data, pawn_data=None):
    filename = f"contract_{loan_data['id']}_{client_data['dni']}.pdf"
    filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', filename)
    
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 2*cm, "CONTRATO DE PRÉSTAMO")
    
    from utils.settings_manager import get_setting
    company_name = get_setting('company_name') or "Mi Empresa"
    company_address = get_setting('company_address') or "Dirección Desconocida"
    company_ruc = get_setting('company_ruc') or "---"
    
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, height - 2.8*cm, f"{company_name} - RUC: {company_ruc}")
    c.drawCentredString(width/2, height - 3.3*cm, f"{company_address}")
    
    c.setFont("Helvetica", 12)
    c.drawString(2*cm, height - 4.5*cm, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}")
    
    # Client Info
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, height - 6*cm, "DATOS DEL CLIENTE:")
    c.setFont("Helvetica", 12)
    c.drawString(2*cm, height - 7*cm, f"Nombre: {client_data['first_name']} {client_data['last_name']}")
    c.drawString(2*cm, height - 8*cm, f"DNI: {client_data['dni']}")
    c.drawString(2*cm, height - 9*cm, f"Dirección: {client_data['address']}")
    
    # Loan Info
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, height - 10.5*cm, "DETALLES DEL PRÉSTAMO:")
    c.setFont("Helvetica", 12)
    c.drawString(2*cm, height - 11.5*cm, f"Monto: S/ {loan_data['amount']:.2f}")
    c.drawString(2*cm, height - 12.5*cm, f"Interés: {loan_data['interest_rate']}%")
    c.drawString(2*cm, height - 13.5*cm, f"Fecha Inicio: {loan_data['start_date']}")
    
    # Pawn Details (if applicable)
    if pawn_data:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2*cm, height - 15*cm, "GARANTÍA PRENDARIA:")
        c.setFont("Helvetica", 12)
        c.drawString(2*cm, height - 16*cm, f"Descripción: {pawn_data['description']}")
        c.drawString(2*cm, height - 17*cm, f"Material: {pawn_data['material']}")
        c.drawString(2*cm, height - 18*cm, f"Peso: {pawn_data['weight']} gr")
    
    # Signatures
    c.line(2*cm, 4*cm, 8*cm, 4*cm)
    c.drawString(3*cm, 3.5*cm, "EL ACREEDOR")
    
    c.line(12*cm, 4*cm, 18*cm, 4*cm)
    c.drawString(13*cm, 3.5*cm, "EL DEUDOR")
    
    c.save()
    return filepath
