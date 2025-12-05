from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import os
import io
import win32clipboard
from utils.settings_manager import get_setting

class ImageGenerator:
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.assets_dir = os.path.join(self.project_root, 'assets')
        # Ensure assets dir exists
        os.makedirs(self.assets_dir, exist_ok=True)
        
        # Fonts - Try to load standard fonts, fallback to default
        try:
            self.font_bold_large = ImageFont.truetype("arialbd.ttf", 40)
            self.font_bold_medium = ImageFont.truetype("arialbd.ttf", 24)
            self.font_bold_small = ImageFont.truetype("arialbd.ttf", 18)
            self.font_regular = ImageFont.truetype("arial.ttf", 18)
            self.font_small = ImageFont.truetype("arial.ttf", 14)
        except IOError:
            self.font_bold_large = ImageFont.load_default()
            self.font_bold_medium = ImageFont.load_default()
            self.font_bold_small = ImageFont.load_default()
            self.font_regular = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

    def generate_simulation_image(self, simulation_data, schedule):
        """
        Generates an image for the simulation.
        Returns the PIL Image object.
        """
        # Canvas setup
        width = 800
        # Estimate height based on content
        # Header: 150, Details: 250, Schedule Header: 50, Schedule Items: 30 * len, Footer: 100
        # Limit schedule items for image to keep it readable/shareable? 
        # Let's show up to 30 items (Rapidiario) but split columns if needed?
        # For simplicity in image, let's just list them. If > 30, maybe truncate?
        # Rapidiario is max 30 days usually.
        
        num_items = len(schedule)
        schedule_height = (num_items + 2) * 35 # 35px per row
        
        height = 150 + 250 + 50 + schedule_height + 100
        
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Colors
        color_primary = "#4CAF50" # Green
        color_text = "black"
        color_white = "white"
        color_grey = "#666666"
        
        # --- Header ---
        draw.rectangle([0, 0, width, 120], fill=color_primary)
        
        company_name = get_setting('company_name') or "Mi Empresa"
        
        # Center text logic
        def draw_centered_text(text, font, y, color):
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) / 2
            draw.text((x, y), text, font=font, fill=color)
            
        draw_centered_text(company_name, self.font_bold_large, 30, color_white)
        draw_centered_text("SIMULACIÓN DE CRÉDITO", self.font_bold_medium, 80, color_white)
        
        y = 150
        
        # --- Details ---
        draw.text((30, y), "DETALLES DE LA SIMULACIÓN", font=self.font_bold_medium, fill=color_primary)
        y += 40
        
        monto = simulation_data.get('monto', 0)
        tasa = simulation_data.get('tasa', 0)
        tipo = simulation_data.get('tipo', '').capitalize()
        fecha = simulation_data.get('fecha_inicio', '').strftime('%d/%m/%Y')
        interes = simulation_data.get('total_interes', 0)
        total = simulation_data.get('total_pagar', 0)
        
        # Left Column
        draw.text((50, y), f"Tipo: {tipo}", font=self.font_regular, fill=color_text)
        y += 30
        draw.text((50, y), f"Monto: S/ {monto:,.2f}", font=self.font_regular, fill=color_text)
        y += 30
        draw.text((50, y), f"Tasa: {tasa}%", font=self.font_regular, fill=color_text)
        
        # Right Column (reset y to start of details)
        y_right = y - 60
        draw.text((450, y_right), f"Fecha: {fecha}", font=self.font_regular, fill=color_text)
        y_right += 30
        draw.text((450, y_right), f"Interés: S/ {interes:,.2f}", font=self.font_regular, fill=color_text)
        y_right += 30
        draw.text((450, y_right), f"TOTAL: S/ {total:,.2f}", font=self.font_bold_small, fill=color_text)
        
        y += 60
        
        # --- Schedule ---
        draw.text((30, y), "CRONOGRAMA DE PAGOS", font=self.font_bold_medium, fill=color_primary)
        y += 40
        
        # Table Header
        draw.rectangle([30, y, width-30, y+35], fill=color_primary)
        draw.text((50, y+5), "Cuota", font=self.font_bold_small, fill=color_white)
        draw.text((250, y+5), "Vencimiento", font=self.font_bold_small, fill=color_white)
        draw.text((550, y+5), "Monto", font=self.font_bold_small, fill=color_white)
        y += 35
        
        # Rows
        for i, (num, date_obj, amount) in enumerate(schedule):
            bg_color = "#f9f9f9" if i % 2 == 0 else "white"
            draw.rectangle([30, y, width-30, y+35], fill=bg_color)
            
            draw.text((50, y+5), str(num), font=self.font_regular, fill=color_text)
            draw.text((250, y+5), date_obj.strftime('%d/%m/%Y'), font=self.font_regular, fill=color_text)
            draw.text((550, y+5), f"S/ {amount:.2f}", font=self.font_regular, fill=color_text)
            
            y += 35
            
        y += 30
        
        # --- Footer ---
        company_address = get_setting('company_address') or "Dirección"
        company_phone = get_setting('company_phone') or "999 999 999"
        
        draw_centered_text(f"{company_address} | Tel: {company_phone}", self.font_small, y, color_grey)
        y += 20
        draw_centered_text("Generado por Sistema El Canguro", self.font_small, y, color_grey)
        
        return img

    def copy_to_clipboard(self, image):
        """
        Copies a PIL Image to the Windows clipboard.
        """
        output = io.BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()

    def generate_payment_receipt_image(self, payment_data):
        """
        Generates an image for a payment receipt.
        payment_data: dict with payment details
        """
        width = 600
        height = 700
        
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Colors
        color_primary = "#2196F3" # Blue for receipts
        color_text = "black"
        color_white = "white"
        color_grey = "#666666"
        
        # --- Header ---
        draw.rectangle([0, 0, width, 100], fill=color_primary)
        
        company_name = get_setting('company_name') or "Mi Empresa"
        
        def draw_centered_text(text, font, y, color):
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) / 2
            draw.text((x, y), text, font=font, fill=color)
            
        draw_centered_text(company_name, self.font_bold_medium, 25, color_white)
        draw_centered_text("COMPROBANTE DE PAGO", self.font_bold_small, 65, color_white)
        
        y = 130
        
        # --- Receipt Details ---
        draw.text((30, y), f"N° Recibo: {payment_data.get('receipt_number', '---')}", font=self.font_regular, fill=color_text)
        y += 30
        draw.text((30, y), f"Fecha: {payment_data.get('date', '')}", font=self.font_regular, fill=color_text)
        y += 40
        
        # --- Client ---
        draw.text((30, y), "CLIENTE", font=self.font_bold_small, fill=color_primary)
        y += 30
        draw.text((30, y), f"Nombre: {payment_data.get('client_name', '')}", font=self.font_regular, fill=color_text)
        y += 30
        draw.text((30, y), f"DNI: {payment_data.get('client_dni', '')}", font=self.font_regular, fill=color_text)
        y += 40
        
        # --- Loan Info ---
        draw.text((30, y), "DETALLE DEL PRÉSTAMO", font=self.font_bold_small, fill=color_primary)
        y += 30
        draw.text((30, y), f"Préstamo ID: {payment_data.get('loan_id', '')}", font=self.font_regular, fill=color_text)
        y += 30
        draw.text((30, y), f"Tipo: {payment_data.get('loan_type', '').capitalize()}", font=self.font_regular, fill=color_text)
        y += 40
        
        # --- Payment Info ---
        draw.rectangle([30, y, width-30, y+100], outline=color_primary, width=2)
        
        draw_centered_text("MONTO PAGADO", self.font_bold_small, y+15, color_text)
        draw_centered_text(f"S/ {payment_data.get('amount', 0):.2f}", self.font_bold_large, y+45, color_primary)
        
        y += 120
        
        # Concept (with wrapping)
        concept_text = f"Concepto: {payment_data.get('description', 'Pago de Préstamo')}"
        
        # Simple wrapping logic
        max_chars_per_line = 50
        if len(concept_text) > max_chars_per_line:
            # Split into two lines if too long
            split_idx = concept_text.rfind(' ', 0, max_chars_per_line)
            if split_idx == -1: split_idx = max_chars_per_line
            
            line1 = concept_text[:split_idx]
            line2 = concept_text[split_idx:].strip()
            
            draw.text((30, y), line1, font=self.font_regular, fill=color_text)
            y += 25
            draw.text((30, y), line2, font=self.font_regular, fill=color_text)
            y += 35
        else:
            draw.text((30, y), concept_text, font=self.font_regular, fill=color_text)
            y += 35
        
        draw.text((30, y), f"Método de Pago: {payment_data.get('payment_method', '').capitalize()}", font=self.font_regular, fill=color_text)
        y += 30
        draw.text((30, y), f"Cajero: {payment_data.get('cashier', 'Admin')}", font=self.font_regular, fill=color_text)
        
        # --- Footer ---
        y = height - 80
        company_address = get_setting('company_address') or "Dirección"
        company_phone = get_setting('company_phone') or "999 999 999"
        
        draw_centered_text(f"{company_address}", self.font_small, y, color_grey)
        y += 20
        draw_centered_text(f"Tel: {company_phone}", self.font_small, y, color_grey)
        y += 20
        draw_centered_text("Gracias por su preferencia", self.font_small, y, color_grey)
        
        return img
