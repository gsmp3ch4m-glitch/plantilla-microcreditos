from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os
from datetime import datetime

def generate_payment_schedule(filepath, loan_data, client_data, installments, pawn_details=None):
    from utils.settings_manager import get_setting
    
    company_name = get_setting('company_name') or "Mi Empresa"
    company_ruc = get_setting('company_ruc') or "---"
    
    # Create PDF with smaller margins
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=0.8*cm,
        bottomMargin=0.8*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title - COMPACT
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=15,
        textColor=colors.HexColor('#1976D2'),
        spaceAfter=5,
        alignment=1
    )
    elements.append(Paragraph("CRONOGRAMA DE PAGOS", title_style))
    
    # Company Info - COMPACT
    company_style = ParagraphStyle('Company', parent=styles['Normal'], fontSize=10, alignment=1, leading=11)
    elements.append(Paragraph(f"<b>{company_name}</b>", company_style))
    elements.append(Paragraph(f"RUC: {company_ruc}", company_style))
    elements.append(Spacer(1, 7))
    
    # Client and Loan Info - COMPACT
    info_style = ParagraphStyle('Info', parent=styles['Normal'], fontSize=9, leading=11)
    elements.append(Paragraph(
        f"<b>Cliente:</b> {loan_data['first_name']} {loan_data['last_name']} | "
        f"<b>DNI:</b> {loan_data['dni']}", info_style))
    elements.append(Paragraph(
        f"<b>Préstamo:</b> {loan_data['loan_type'].title()} | "
        f"<b>Monto:</b> S/ {loan_data['amount']:.2f} | "
        f"<b>Interés:</b> {loan_data['interest_rate']}%", info_style))
    elements.append(Spacer(1, 7))
    
    # Pawn Details Table (if applicable) - COMPACT
    if pawn_details:
        elements.append(Paragraph("<b>Garantías:</b>", info_style))
        elements.append(Spacer(1, 3))
        
        pawn_data = [['Tipo', 'Marca', 'Estado', 'Valor']]
        for pawn in pawn_details:
            pawn_data.append([
                pawn['item_type'],
                pawn['brand'],
                pawn['condition'],
                f"S/ {pawn['market_value']:.2f}"
            ])
        
        pawn_table = Table(pawn_data, colWidths=[3*cm, 3.5*cm, 2.5*cm, 2*cm])
        pawn_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        elements.append(pawn_table)
        elements.append(Spacer(1, 7))
    
    # Installments Table - COMPACT
    elements.append(Paragraph("<b>CRONOGRAMA DE PAGOS</b>", info_style))
    elements.append(Spacer(1, 4))
    
    data = [['N°', 'Vencimiento', 'Monto', 'Estado']]
    total_to_pay = 0
    for inst in installments:
        data.append([
            str(inst['number']),
            inst['due_date'],
            f"S/ {inst['amount']:.2f}",
            inst['status'].title()
        ])
        total_to_pay += inst['amount']
    
    # Add TOTAL row
    data.append(['', 'TOTAL A PAGAR:', f"S/ {total_to_pay:.2f}", ''])
    
    t = Table(data, colWidths=[1.2*cm, 3*cm, 2.5*cm, 2.5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1976D2')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('ROWBACKGROUNDS', (0,1), (-2,-1), [colors.white, colors.HexColor('#E3F2FD')]),
        # Total row styling
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#E3F2FD')),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,-1), (-1,-1), 9),
        ('TEXTCOLOR', (1,-1), (2,-1), colors.HexColor('#1976D2')),
        ('SPAN', (0,-1), (0,-1)),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    elements.append(t)
    
    # Contact Information Footer - COMPACT
    elements.append(Spacer(1, 7))
    
    company_phone = get_setting('company_phone') or '---'
    company_phone2 = get_setting('company_phone2') or ''
    manager_phone = get_setting('manager_phone') or ''
    company_address = get_setting('company_address') or '---'
    
    # Get analyst info from loan's assigned analyst
    analyst_name = '---'
    analyst_phone = '---'
    
    analyst_id = loan_data.get('analyst_id') if hasattr(loan_data, 'get') else loan_data['analyst_id'] if 'analyst_id' in loan_data.keys() else None
    if analyst_id:
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT analyst_name, analyst_phone, role FROM users WHERE id = ?", (analyst_id,))
        analyst_row = cursor.fetchone()
        conn.close()
        if analyst_row:
            # If admin, use manager name and phone from settings
            if analyst_row['role'] == 'admin':
                analyst_name = get_setting('company_manager') or analyst_row['analyst_name'] or 'Gerente General'
                analyst_phone = manager_phone or analyst_row['analyst_phone'] or '---'
            else:
                analyst_name = analyst_row['analyst_name'] or 'Analista'
                analyst_phone = analyst_row['analyst_phone'] or '---'
    
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=1, leading=9)
    
    # Build phone numbers string
    phones = company_phone
    if company_phone2:
        phones += f" / {company_phone2}"
    
    # Don't repeat company name, just show address and contact
    elements.append(Paragraph(f"{company_address} | Tel: {phones}", footer_style))
    elements.append(Paragraph(f"Analista: {analyst_name} | Tel: {analyst_phone}", footer_style))
    
    doc.build(elements)
    return filepath
