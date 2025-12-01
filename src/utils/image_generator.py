from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime
from utils.settings_manager import get_setting

def generate_schedule_image(filepath, loan_data, client_data, installments, pawn_data=None):
    """Genera una imagen del cronograma para compartir"""
    
    # Configuración de dimensiones y colores
    width = 800
    base_height = 500
    pawn_height = 150 if pawn_data else 0
    installments_height = len(installments) * 30 + 100
    height = base_height + pawn_height + installments_height
    
    bg_color = "white"
    text_color = "black"
    header_color = "#2196F3"
    
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Intentar cargar fuentes, usar default si falla
    try:
        font_title = ImageFont.truetype("arial.ttf", 36)
        font_header = ImageFont.truetype("arial.ttf", 24)
        font_bold = ImageFont.truetype("arialbd.ttf", 18)
        font_normal = ImageFont.truetype("arial.ttf", 16)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except:
        font_title = ImageFont.load_default()
        font_header = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        font_normal = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Header Azul
    draw.rectangle([(0, 0), (width, 120)], fill=header_color)
    
    company_name = get_setting('company_name') or "Mi Empresa"
    company_ruc = get_setting('company_ruc') or "---"
    
    draw.text((width/2, 30), company_name, font=font_title, fill="white", anchor="mm")
    draw.text((width/2, 80), f"RUC: {company_ruc}", font=font_header, fill="white", anchor="mm")
    
    y = 150
    margin = 50
    
    # Datos del Cliente y Préstamo
    draw.text((margin, y), "DATOS DEL PRÉSTAMO", font=font_bold, fill=header_color)
    y += 30
    
    info_lines = [
        f"Cliente: {client_data['first_name']} {client_data['last_name']}",
        f"DNI: {client_data['dni']}",
        f"Préstamo ID: {loan_data['id']} - {loan_data['loan_type'].capitalize()}",
        f"Monto: S/ {loan_data['amount']:.2f}  |  Interés: {loan_data['interest_rate']}%",
        f"Fecha: {datetime.now().strftime('%d/%m/%Y')}"
    ]
    
    for line in info_lines:
        draw.text((margin, y), line, font=font_normal, fill=text_color)
        y += 25
        
    y += 20
    
    # Garantías (si existen)
    if pawn_data and len(pawn_data) > 0:
        draw.text((margin, y), "GARANTÍAS PRENDARIAS", font=font_bold, fill=header_color)
        y += 30
        for item in pawn_data:
            desc = f"• {item['item_type']} {item['brand']} - {item['characteristics']}"
            draw.text((margin, y), desc, font=font_small, fill=text_color)
            y += 25
        y += 20
        
    # Tabla de Cuotas
    draw.text((margin, y), "CRONOGRAMA DE PAGOS", font=font_bold, fill=header_color)
    y += 30
    
    # Cabecera Tabla
    cols = [50, 200, 400, 600]
    headers = ["N°", "Vencimiento", "Monto", "Estado"]
    
    draw.rectangle([(margin, y), (width-margin, y+30)], fill="#f0f0f0")
    
    draw.text((cols[0]+margin, y+5), headers[0], font=font_bold, fill=text_color)
    draw.text((cols[1], y+5), headers[1], font=font_bold, fill=text_color)
    draw.text((cols[2], y+5), headers[2], font=font_bold, fill=text_color)
    draw.text((cols[3], y+5), headers[3], font=font_bold, fill=text_color)
    
    y += 35
    
    total = 0
    for inst in installments:
        status_map = {'pending': 'Pendiente', 'paid': 'Pagado', 'partial': 'Parcial', 'overdue': 'Vencido'}
        status = status_map.get(inst['status'], inst['status'])
        
        draw.text((cols[0]+margin, y), str(inst['number']), font=font_normal, fill=text_color)
        draw.text((cols[1], y), inst['due_date'], font=font_normal, fill=text_color)
        draw.text((cols[2], y), f"S/ {inst['amount']:.2f}", font=font_normal, fill=text_color)
        draw.text((cols[3], y), status, font=font_normal, fill=text_color)
        
        total += inst['amount']
        y += 30
        
    # Total
    y += 10
    draw.line([(margin, y), (width-margin, y)], fill=header_color, width=2)
    y += 10
    draw.text((cols[1], y), "TOTAL A PAGAR:", font=font_bold, fill=text_color)
    draw.text((cols[2], y), f"S/ {total:.2f}", font=font_bold, fill=header_color)
    
    # Footer
    y += 60
    
    # Contact Information
    company_phone = get_setting('company_phone') or '999 999 999'
    company_phone2 = get_setting('company_phone2') or ''
    manager_phone = get_setting('manager_phone') or ''
    company_address = get_setting('company_address') or 'Dirección'
    
    # Get analyst info from loan's assigned analyst
    analyst_name = '---'
    analyst_phone = '999 999 999'
    
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
                analyst_phone = manager_phone or analyst_row['analyst_phone'] or '999 999 999'
            else:
                analyst_name = analyst_row['analyst_name'] or 'Analista'
                analyst_phone = analyst_row['analyst_phone'] or '999 999 999'
    
    # Build phone numbers string
    phones = company_phone
    if company_phone2:
        phones += f" / {company_phone2}"
    
    draw.text((width/2, y), f"{company_name}", font=font_bold, fill=header_color, anchor="mm")
    y += 25
    draw.text((width/2, y), f"{company_address} | Tel: {phones}", font=font_small, fill=text_color, anchor="mm")
    y += 20
    draw.text((width/2, y), f"Analista: {analyst_name} | Tel: {analyst_phone}", font=font_small, fill=text_color, anchor="mm")
    
    img.save(filepath)
    return filepath
