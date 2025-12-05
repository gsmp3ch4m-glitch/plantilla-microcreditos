from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, KeepTogether
from datetime import datetime
import os

class PDFGenerator:
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.reports_dir = os.path.join(self.project_root, 'reports')
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_cash_report(self, data):
        """
        Generates a PDF report for cash closing.
        data: dict with keys 'income', 'expense', 'balance', 'details' (list of transactions)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"cierre_caja_{timestamp}.pdf"
        filepath = os.path.join(self.reports_dir, filename)
        
        c = canvas.Canvas(filepath, pagesize=A4)
        width, height = A4
        
        # Header
        c.setFont("Helvetica-Bold", 18)
        c.drawString(2*cm, height - 2*cm, "Reporte de Cierre de Caja")
        
        c.setFont("Helvetica", 10)
        c.drawString(2*cm, height - 2.8*cm, f"Fecha de Generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        c.drawString(2*cm, height - 3.3*cm, f"Generado por: {data.get('user', 'Sistema')}")
        
        # Summary Box
        c.rect(2*cm, height - 6*cm, width - 4*cm, 2.5*cm)
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2.5*cm, height - 4.5*cm, "Resumen Financiero")
        
        c.setFont("Helvetica", 11)
        c.drawString(2.5*cm, height - 5.2*cm, f"Total Ingresos: S/ {data['income']:,.2f}")
        c.drawString(8*cm, height - 5.2*cm, f"Total Egresos: S/ {data['expense']:,.2f}")
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(14*cm, height - 5.2*cm, f"Balance: S/ {data['balance']:,.2f}")
        
        # Transactions Table Header
        y = height - 7*cm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(1.5*cm, y, "Hora")
        c.drawString(3*cm, y, "Tipo")
        c.drawString(5*cm, y, "Cliente")
        c.drawString(9*cm, y, "Categoría")
        c.drawString(12.5*cm, y, "Descripción")
        c.drawString(17.5*cm, y, "Monto")
        
        c.line(1.5*cm, y - 0.2*cm, width - 1.5*cm, y - 0.2*cm)
        
        y -= 0.8*cm
        c.setFont("Helvetica", 9)
        
        # Category Map
        cat_map = {
            'payment': 'Pago Cuota',
            'loan_disbursement': 'Desembolso',
            'petty_cash_deposit': 'Depósito Caja Chica',
            'petty_cash_withdrawal': 'Retiro Caja Chica'
        }
        
        for trans in data['details']:
            if y < 3*cm: # New Page
                c.showPage()
                y = height - 2*cm
            
            # trans is expected to be a dict or sqlite3.Row
            t_time = trans['date'][11:16] if len(trans['date']) > 16 else trans['date']
            t_type = "Ingreso" if trans['type'] == 'income' else "Egreso"
            
            # Category Translation
            t_cat_raw = trans['category']
            t_cat = cat_map.get(t_cat_raw, t_cat_raw)[:15] # Truncate category
            
            t_desc = trans['description'][:30] + "..." if len(trans['description']) > 30 else trans['description']
            t_amount = f"S/ {trans['amount']:,.2f}"
            
            # Client Name
            if trans['first_name']:
                t_client = f"{trans['first_name']} {trans['last_name']}"
                t_client = t_client[:20] + "..." if len(t_client) > 20 else t_client
            else:
                t_client = "-"
            
            c.drawString(1.5*cm, y, t_time)
            c.drawString(3*cm, y, t_type)
            c.drawString(5*cm, y, t_client)
            c.drawString(9*cm, y, t_cat)
            c.drawString(12.5*cm, y, t_desc)
            c.drawRightString(width - 1.5*cm, y, t_amount)
            
            y -= 0.6*cm
            
        # Signature
        c.line(width/2 - 3*cm, 2*cm, width/2 + 3*cm, 2*cm)
        c.drawCentredString(width/2, 1.5*cm, "Firma Responsable")
        
        c.save()
        return filepath

    def generate_simulation_report(self, filepath, simulation_data, schedule):
        """
        Generates a PDF for loan simulation (Quote).
        simulation_data: dict with loan details (amount, rate, type, etc.)
        schedule: list of tuples (num, date, amount)
        """
        from utils.settings_manager import get_setting
        
        c = canvas.Canvas(filepath, pagesize=A4)
        width, height = A4
        
        # Get company settings
        company_name = get_setting('company_name') or "Mi Empresa"
        company_address = get_setting('company_address') or "Dirección"
        company_phone = get_setting('company_phone') or "999 999 999"
        
        # Header (Green for Simulation)
        c.setFillColor(colors.HexColor('#4CAF50'))
        c.rect(0, height - 2.5*cm, width, 2.5*cm, fill=True, stroke=False)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width/2, height - 1.2*cm, company_name)
        c.setFont("Helvetica", 12)
        c.drawCentredString(width/2, height - 1.8*cm, "SIMULACIÓN DE CRÉDITO")
        
        # Reset to black
        c.setFillColor(colors.black)
        
        y = height - 3.2*cm
        
        # Simulation Details
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.HexColor('#4CAF50'))
        c.drawString(2*cm, y, "DETALLES DE LA SIMULACIÓN")
        c.setFillColor(colors.black)
        y -= 0.6*cm
        
        c.setFont("Helvetica", 10)
        
        # Format currency
        monto = simulation_data.get('monto', 0)
        total = simulation_data.get('total_pagar', 0)
        interes = simulation_data.get('total_interes', 0)
        
        # Compact details layout (2 columns for details)
        col1_x = 2.5*cm
        col2_x = 11*cm
        
        details_left = [
            f"Tipo de Préstamo: {simulation_data.get('tipo', '').capitalize()}",
            f"Monto Solicitado: S/ {monto:,.2f}",
            f"Tasa de Interés: {simulation_data.get('tasa', 0)}%",
        ]
        
        details_right = [
            f"Fecha de Inicio: {simulation_data.get('fecha_inicio', '').strftime('%d/%m/%Y')}",
            f"Total Intereses: S/ {interes:,.2f}",
            f"TOTAL A PAGAR: S/ {total:,.2f}"
        ]
        
        start_y = y
        for line in details_left:
            c.drawString(col1_x, y, line)
            y -= 0.5*cm
            
        y = start_y
        for line in details_right:
            if "TOTAL A PAGAR" in line:
                c.setFont("Helvetica-Bold", 10)
            c.drawString(col2_x, y, line)
            c.setFont("Helvetica", 10)
            y -= 0.5*cm
            
        y -= 0.5*cm
        
        # Schedule Table
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.HexColor('#4CAF50'))
        c.drawString(2*cm, y, "CRONOGRAMA PROYECTADO")
        c.setFillColor(colors.black)
        y -= 0.6*cm
        
        # Determine layout based on number of items
        num_items = len(schedule)
        use_two_columns = num_items > 15
        
        if use_two_columns:
            # Split data into two columns
            mid_point = (num_items + 1) // 2
            col1_data = schedule[:mid_point]
            col2_data = schedule[mid_point:]
            
            # Prepare table data with 6 columns + spacer
            # Columns: #, Date, Amount, Spacer, #, Date, Amount
            table_data = [['Cuota', 'Vencimiento', 'Monto', '', 'Cuota', 'Vencimiento', 'Monto']]
            
            for i in range(len(col1_data)):
                row = []
                # Left side
                item1 = col1_data[i]
                row.extend([str(item1[0]), item1[1].strftime('%d/%m/%Y'), f"S/ {item1[2]:.2f}"])
                
                # Spacer
                row.append('')
                
                # Right side
                if i < len(col2_data):
                    item2 = col2_data[i]
                    row.extend([str(item2[0]), item2[1].strftime('%d/%m/%Y'), f"S/ {item2[2]:.2f}"])
                else:
                    row.extend(['', '', ''])
                
                table_data.append(row)
                
            col_widths = [1.5*cm, 2.5*cm, 2.5*cm, 1*cm, 1.5*cm, 2.5*cm, 2.5*cm]
            
        else:
            # Standard single column layout
            table_data = [['Cuota', 'Fecha Vencimiento', 'Monto (S/)']]
            for num, date_obj, amount in schedule:
                table_data.append([
                    str(num),
                    date_obj.strftime('%d/%m/%Y'),
                    f"S/ {amount:.2f}"
                ])
            col_widths = [2*cm, 5*cm, 4*cm]

        # Create table
        table = Table(table_data, colWidths=col_widths)
        
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ])
        
        if use_two_columns:
            # Remove grid and background for spacer column (index 3)
            style.add('BACKGROUND', (3, 0), (3, -1), colors.white)
            style.add('GRID', (3, 0), (3, -1), 0, colors.white)
            style.add('TEXTCOLOR', (3, 0), (3, 0), colors.white) # Hide header text in spacer if any
        
        table.setStyle(style)
        
        table.wrapOn(c, width, height)
        table_height = table._height
        
        # Check if new page needed (unlikely with 2 columns but good practice)
        if y - table_height < 2*cm:
            c.showPage()
            y = height - 2*cm
            
        table.drawOn(c, 2*cm, y - table_height)
        
        # Footer
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.grey)
        c.drawCentredString(width/2, 1.5*cm, f"{company_address} | Tel: {company_phone}")
        c.drawCentredString(width/2, 1.0*cm, "Nota: Esta simulación es referencial y no constituye una aprobación del crédito.")
        
        c.save()
        return filepath



    def generate_pawn_contract(self, filepath, contract_data):
        """
        Generates the Pawn Shop Contract (Contrato de Préstamo Prendario).
        contract_data: dict with all necessary fields (client, loan, items, etc.)
        """
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
        from reportlab.lib.units import cm
        
        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                rightMargin=2.5*cm, leftMargin=2.5*cm,
                                topMargin=2.5*cm, bottomMargin=2.5*cm)
        
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, fontName='Helvetica', fontSize=10, leading=14))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=12, leading=16))
        styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT, fontName='Helvetica', fontSize=10))
        
        story = []
        
        # Title
        story.append(Paragraph("CONTRATO DE PRESTAMO PRENDARIO", styles['Center']))
        story.append(Paragraph("CONTRATO DE PRESTAMO DE DINERO CON GARANTIA PRENDARIA", styles['Center']))
        story.append(Spacer(1, 12))
        
        # Intro
        intro_text = f"En la ciudad de Huamanga, Ayacucho, a los <b>{contract_data['dia']}</b> días del mes de <b>{contract_data['mes']}</b> del año <b>{contract_data['anio']}</b>, se celebra el presente contrato de préstamo de dinero con garantía prendaria, entre las siguientes partes:"
        story.append(Paragraph(intro_text, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # I. PARTES CONTRATANTES
        story.append(Paragraph("I. PARTES CONTRATANTES", styles['Heading3']))
        
        part1 = """1. <b>EL ACREEDOR:</b> CORPORACIÓN EL CANGURO S.A.C., inscrita en la Partida Electrónica N° 11191281 del Registro Público de Ayacucho, con RUC N° 20614279924, con domicilio legal en Av. Mariscal Cáceres N° 850, Segundo Piso, Huamanga, Ayacucho, representada por su Gerente General, señor Edgar Tucno Pacotaype, identificado con DNI N° 45303843, con domicilio en Jr. Puno Mz. G Lt. 10, La Florida, Carmen Alto, Ayacucho, quien en adelante será denominado EL ACREEDOR."""
        story.append(Paragraph(part1, styles['Justify']))
        story.append(Spacer(1, 6))
        
        part2 = f"""2. <b>EL DEUDOR:</b> <b>{contract_data['cliente_nombre']}</b>, identificado con DNI N° <b>{contract_data['cliente_dni']}</b>, con domicilio en <b>{contract_data['cliente_direccion']}</b>, quien en adelante será denominado EL DEUDOR."""
        story.append(Paragraph(part2, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # II. OBJETO DEL CONTRATO
        story.append(Paragraph("II. OBJETO DEL CONTRATO", styles['Heading3']))
        objeto = f"""Por el presente contrato, EL ACREEDOR entrega a EL DEUDOR, en calidad de préstamo, la suma de <b>S/ {contract_data['monto_prestamo']} ({contract_data['monto_texto']})</b>, la cual será devuelta por EL DEUDOR en los términos y condiciones establecidos en este contrato. Como garantía del cumplimiento de las obligaciones, EL DEUDOR entrega en prenda el bien descrito en la cláusula tercera, conforme a lo dispuesto en el Código Civil Peruano y la Ley N° 28677, Ley de la Garantía Mobiliaria."""
        story.append(Paragraph(objeto, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # III. DESCRIPCIÓN DEL BIEN EN PRENDA
        story.append(Paragraph("III. DESCRIPCIÓN DEL BIEN EN PRENDA", styles['Heading3']))
        story.append(Paragraph("1. Bien en Garantía: EL DEUDOR entrega en prenda a EL ACREEDOR el siguiente bien:", styles['Justify']))
        story.append(Spacer(1, 6))
        
        # Items
        for item in contract_data['items']:
            item_desc = f"• <b>{item['tipo']} {item['marca']}</b>: <b>{item['descripcion']}</b>. Estado: <b>{item['estado']}</b>. Valor estimado: <b>S/ {item['valor']}</b>."
            story.append(Paragraph(item_desc, styles['Justify'], bulletText="•"))
        story.append(Spacer(1, 6))
        
        condiciones = """2. Condiciones de la Prenda:<br/>
        • El bien será custodiado por EL ACREEDOR en un lugar seguro designado por este, y EL DEUDOR autoriza su depósito.<br/>
        • EL DEUDOR declara ser propietario legítimo del bien y que este se encuentra libre de gravámenes, embargos o cualquier limitación de dominio.<br/>
        • El bien será devuelto a EL DEUDOR una vez cumplidas íntegramente las obligaciones de pago establecidas en este contrato."""
        story.append(Paragraph(condiciones, styles['Justify']))
        story.append(Spacer(1, 6))
        
        registro = "3. Registro de la Prenda: La prenda será inscrita en el Registro de Garantías Mobiliarias, conforme a la Ley N° 28677, siendo los costos de inscripción asumidos por EL DEUDOR."
        story.append(Paragraph(registro, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # IV. CONDICIONES DEL PRÉSTAMO
        story.append(Paragraph("IV. CONDICIONES DEL PRÉSTAMO", styles['Heading3']))
        
        cond1 = f"1. Monto del Préstamo: El Capital asciende a <b>S/ {contract_data['monto_prestamo']} ({contract_data['monto_texto']})</b>."
        story.append(Paragraph(cond1, styles['Justify']))
        
        cond2 = f"2. Tasa de Interés y Gastos: El préstamo devengará una tasa de interés mensual de <b>{contract_data.get('tasa_interes_base', contract_data['tasa_interes'])}%</b>, determinada por el Gerente General de EL ACREEDOR, más un <b>2%</b> adicional en concepto de gastos administrativos y otros costos asociados, totalizando un costo financiero efectivo mensual de <b>{contract_data.get('tasa_total', contract_data['tasa_interes'])}%</b>. El interés mensual a pagar asciende a <b>S/ {contract_data['interes_monto']} ({contract_data['interes_texto']})</b>. Los gastos adicionales, como costos de custodia, notariales, registrales o legales, serán asumidos íntegramente por EL DEUDOR."
        story.append(Paragraph(cond2, styles['Justify']))
        
        cond3 = "3. Plazo del Préstamo: El plazo del préstamo será de 30 días calendario, contados a partir de la fecha de desembolso del Capital."
        story.append(Paragraph(cond3, styles['Justify']))
        
        cond4 = f"4. Modalidad de Pago: EL DEUDOR se obliga a realizar el pago del Capital, intereses y gastos en una sola cuota al vencimiento del plazo de 30 días, conforme al cronograma de pagos que se adjunta como Anexo 1 al presente contrato. El monto total a pagar al vencimiento es de <b>S/ {contract_data['total_pagar']} ({contract_data['total_texto']})</b>."
        story.append(Paragraph(cond4, styles['Justify']))
        
        cond5 = """5. Lugar y Forma de Pago: Los pagos podrán realizarse mediante las siguientes modalidades:<br/>
        • Pago en Oficina: En el domicilio de EL ACREEDOR, ubicado en Av. Mariscal Cáceres N° 850, Segundo Piso, Huamanga, Ayacucho.<br/>
        • Pago Físico de Cobranza: A través de agentes de cobranza autorizados por EL ACREEDOR.<br/>
        • Pago Virtual: Mediante transferencia bancaria o plataformas de pago electrónico indicadas por EL ACREEDOR, cuyos datos serán proporcionados al momento de la suscripción del contrato."""
        story.append(Paragraph(cond5, styles['Justify']))
        
        cond6 = "6. Comprobantes de Pago: EL ACREEDOR emitirá comprobantes por cada pago recibido, en físico o formato electrónico, según corresponda."
        story.append(Paragraph(cond6, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # V. INCUMPLIMIENTO Y MORA
        story.append(Paragraph("V. INCUMPLIMIENTO Y MORA", styles['Heading3']))
        
        inc1 = f"1. Plazo de Gracia: En caso EL DEUDOR no cancele la totalidad del Capital, intereses y gastos al vencimiento del plazo de 30 días, se otorgará un plazo de gracia de 30 días calendario adicionales para regularizar el pago. Durante este periodo, EL DEUDOR incurrirá en una mora diaria del 0.1% sobre el saldo pendiente, equivalente a <b>S/ {contract_data['mora_diaria']} ({contract_data['mora_texto']})</b> por día, acumulable hasta el cumplimiento total de la obligación o el vencimiento del plazo de gracia."
        story.append(Paragraph(inc1, styles['Justify']))
        
        inc2 = "2. Comunicación Obligatoria: EL DEUDOR deberá comunicar por escrito a EL ACREEDOR cualquier dificultad para cumplir con los pagos o solicitar una ampliación del plazo, acompañada del pago de los intereses y moras correspondientes."
        story.append(Paragraph(inc2, styles['Justify']))
        
        inc3 = """3. Ejecución de la Prenda: Si EL DEUDOR no cancela la totalidad del Capital, intereses, moras y gastos dentro de los 60 días calendario (30 días iniciales más 30 días de gracia), y no se ha comunicado ni solicitado una ampliación, EL ACREEDOR procederá a ejecutar la prenda mediante la venta del bien en remate público, conforme a lo establecido en el Código Civil y la Ley N° 28677. Los fondos obtenidos se destinarán a cubrir:<br/>
        • El Capital adeudado.<br/>
        • Los intereses generados.<br/>
        • Las moras acumuladas.<br/>
        • Los gastos administrativos y costos asociados al remate (notariales, registrales, legales, etc.).<br/>
        Cualquier saldo restante será entregado a EL DEUDOR. Si el producto del remate no cubre la totalidad de la deuda, EL DEUDOR seguirá siendo responsable por el saldo pendiente."""
        story.append(Paragraph(inc3, styles['Justify']))
        
        inc4 = "4. Reporte a Centrales de Riesgo: En caso de incumplimiento, EL DEUDOR será reportado a las centrales de riesgo crediticio, lo que podrá afectar su historial crediticio."
        story.append(Paragraph(inc4, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # VI. OBLIGACIONES DE LAS PARTES
        story.append(Paragraph("VI. OBLIGACIONES DE LAS PARTES", styles['Heading3']))
        
        obl1 = """1. Obligaciones de EL ACREEDOR:<br/>
        • Entregar el Capital a EL DEUDOR en la fecha de suscripción del presente contrato.<br/>
        • Custodiar el bien en prenda en condiciones adecuadas, evitando su deterioro por causas imputables.<br/>
        • Facilitar los medios de pago (oficina, cobranza física o virtual) y emitir comprobantes por cada pago recibido.<br/>
        • Devolver el bien en prenda a EL DEUDOR una vez cumplidas íntegramente las obligaciones de pago."""
        story.append(Paragraph(obl1, styles['Justify']))
        story.append(Spacer(1, 6))
        
        obl2 = """2. Obligaciones de EL DEUDOR:<br/>
        • Pagar puntualmente el Capital, intereses y gastos al vencimiento del plazo.<br/>
        • Entregar el bien en prenda en buen estado y libre de gravámenes.<br/>
        • Informar oportunamente a EL ACREEDOR sobre cualquier dificultad para cumplir con las obligaciones de pago.<br/>
        • Asumir todos los gastos adicionales que se generen por el incumplimiento del presente contrato, incluyendo costos de remate, legales, notariales o registrales."""
        story.append(Paragraph(obl2, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # VII. CLÁUSULAS ADICIONALES
        story.append(Paragraph("VII. CLÁUSULAS ADICIONALES", styles['Heading3']))
        
        adic = """1. Cesión de Derechos: EL ACREEDOR podrá ceder los derechos derivados del presente contrato a terceros, previa notificación escrita a EL DEUDOR.<br/>
        2. Modificaciones: Cualquier modificación al presente contrato deberá realizarse por escrito y contar con la firma de ambas partes.<br/>
        3. Legislación Aplicable: Este contrato se rige por las disposiciones del Código Civil Peruano, la Ley N° 28677 de la Garantía Mobiliaria y demás normas aplicables de la legislación peruana.<br/>
        4. Resolución de Controversias: Las partes acuerdan someter cualquier controversia derivada del presente contrato a la jurisdicción de los juzgados y tribunales de Huamanga, Ayacucho, renunciando a cualquier otro fuero que pudiera corresponderles."""
        story.append(Paragraph(adic, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # VIII. DECLARACIONES
        story.append(Paragraph("VIII. DECLARACIONES", styles['Heading3']))
        decl = """EL DEUDOR declara que:<br/>
        • Es propietario legítimo del bien entregado en prenda y que este se encuentra libre de gravámenes, embargos o cualquier limitación de dominio.<br/>
        • Los fondos recibidos serán utilizados para fines lícitos.<br/>
        • Cuenta con la capacidad económica para cumplir con las obligaciones asumidas en el presente contrato."""
        story.append(Paragraph(decl, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # IX. VIGENCIA
        story.append(Paragraph("IX. VIGENCIA", styles['Heading3']))
        vigencia = "El presente contrato entrará en vigencia a partir de la fecha de su suscripción y permanecerá vigente hasta el cumplimiento total de las obligaciones de EL DEUDOR o la ejecución de la prenda, según corresponda."
        story.append(Paragraph(vigencia, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # Cierre y Firmas (KeepTogether)
        cierre = f"En señal de conformidad, las partes firman el presente contrato en dos ejemplares de igual tenor y valor, en la ciudad de Huamanga, Ayacucho, a los <b>{contract_data['dia']}</b> días del mes de <b>{contract_data['mes']}</b> del año <b>{contract_data['anio']}</b>."
        
        # Table for signatures
        sig_data = [
            ["_____________________________________", "____________________________________"],
            ["Edgar Tucno Pacotaype", f"{contract_data['cliente_nombre']}"],
            ["Gerente General", "EL DEUDOR"],
            ["Corporación El Canguro S.A.C.", ""],
            ["DNI N° 45303843", f"DNI N° {contract_data['cliente_dni']}"]
        ]
        
        sig_table = Table(sig_data, colWidths=[8*cm, 8*cm])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 2),
        ]))
        
        # Keep closure text and signatures together
        signature_block = KeepTogether([
            Paragraph(cierre, styles['Justify']),
            Spacer(1, 30),
            sig_table
        ])
        
        story.append(signature_block)
        
        doc.build(story)
        return filepath

    def generate_rapidiario_contract(self, filepath, contract_data):
        """
        Generates the Rapidiario Contract (Contrato de Préstamo de Dinero con Intereses).
        contract_data: dict with all necessary fields
        """
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
        from reportlab.lib.units import cm
        
        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                rightMargin=2.5*cm, leftMargin=2.5*cm,
                                topMargin=2.5*cm, bottomMargin=2.5*cm)
        
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, fontName='Helvetica', fontSize=10, leading=14))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=12, leading=16))
        styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT, fontName='Helvetica', fontSize=10))
        
        story = []
        
        # Title
        story.append(Paragraph("CONTRATO DE PRESTAMO DE RAPIDIARIO", styles['Center']))
        story.append(Paragraph("CONTRATO DE PRESTAMO DE DINERO CON INTERESES", styles['Center']))
        story.append(Spacer(1, 12))
        
        # Intro
        intro_text = f"En la ciudad de Huamanga, Ayacucho, a los <b>{contract_data['dia']}</b> días del mes de <b>{contract_data['mes']}</b> del año <b>{contract_data['anio']}</b>, se celebra el presente contrato de préstamo de dinero con intereses, entre las partes siguientes:"
        story.append(Paragraph(intro_text, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # I. PARTES CONTRATANTES
        story.append(Paragraph("I. PARTES CONTRATANTES", styles['Heading3']))
        
        part1 = """1. <b>EL ACREEDOR:</b> CORPORACIÓN EL CANGURO S.A.C., inscrita en la Partida Electrónica N° 11191281 del Registro Público de Ayacucho, con RUC N° 20614279924, con domicilio legal en Av. Mariscal Cáceres N° 850, Segundo Piso, Huamanga, Ayacucho, representada por su Gerente General, señor Edgar Tucno Pacotaype, identificado con DNI N° 45303843, con domicilio en Jr. Puno Mz. G Lt. 10, La Florida, Carmen Alto, Ayacucho, quien en adelante será denominado EL ACREEDOR."""
        story.append(Paragraph(part1, styles['Justify']))
        story.append(Spacer(1, 6))
        
        part2 = f"""2. <b>EL DEUDOR:</b> <b>{contract_data['cliente_nombre']}</b>, identificado con DNI N° <b>{contract_data['cliente_dni']}</b>, con domicilio en <b>{contract_data['cliente_direccion']}</b>, quien en adelante será denominado EL DEUDOR."""
        story.append(Paragraph(part2, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # II. OBJETO DEL CONTRATO
        story.append(Paragraph("II. OBJETO DEL CONTRATO", styles['Heading3']))
        objeto = f"""Por el presente contrato, EL ACREEDOR entrega a EL DEUDOR, en calidad de préstamo, la suma de <b>S/ {contract_data['monto_prestamo']} ({contract_data['monto_texto']})</b> (en adelante, "el Capital"), destinada exclusivamente a capital de trabajo para actividades comerciales o de negocio, la cual será devuelta por EL DEUDOR en los términos y condiciones establecidos en este contrato. Las partes declaran expresamente que el presente préstamo no está respaldado por garantías reales ni personales, asumiendo EL DEUDOR la obligación de cumplimiento con base en su compromiso contractual."""
        story.append(Paragraph(objeto, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # III. CONDICIONES DEL PRESTAMO
        story.append(Paragraph("III. CONDICIONES DEL PRESTAMO", styles['Heading3']))
        
        cond1 = f"1. Monto del Préstamo: El Capital asciende a <b>S/ {contract_data['monto_prestamo']} ({contract_data['monto_texto']})</b>."
        story.append(Paragraph(cond1, styles['Justify']))
        
        cond2 = f"2. Tasa de Interés y Gastos: El préstamo devengará una tasa de interés mensual del <b>{contract_data.get('tasa_interes_base', contract_data['tasa_interes'])}%</b> más un <b>2%</b> adicional en concepto de gastos administrativos y otros costos asociados, totalizando un costo financiero efectivo mensual del <b>{contract_data.get('tasa_total', contract_data['tasa_interes'])}%</b>. Asimismo, se incluirá una provisión para cubrir eventuales gastos posteriores que pudieran generarse, tales como costos de cobranza, notariales o legales, los cuales serán asumidos íntegramente por EL DEUDOR."
        story.append(Paragraph(cond2, styles['Justify']))
        
        cond3 = "3. Plazo del Préstamo: El plazo del préstamo será de 30 días calendario, contados a partir de la fecha de desembolso del Capital."
        story.append(Paragraph(cond3, styles['Justify']))
        
        cond4 = f"4. Modalidad de Pago: EL DEUDOR se obliga a realizar pagos diarios, de lunes a sábado, con excepción de los domingos, conforme al cronograma de pagos que se adjunta como Anexo 1 al presente contrato. Cada cuota diaria será de <b>S/ {contract_data['cuota_diaria']}</b> ({contract_data.get('cuota_texto', '')}), e incluirá amortización del Capital, intereses y gastos administrativos."
        story.append(Paragraph(cond4, styles['Justify']))
        
        cond5 = """5. Lugar y Forma de Pago: Los pagos podrán realizarse mediante las siguientes modalidades, a elección de EL DEUDOR:<br/>
        • Pago en Oficina: En el domicilio de EL ACREEDOR, ubicado en Av. Mariscal Cáceres N° 850, Segundo Piso, Huamanga, Ayacucho.<br/>
        • Pago Físico de Cobranza: A través de los agentes de cobranza autorizados por EL ACREEDOR, quienes se presentarán en el domicilio o lugar de negocio de EL DEUDOR.<br/>
        • Pago Virtual: Mediante transferencia bancaria o plataformas de pago electrónico indicadas por EL ACREEDOR, cuyos datos serán proporcionados al momento de la suscripción del contrato."""
        story.append(Paragraph(cond5, styles['Justify']))
        
        cond6 = "6. Comprobantes de Pago: EL ACREEDOR emitirá comprobantes por cada pago recibido, ya sea en físico o en formato electrónico, según corresponda."
        story.append(Paragraph(cond6, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # IV. INCUMPLIMIENTO Y REFINANCIAMIENTO
        story.append(Paragraph("IV. INCUMPLIMIENTO Y REFINANCIAMIENTO", styles['Heading3']))
        
        inc1 = "1. Plazo de Gracia: En caso EL DEUDOR no cancele la totalidad del Capital, intereses y gastos al vencimiento del plazo de 30 días, se otorgará un plazo de gracia de dos (2) días calendario adicionales para regularizar el pago. Durante este periodo, EL DEUDOR deberá comunicar su intención de pago a EL ACREEDOR."
        story.append(Paragraph(inc1, styles['Justify']))
        
        inc2 = f"2. Refinanciamiento Automático: Si EL DEUDOR no efectúa el pago total ni comunica su intención de pago dentro del plazo de gracia, el saldo pendiente será automáticamente refinanciado por un nuevo periodo de 30 días, aplicándose la misma tasa de costo financiero efectivo del <b>{contract_data.get('tasa_total', contract_data['tasa_interes'])}%</b> mensual sobre el saldo pendiente. Este refinanciamiento automático procederá hasta un máximo de tres (3) veces consecutivas."
        story.append(Paragraph(inc2, styles['Justify']))
        
        inc3 = "3. Acciones Legales por Incumplimiento: En caso EL DEUDOR no cumpla con el pago total del Capital, intereses y gastos tras los tres refinanciamientos automáticos, EL ACREEDOR iniciará las acciones legales correspondientes para el cobro de la deuda. Todos los gastos derivados de dichas acciones, incluyendo honorarios legales, costos judiciales, notariales y otros, serán asumidos íntegramente por EL DEUDOR, sumándose al monto adeudado. Asimismo, EL DEUDOR será reportado a las centrales de riesgo crediticio, lo que podrá afectar su historial crediticio."
        story.append(Paragraph(inc3, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # V. OBLIGACIONES DE LAS PARTES
        story.append(Paragraph("V. OBLIGACIONES DE LAS PARTES", styles['Heading3']))
        
        obl1 = """1. Obligaciones de EL ACREEDOR:<br/>
        • Entregar el Capital a EL DEUDOR en la fecha de suscripción del presente contrato.<br/>
        • Proporcionar a EL DEUDOR un cronograma de pagos detallado.<br/>
        • Facilitar los medios de pago (oficina, cobranza física o virtual) y emitir comprobantes por cada pago recibido."""
        story.append(Paragraph(obl1, styles['Justify']))
        story.append(Spacer(1, 6))
        
        obl2 = """2. Obligaciones de EL DEUDOR:<br/>
        • Pagar puntualmente las cuotas diarias conforme al cronograma de pagos.<br/>
        • Informar oportunamente a EL ACREEDOR sobre cualquier dificultad para cumplir con las obligaciones de pago.<br/>
        • Asumir todos los gastos adicionales que se generen por el incumplimiento del presente contrato.<br/>
        • Utilizar el Capital exclusivamente para fines comerciales o de negocio, conforme a lo declarado."""
        story.append(Paragraph(obl2, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # VI. CLAUSULAS ADICIONALES
        story.append(Paragraph("VI. CLAUSULAS ADICIONALES", styles['Heading3']))
        
        adic = """1. Cesión de Derechos: EL ACREEDOR podrá ceder los derechos derivados del presente contrato a terceros, previa notificación escrita a EL DEUDOR.<br/>
        2. Modificaciones: Cualquier modificación al presente contrato deberá realizarse por escrito y contar con la firma de ambas partes.<br/>
        3. Legislación Aplicable: Este contrato se rige por las disposiciones del Código Civil Peruano y demás normas aplicables de la legislación peruana.<br/>
        4. Resolución de Controversias: Las partes acuerdan someter cualquier controversia derivada del presente contrato a la jurisdicción de los juzgados y tribunales de Huamanga, Ayacucho, renunciando a cualquier otro fuero que pudiera corresponderles."""
        story.append(Paragraph(adic, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # VII. DECLARACIONES
        story.append(Paragraph("VII. DECLARACIONES", styles['Heading3']))
        decl = """EL DEUDOR declara que los fondos recibidos serán utilizados exclusivamente para fines lícitos relacionados con actividades comerciales o de negocio y que cuenta con la capacidad económica para cumplir con las obligaciones asumidas en el presente contrato. Asimismo, reconoce que el préstamo no está respaldado por garantías reales ni personales."""
        story.append(Paragraph(decl, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # VIII. VIGENCIA
        story.append(Paragraph("VIII. VIGENCIA", styles['Heading3']))
        vigencia = "El presente contrato entrará en vigencia a partir de la fecha de su suscripción y permanecerá vigente hasta el cumplimiento total de las obligaciones de EL DEUDOR."
        story.append(Paragraph(vigencia, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # Cierre y Firmas (KeepTogether)
        cierre = f"En señal de conformidad, las partes firman el presente contrato en dos ejemplares de igual tenor y valor, en la ciudad de Huamanga, Ayacucho, a los <b>{contract_data['dia']}</b> días del mes de <b>{contract_data['mes']}</b> del año <b>{contract_data['anio']}</b>."
        
        # Firmas
        sig_data = [
            ["_____________________________________", "____________________________________"],
            ["Edgar Tucno Pacotaype", f"{contract_data['cliente_nombre']}"],
            ["Gerente General", "EL DEUDOR"],
            ["Corporación El Canguro S.A.C.", ""],
            ["DNI N° 45303843", f"DNI N° {contract_data['cliente_dni']}"]
        ]
        
        sig_table = Table(sig_data, colWidths=[8*cm, 8*cm])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 2),
        ]))
        
        # Keep closure text and signatures together
        signature_block = KeepTogether([
            Paragraph(cierre, styles['Justify']),
            Spacer(1, 30),
            sig_table
        ])
        
        story.append(signature_block)
        
        doc.build(story)
        return filepath

    def generate_scheduled_pawn_contract(self, filepath, contract_data):
        """
        Generates the Scheduled Pawn Contract (Empeño Programado).
        contract_data: dict with all necessary fields including payment schedule
        """
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
        from reportlab.lib.units import cm
        
        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                rightMargin=2.5*cm, leftMargin=2.5*cm,
                                topMargin=2.5*cm, bottomMargin=2.5*cm)
        
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, fontName='Helvetica', fontSize=10, leading=14))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=12, leading=16))
        styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT, fontName='Helvetica', fontSize=10))
        
        story = []
        
        # Title
        story.append(Paragraph("CONTRATO DE PRESTAMO PRENDARIO PROGRAMADO", styles['Center']))
        story.append(Paragraph("CONTRATO DE PRESTAMO DE DINERO CON GARANTIA PRENDARIA Y PAGO PROGRAMADO", styles['Center']))
        story.append(Spacer(1, 12))
        
        # Intro
        intro_text = f"En la ciudad de Huamanga, Ayacucho, a los <b>{contract_data['dia']}</b> días del mes de <b>{contract_data['mes']}</b> del año <b>{contract_data['anio']}</b>, se celebra el presente contrato de préstamo de dinero con garantía prendaria y pago programado, entre las siguientes partes:"
        story.append(Paragraph(intro_text, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # I. PARTES CONTRATANTES
        story.append(Paragraph("I. PARTES CONTRATANTES", styles['Heading3']))
        
        part1 = """1. <b>EL ACREEDOR:</b> CORPORACIÓN EL CANGURO S.A.C., sociedad anónima cerrada, inscrita en la Partida Electrónica N° 11191281 del Registro Público de Ayacucho, con RUC N° 20614279924, con domicilio legal en Av. Mariscal Cáceres N° 850, Segundo Piso, Huamanga, Ayacucho, representada por su Gerente General, señor Edgar Tucno Pacotaype, identificado con DNI N° 45303843, con domicilio en Jr. Puno Mz. G Lt. 10, La Florida, Carmen Alto, Ayacucho, quien en adelante será denominado EL ACREEDOR."""
        story.append(Paragraph(part1, styles['Justify']))
        story.append(Spacer(1, 6))
        
        part2 = f"""2. <b>EL DEUDOR:</b> <b>{contract_data['cliente_nombre']}</b>, identificado con DNI N° <b>{contract_data['cliente_dni']}</b>, con domicilio en <b>{contract_data['cliente_direccion']}</b>, quien en adelante será denominado EL DEUDOR."""
        story.append(Paragraph(part2, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # II. OBJETO DEL CONTRATO
        story.append(Paragraph("II. OBJETO DEL CONTRATO", styles['Heading3']))
        objeto = f"""Por el presente contrato, EL ACREEDOR entrega a EL DEUDOR, en calidad de préstamo, la suma de <b>S/ {contract_data['monto_prestamo']} ({contract_data['monto_texto']})</b> (en adelante, "el Capital"), la cual será devuelta por EL DEUDOR en los términos y condiciones establecidos en este contrato. Como garantía del cumplimiento de las obligaciones, EL DEUDOR entrega en prenda el bien descrito en la cláusula tercera, conforme a lo dispuesto en el Código Civil Peruano y la Ley N° 28677, Ley de la Garantía Mobiliaria."""
        story.append(Paragraph(objeto, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # III. DESCRIPCIÓN DEL BIEN EN PRENDA
        story.append(Paragraph("III. DESCRIPCION DEL BIEN EN PRENDA", styles['Heading3']))
        story.append(Paragraph("1. Bien en Garantía: EL DEUDOR entrega en prenda a EL ACREEDOR el siguiente bien:", styles['Justify']))
        story.append(Spacer(1, 6))
        
        # Items
        for item in contract_data['items']:
            item_desc = f"• <b>Tipo de bien:</b> {item['tipo']} {item['marca']}<br/>• <b>Descripción:</b> {item['descripcion']}<br/>• <b>Estado:</b> {item['estado']}<br/>• <b>Valor estimado:</b> S/ {item['valor']}, según tasación acordada por las partes."
            story.append(Paragraph(item_desc, styles['Justify']))
            story.append(Spacer(1, 6))
        
        condiciones = """2. Condiciones de la Prenda:<br/>
        • El bien será custodiado por EL ACREEDOR en un lugar seguro designado por este, y EL DEUDOR autoriza su depósito.<br/>
        • EL DEUDOR declara ser propietario legítimo del bien y que este se encuentra libre de gravámenes, embargos o cualquier limitación de dominio.<br/>
        • El bien será devuelto a EL DEUDOR una vez cumplidas íntegramente las obligaciones de pago establecidas en este contrato."""
        story.append(Paragraph(condiciones, styles['Justify']))
        story.append(Spacer(1, 6))
        
        registro = "3. Registro de la Prenda: La prenda será inscrita en el Registro de Garantías Mobiliarias, conforme a la Ley N° 28677, siendo los costos de inscripción asumidos por EL DEUDOR."
        story.append(Paragraph(registro, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # IV. CONDICIONES DEL PRÉSTAMO
        story.append(Paragraph("IV. CONDICIONES DEL PRESTAMO", styles['Heading3']))
        
        cond1 = f"1. Monto del Préstamo: El Capital asciende a <b>S/ {contract_data['monto_prestamo']} ({contract_data['monto_texto']})</b>."
        story.append(Paragraph(cond1, styles['Justify']))
        
        cond2 = f"""2. Tasa de Interés y Gastos: El préstamo devengará una tasa de interés mensual de <b>{contract_data.get('tasa_interes_base', contract_data['tasa_interes'])}%</b>, determinada por el Gerente General de EL ACREEDOR, más un <b>2%</b> adicional en concepto de gastos administrativos y otros costos asociados, totalizando un costo financiero efectivo mensual de <b>{contract_data['tasa_total']}%</b>. El interés mensual a pagar asciende a <b>S/ {contract_data.get('total_interes', '0.00')}</b>. Los gastos adicionales, como costos de custodia, notariales, registrales o legales, serán asumidos íntegramente por EL DEUDOR."""
        story.append(Paragraph(cond2, styles['Justify']))
        
        # Get payment frequency from data
        num_cuotas = contract_data.get('num_cuotas', 1)
        cuota_promedio = contract_data.get('cuota_promedio', contract_data['monto_prestamo'])
        
        if num_cuotas <= 4:
            frecuencia = "semanales"
        elif num_cuotas <= 6:
            frecuencia = "quincenales"
        else:
            frecuencia = "mensuales"
        
        cond3 = f"3. Plazo del Préstamo: El plazo del préstamo será determinado por el cronograma de pagos programado."
        story.append(Paragraph(cond3, styles['Justify']))
        
        cond4 = f"""4. Modalidad de Pago Programado: EL DEUDOR se obliga a realizar pagos <b>{frecuencia}</b>, conforme al cronograma de pagos que se adjunta como Anexo 1 al presente contrato. Cada cuota será de aproximadamente <b>S/ {cuota_promedio}</b>, e incluirá amortización del Capital, intereses y gastos administrativos. El cronograma detalla la distribución de <b>{num_cuotas} cuotas</b>, con un interés acumulado de <b>S/ {contract_data.get('total_interes', '0.00')}</b> para el plazo total."""
        story.append(Paragraph(cond4, styles['Justify']))
        
        cond5 = """5. Lugar y Forma de Pago: Los pagos podrán realizarse mediante las siguientes modalidades:<br/>
        • Pago en Oficina: En el domicilio de EL ACREEDOR, ubicado en Av. Mariscal Cáceres N° 850, Segundo Piso, Huamanga, Ayacucho.<br/>
        • Pago Físico de Cobranza: A través de agentes de cobranza autorizados por EL ACREEDOR.<br/>
        • Pago Virtual: Mediante transferencia bancaria o plataformas de pago electrónico indicadas por EL ACREEDOR, cuyos datos serán proporcionados al momento de la suscripción del contrato."""
        story.append(Paragraph(cond5, styles['Justify']))
        
        cond6 = "6. Comprobantes de Pago: EL ACREEDOR emitirá comprobantes por cada pago recibido, en físico o formato electrónico, según corresponda."
        story.append(Paragraph(cond6, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # V. INCUMPLIMIENTO Y MORA
        story.append(Paragraph("V. INCUMPLIMIENTO Y MORA", styles['Heading3']))
        
        inc1 = f"""1. Mora por Incumplimiento de Cuotas: En caso EL DEUDOR no realice el pago de una cuota en la fecha pactada, incurrirá en una mora diaria del 0.1% sobre el monto del Capital prestado, equivalente a <b>S/ {contract_data.get('mora_diaria', '0.00')} ({contract_data.get('mora_texto', '')})</b> por día de retraso, acumulable hasta el cumplimiento de la obligación o la ejecución de la prenda."""
        story.append(Paragraph(inc1, styles['Justify']))
        
        inc2 = """2. Ejecución de la Prenda por Incumplimiento: Si EL DEUDOR incumple el pago de tres (3) cuotas consecutivas, EL ACREEDOR procederá a ejecutar la prenda mediante la venta del bien en remate público, conforme a lo establecido en el Código Civil y la Ley N° 28677. Los fondos obtenidos se destinarán a cubrir:<br/>
        • El Capital adeudado.<br/>
        • Los intereses generados, incluyendo los intereses acumulados por los meses programados.<br/>
        • Las moras acumuladas.<br/>
        • Los gastos administrativos y costos asociados al remate (notariales, registrales, legales, etc.).<br/>
        Cualquier saldo restante será entregado a EL DEUDOR. Si el producto del remate no cubre la totalidad de la deuda, EL DEUDOR seguirá siendo responsable por el saldo pendiente."""
        story.append(Paragraph(inc2, styles['Justify']))
        
        inc3 = "3. Comunicación Obligatoria: EL DEUDOR deberá comunicar por escrito a EL ACREEDOR cualquier dificultad para cumplir con los pagos o solicitar una reprogramación, acompañada del pago de los intereses y moras correspondientes. La reprogramación estará sujeta a la aprobación de EL ACREEDOR."
        story.append(Paragraph(inc3, styles['Justify']))
        
        inc4 = "4. Reporte a Centrales de Riesgo: En caso de incumplimiento, EL DEUDOR será reportado a las centrales de riesgo crediticio, lo que podrá afectar su historial crediticio."
        story.append(Paragraph(inc4, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # VI. OBLIGACIONES DE LAS PARTES
        story.append(Paragraph("VI. OBLIGACIONES DE LAS PARTES", styles['Heading3']))
        
        obl1 = """1. Obligaciones de EL ACREEDOR:<br/>
        • Entregar el Capital a EL DEUDOR en la fecha de suscripción del presente contrato.<br/>
        • Custodiar el bien en prenda en condiciones adecuadas, evitando su deterioro por causas imputables.<br/>
        • Facilitar los medios de pago (oficina, cobranza física o virtual) y emitir comprobantes por cada pago recibido.<br/>
        • Devolver el bien en prenda a EL DEUDOR una vez cumplidas íntegramente las obligaciones de pago."""
        story.append(Paragraph(obl1, styles['Justify']))
        story.append(Spacer(1, 6))
        
        obl2 = """2. Obligaciones de EL DEUDOR:<br/>
        • Pagar puntualmente las cuotas programadas conforme al cronograma de pagos.<br/>
        • Entregar el bien en prenda en buen estado y libre de gravámenes.<br/>
        • Informar oportunamente a EL ACREEDOR sobre cualquier dificultad para cumplir con las obligaciones de pago.<br/>
        • Asumir todos los gastos adicionales que se generen por el incumplimiento del presente contrato, incluyendo costos de remate, legales, notariales o registrales."""
        story.append(Paragraph(obl2, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # VII. CLÁUSULAS ADICIONALES
        story.append(Paragraph("VII. CLAUSULAS ADICIONALES", styles['Heading3']))
        
        adic = """1. Cesión de Derechos: EL ACREEDOR podrá ceder los derechos derivados del presente contrato a terceros, previa notificación escrita a EL DEUDOR.<br/>
        2. Modificaciones: Cualquier modificación al presente contrato deberá realizarse por escrito y contar con la firma de ambas partes.<br/>
        3. Legislación Aplicable: Este contrato se rige por las disposiciones del Código Civil Peruano, la Ley N° 28677 de la Garantía Mobiliaria y demás normas aplicables de la legislación peruana.<br/>
        4. Resolución de Controversias: Las partes acuerdan someter cualquier controversia derivada del presente contrato a la jurisdicción de los juzgados y tribunales de Huamanga, Ayacucho, renunciando a cualquier otro fuero que pudiera corresponderles."""
        story.append(Paragraph(adic, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # VIII. DECLARACIONES
        story.append(Paragraph("VIII. DECLARACIONES", styles['Heading3']))
        decl = """EL DEUDOR declara que:<br/>
        • Es propietario legítimo del bien entregado en prenda y que este se encuentra libre de gravámenes, embargos o cualquier limitación de dominio.<br/>
        • Los fondos recibidos serán utilizados para fines lícitos.<br/>
        • Cuenta con la capacidad económica para cumplir con las obligaciones asumidas en el presente contrato."""
        story.append(Paragraph(decl, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # IX. VIGENCIA
        story.append(Paragraph("IX. VIGENCIA", styles['Heading3']))
        vigencia = "El presente contrato entrará en vigencia a partir de la fecha de su suscripción y permanecerá vigente hasta el cumplimiento total de las obligaciones de EL DEUDOR o la ejecución de la prenda, según corresponda."
        story.append(Paragraph(vigencia, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # Cierre y Firmas (KeepTogether)
        cierre = f"En señal de conformidad, las partes firman el presente contrato en dos ejemplares de igual tenor y valor, en la ciudad de Huamanga, Ayacucho, a los <b>{contract_data['dia']}</b> días del mes de <b>{contract_data['mes']}</b> del año <b>{contract_data['anio']}</b>."
        
        # Firmas
        sig_data = [
            ["_____________________________________", "____________________________________"],
            ["Edgar Tucno Pacotaype", f"{contract_data['cliente_nombre']}"],
            ["Gerente General", "EL DEUDOR"],
            ["Corporación El Canguro S.A.C.", ""],
            ["DNI N° 45303843", f"DNI N° {contract_data['cliente_dni']}"]
        ]
        
        sig_table = Table(sig_data, colWidths=[8*cm, 8*cm])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 2),
        ]))
        
        # Keep closure text and signatures together
        signature_block = KeepTogether([
            Paragraph(cierre, styles['Justify']),
            Spacer(1, 30),
            sig_table
        ])
        
        story.append(signature_block)
        
        doc.build(story)
        return filepath

    def generate_affidavit(self, filepath, data):
        """
        Generates Affidavit of Property Origin (Declaración Jurada de Procedencia de Bienes).
        data: dict with client info and items
        """
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
        from reportlab.lib.units import cm
        
        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                rightMargin=2.5*cm, leftMargin=2.5*cm,
                                topMargin=2.5*cm, bottomMargin=2.5*cm)
        
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, fontName='Helvetica', fontSize=11, leading=14))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=14, leading=16))
        styles.add(ParagraphStyle(name='Bold', fontName='Helvetica-Bold', fontSize=11))
        
        story = []
        
        # Title
        story.append(Paragraph("DECLARACION JURADA DE PROCEDENCIA DE BIENES EN GARANTIA", styles['Center']))
        story.append(Spacer(1, 20))
        
        # Introduction
        intro = f"Yo, <b>{data['client_name']}</b>, identificado/a con DNI N° <b>{data['client_dni']}</b>, con domicilio en <b>{data['client_address']}</b>, en pleno uso de mis facultades y con carácter de declaración jurada, manifiesto lo siguiente:"
        story.append(Paragraph(intro, styles['Justify']))
        story.append(Spacer(1, 16))
        
        # Bienes en Garantía
        story.append(Paragraph("Bienes en Garantía:", styles['Bold']))
        story.append(Spacer(1, 10))
        
        # List each item - leave blank for manual completion
        # Always show 2 items regardless of how many the loan has
        num_items = 2
        
        for idx in range(1, num_items + 1):
            letter = chr(96 + idx)  # a, b, c, ...
            
            item_header = f"{letter}. Descripción del bien {idx}:"
            story.append(Paragraph(item_header, styles['Bold']))
            story.append(Spacer(1, 6))
            
            # Leave fields blank for client to fill
            details = """Tipo de bien: ______________________________________________________<br/>
            Marca y modelo: ___________________________________________________<br/>
            Número de serie: __________________________________________________<br/>
            Otros detalles: ____________________________________________________"""
            
            story.append(Paragraph(details, styles['Justify']))
            story.append(Spacer(1, 10))
        
        # Procedencia de los Bienes
        story.append(Paragraph("Procedencia de los Bienes:", styles['Bold']))
        story.append(Spacer(1, 8))
        
        procedencia = "Declaro bajo juramento que los bienes descritos anteriormente son de mi legítima propiedad y que no pesan sobre ellos ningún tipo de gravamen, embargo, o situación que limite mi derecho de disposición."
        story.append(Paragraph(procedencia, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # Origen de los Bienes - leave blank for client to fill
        story.append(Paragraph("Origen de los Bienes:", styles['Bold']))
        story.append(Spacer(1, 8))
        
        story.append(Paragraph("Declaro que la procedencia de los bienes es la siguiente:", styles['Justify']))
        story.append(Spacer(1, 8))
        
        for idx in range(1, num_items + 1):
            origen_text = f"Bien {idx}: ____________________________________________________________"
            story.append(Paragraph(origen_text, styles['Justify']))
            story.append(Spacer(1, 6))
        
        story.append(Spacer(1, 12))
        
        # Veracidad de la Información
        story.append(Paragraph("Veracidad de la Información:", styles['Bold']))
        story.append(Spacer(1, 8))
        
        veracidad = "Declaro que toda la información proporcionada en la presente declaración jurada es veraz y fidedigna, y me comprometo a responder por la misma ante cualquier autoridad competente."
        story.append(Paragraph(veracidad, styles['Justify']))
        story.append(Spacer(1, 20))
        
        # Firma y Fecha
        story.append(Paragraph("Firma y Fecha:", styles['Bold']))
        story.append(Spacer(1, 8))
        
        # Get date components
        from datetime import datetime
        now = datetime.now()
        months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", 
                  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        
        firma_text = f"En señal de conformidad, firmo la presente declaración jurada en la ciudad de Ayacucho, a los <b>{now.day}</b> días del mes de <b>{months[now.month-1]}</b> del <b>{now.year}</b>."
        story.append(Paragraph(firma_text, styles['Justify']))
        story.append(Spacer(1, 40))
        
        # Signature line
        sig_line = f"_________________________<br/>DNI N° {data['client_dni']}"
        story.append(Paragraph(sig_line, styles['Center']))
        
        doc.build(story)
        return filepath

    def generate_no_debt_certificate(self, filepath, data):
        """
        Generates No Debt Certificate (Constancia de No Adeudo) for paid pawn loans.
        data: dict with keys: client_name, client_dni, loan_amount, loan_amount_text, 
              collateral_description, collateral_items (list), date
        """
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
        from reportlab.lib.units import cm
        from datetime import datetime
        
        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                rightMargin=2.5*cm, leftMargin=2.5*cm,
                                topMargin=2.5*cm, bottomMargin=2.5*cm)
        
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, fontName='Helvetica', fontSize=11, leading=16))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=13, leading=16))
        styles.add(ParagraphStyle(name='Bold', fontName='Helvetica-Bold', fontSize=11, leading=16))
        
        story = []
        
        # Title
        story.append(Paragraph("CONSTANCIA DE NO ADEUDO", styles['Center']))
        story.append(Paragraph("PRESTAMO CON GARANTIA PRENDARIA", styles['Center']))
        story.append(Spacer(1, 20))
        
        # Get date components
        date_obj = data.get('date', datetime.now())
        if isinstance(date_obj, str):
            date_obj = datetime.now()
        
        months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", 
                  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        
        dia = date_obj.day
        mes = months[date_obj.month - 1]
        anio = date_obj.year
        
        # Introduction
        intro = f"""En la ciudad de Ayacucho, a los <b>{dia}</b> días del mes de <b>{mes}</b> del año <b>{anio}</b>, la empresa <b>CORPORACION EL CANGURO S.A.C.</b>, inscrita en la Partida Electrónica N° <b>11191281</b> del Registro Público de Ayacucho, con RUC N° <b>20614279924</b>, con domicilio legal en <b>Av. Mariscal Cáceres N° 850, Segundo Piso, Huamanga, Ayacucho</b>, representada por su Gerente General, señor <b>Edgar Tucno Pacotaype</b>, identificado con DNI N° <b>45303843</b>, con domicilio en <b>Jr. Puno Mz. G Lt. 10, La Florida, Carmen Alto, Ayacucho</b>,"""
        story.append(Paragraph(intro, styles['Justify']))
        story.append(Spacer(1, 14))
        
        # HACE CONSTAR QUE
        story.append(Paragraph("HACE CONSTAR QUE:", styles['Bold']))
        story.append(Spacer(1, 12))
        
        # Client and loan details
        content = f"""El señor(a) <b>{data['client_name']}</b>, identificado con DNI N° <b>{data['client_dni']}</b>, contrajo con nuestra empresa un préstamo por la suma de <b>S/. {data['loan_amount']:.2f} ({data['loan_amount_text']})</b>, dejando como garantía prendaria: <b>{data['collateral_description']}</b> con las siguientes características:"""
        story.append(Paragraph(content, styles['Justify']))
        story.append(Spacer(1, 10))
        
        # List collateral items
        for item in data.get('collateral_items', []):
            story.append(Paragraph(f"• {item}", styles['Justify']))
            story.append(Spacer(1, 4))
        
        story.append(Spacer(1, 12))
        
        # Payment declaration
        payment_decl = """A la fecha, el cliente ha cancelado en su totalidad la deuda contraída, no manteniendo obligación pendiente alguna con CORPORACION EL CANGURO S.A.C. por dicho concepto."""
        story.append(Paragraph(payment_decl, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # Conclusion
        conclusion = """En consecuencia, la empresa otorga la presente Constancia de No Adeudo, liberando la garantía prendaria mencionada y quedando el cliente en pleno derecho de disponer del bien."""
        story.append(Paragraph(conclusion, styles['Justify']))
        story.append(Spacer(1, 12))
        
        # Purpose
        purpose = """Se expide la presente para los fines que el interesado estime convenientes."""
        story.append(Paragraph(purpose, styles['Justify']))
        story.append(Spacer(1, 40))
        
        # Signatures
        sig_data = [
            ["_____________________________", "_____________________________"],
            ["", ""],
            ["Edgar Tucno Pacotaype", ""],
            ["Gerente General", ""],
            ["DNI N° 45303843", f"DNI N° {data['client_dni']}"],
            ["CORPORACION EL CANGURO S.A.C.", ""]
        ]
        
        sig_table = Table(sig_data, colWidths=[8*cm, 8*cm])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        
        story.append(sig_table)
        
        doc.build(story)
        return filepath



def generate_payment_schedule(filepath, loan_data, client_data, installments, pawn_data=None):
    """
    Generates a professional PDF for payment schedules with company branding
    """
    from utils.settings_manager import get_setting
    
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    
    # Get company settings
    company_name = get_setting('company_name') or "Mi Empresa"
    company_ruc = get_setting('company_ruc') or "---"
    company_address = get_setting('company_address') or "Dirección"
    company_phone = get_setting('company_phone') or "999 999 999"
    company_phone2 = get_setting('company_phone2') or ""
    manager_phone = get_setting('manager_phone') or ""
    
    # Header with company branding (Blue background)
    c.setFillColor(colors.HexColor('#2196F3'))
    c.rect(0, height - 3*cm, width, 3*cm, fill=True, stroke=False)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height - 1.5*cm, company_name)
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height - 2.2*cm, f"RUC: {company_ruc}")
    
    # Reset to black for body
    c.setFillColor(colors.black)
    
    y = height - 4*cm
    
    # Title
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2, y, "CRONOGRAMA DE PAGOS")
    y -= 1*cm
    
    # Client and Loan Information Box
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor('#2196F3'))
    c.drawString(2*cm, y, "DATOS DEL PRÉSTAMO")
    c.setFillColor(colors.black)
    y -= 0.6*cm
    
    c.setFont("Helvetica", 10)
    info_lines = [
        f"Cliente: {client_data['first_name']} {client_data['last_name']}",
        f"DNI: {client_data['dni']}",
        f"Préstamo ID: {loan_data['id']} - Tipo: {loan_data['loan_type'].capitalize()}",
        f"Monto Prestado: S/ {loan_data['amount']:.2f}",
        f"Tasa de Interés: {loan_data['interest_rate']}%",
        f"Fecha de Emisión: {datetime.now().strftime('%d/%m/%Y')}"
    ]
    
    for line in info_lines:
        c.drawString(2.5*cm, y, line)
        y -= 0.5*cm
    
    y -= 0.5*cm
    
    # Pawn Details (if applicable)
    if pawn_data and len(pawn_data) > 0:
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor('#2196F3'))
        c.drawString(2*cm, y, "GARANTÍAS PRENDARIAS")
        c.setFillColor(colors.black)
        y -= 0.6*cm
        
        c.setFont("Helvetica", 9)
        for item in pawn_data:
            desc = f"• {item['item_type']} {item['brand']} - {item['characteristics']}"
            c.drawString(2.5*cm, y, desc)
            y -= 0.4*cm
        
        y -= 0.5*cm
    
    # Payment Schedule Table
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor('#2196F3'))
    c.drawString(2*cm, y, "CRONOGRAMA DE CUOTAS")
    c.setFillColor(colors.black)
    y -= 0.8*cm
    
    # Table headers
    table_data = [['N°', 'Fecha Vencimiento', 'Monto (S/)', 'Estado', 'Fecha Pago']]
    
    # Table rows
    total_amount = 0
    status_map = {'pending': 'Pendiente', 'paid': 'Pagado', 'partial': 'Parcial', 'overdue': 'Vencido'}
    
    for inst in installments:
        status = status_map.get(inst['status'], inst['status'])
        payment_date = inst['payment_date'] if inst['payment_date'] else '-'
        
        table_data.append([
            str(inst['number']),
            inst['due_date'],
            f"S/ {inst['amount']:.2f}",
            status,
            payment_date
        ])
        total_amount += inst['amount']
    
    # Add total row
    table_data.append(['', '', '', 'TOTAL:', f"S/ {total_amount:.2f}"])
    
    # Create table
    table = Table(table_data, colWidths=[1.5*cm, 3.5*cm, 3*cm, 3*cm, 3.5*cm])
    
    # Style the table
    style = TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2196F3')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Data rows
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 9),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ('ALIGN', (3, 1), (3, -1), 'CENTER'),
        ('ALIGN', (4, 1), (4, -1), 'CENTER'),
        
        # Total row
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('ALIGN', (3, -1), (3, -1), 'RIGHT'),
        ('ALIGN', (4, -1), (4, -1), 'RIGHT'),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ])
    
    # Color code status
    for i, inst in enumerate(installments, start=1):
        if inst['status'] == 'paid':
            style.add('BACKGROUND', (3, i), (3, i), colors.HexColor('#C8E6C9'))
        elif inst['status'] == 'overdue':
            style.add('BACKGROUND', (3, i), (3, i), colors.HexColor('#FFCDD2'))
        elif inst['status'] == 'partial':
            style.add('BACKGROUND', (3, i), (3, i), colors.HexColor('#FFF9C4'))
    
    table.setStyle(style)
    
    # Draw table
    table.wrapOn(c, width, height)
    table_height = table._height
    table.drawOn(c, 2*cm, y - table_height)
    
    y = y - table_height - 1.5*cm
    
    # Get analyst information
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
            if analyst_row['role'] == 'admin':
                analyst_name = get_setting('company_manager') or analyst_row['analyst_name'] or 'Gerente General'
                analyst_phone = manager_phone or analyst_row['analyst_phone'] or '999 999 999'
            else:
                analyst_name = analyst_row['analyst_name'] or 'Analista'
                analyst_phone = analyst_row['analyst_phone'] or '999 999 999'
    
    # Footer
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.grey)
    
    phones = company_phone
    if company_phone2:
        phones += f" / {company_phone2}"
    
    c.drawCentredString(width/2, y, f"{company_address} | Tel: {phones}")
    y -= 0.4*cm
    c.drawCentredString(width/2, y, f"Analista: {analyst_name} | Tel: {analyst_phone}")
    
    c.save()
    return filepath


def generate_payment_receipt(filepath, payment_data, client_data, loan_data, user_data):
    """
    Generates a professional payment receipt PDF
    
    payment_data: dict with 'transaction_id', 'amount', 'payment_method', 'date'
    client_data: dict with client information
    loan_data: dict with loan information
    user_data: dict with cashier/user information
    """
    from utils.settings_manager import get_setting
    
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    
    # Get company settings
    company_name = get_setting('company_name') or "Mi Empresa"
    company_ruc = get_setting('company_ruc') or "---"
    company_address = get_setting('company_address') or "Dirección"
    company_phone = get_setting('company_phone') or "999 999 999"
    company_phone2 = get_setting('company_phone2') or ""
    
    # Header with company branding (Blue background)
    c.setFillColor(colors.HexColor('#2196F3'))
    c.rect(0, height - 3.5*cm, width, 3.5*cm, fill=True, stroke=False)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(width/2, height - 1.5*cm, company_name)
    c.setFont("Helvetica", 11)
    c.drawCentredString(width/2, height - 2.2*cm, f"RUC: {company_ruc}")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, height - 2.8*cm, f"{company_address}")
    
    # Reset to black for body
    c.setFillColor(colors.black)
    
    y = height - 4.5*cm
    
    # Receipt Title
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, y, "RECIBO DE PAGO")
    y -= 0.8*cm
    
    # Receipt Number and Date
    c.setFont("Helvetica", 10)
    receipt_number = f"REC-{payment_data['transaction_id']:06d}"
    c.drawString(2*cm, y, f"Recibo N°: {receipt_number}")
    c.drawRightString(width - 2*cm, y, f"Fecha: {payment_data['date']}")
    y -= 1*cm
    
    # Client Information Box
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor('#2196F3'))
    c.drawString(2*cm, y, "DATOS DEL CLIENTE")
    c.setFillColor(colors.black)
    y -= 0.6*cm
    
    c.setFont("Helvetica", 11)
    client_info = [
        f"Nombre: {client_data['first_name']} {client_data['last_name']}",
        f"DNI: {client_data['dni']}"
    ]
    
    for line in client_info:
        c.drawString(2.5*cm, y, line)
        y -= 0.5*cm
    
    y -= 0.5*cm
    
    # Loan Information Box
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor('#2196F3'))
    c.drawString(2*cm, y, "DATOS DEL PRÉSTAMO")
    c.setFillColor(colors.black)
    y -= 0.6*cm
    
    c.setFont("Helvetica", 11)
    loan_info = [
        f"Préstamo ID: {loan_data['id']}",
        f"Tipo: {loan_data['loan_type'].capitalize()}",
        f"Monto Original: S/ {loan_data['amount']:.2f}"
    ]
    
    for line in loan_info:
        c.drawString(2.5*cm, y, line)
        y -= 0.5*cm
    
    y -= 0.8*cm
    
    # Payment Details Box (Highlighted)
    box_height = 3*cm
    c.setFillColor(colors.HexColor('#E3F2FD'))
    c.rect(2*cm, y - box_height, width - 4*cm, box_height, fill=True, stroke=True)
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2.5*cm, y - 0.7*cm, "DETALLES DEL PAGO")
    
    c.setFont("Helvetica", 12)
    c.drawString(2.5*cm, y - 1.5*cm, f"Monto Pagado:")
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.HexColor('#4CAF50'))
    c.drawString(7*cm, y - 1.5*cm, f"S/ {payment_data['amount']:.2f}")
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 12)
    c.drawString(2.5*cm, y - 2.3*cm, f"Concepto:")
    c.setFont("Helvetica", 10)
    # Truncate description if too long
    desc = payment_data.get('description', 'Pago de Préstamo')
    if len(desc) > 45: desc = desc[:42] + "..."
    c.drawString(7*cm, y - 2.3*cm, desc)

    c.setFont("Helvetica", 12)
    c.drawString(2.5*cm, y - 3.1*cm, f"Método de Pago:")
    c.setFont("Helvetica-Bold", 12)
    method_display = {
        'efectivo': 'Efectivo',
        'yape': 'Yape',
        'deposito': 'Depósito Bancario'
    }
    c.drawString(7*cm, y - 3.1*cm, method_display.get(payment_data['payment_method'], payment_data['payment_method']))
    
    y -= box_height + 1*cm
    
    # Cashier Information
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.grey)
    cashier_name = user_data.get('full_name') or user_data.get('username', 'Cajero')
    c.drawString(2*cm, y, f"Atendido por: {cashier_name}")
    y -= 1.5*cm
    
    # Signature line
    c.setFillColor(colors.black)
    c.line(2*cm, y, 8*cm, y)
    y -= 0.4*cm
    c.setFont("Helvetica", 9)
    c.drawString(2*cm, y, "Firma del Cliente")
    
    # Footer
    y = 3*cm
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.grey)
    
    phones = company_phone
    if company_phone2:
        phones += f" / {company_phone2}"
    
    c.drawCentredString(width/2, y, f"Tel: {phones}")
    y -= 0.4*cm
    # Watermark
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.lightgrey)
    c.drawCentredString(width/2, 1*cm, f"Recibo generado electrónicamente - {receipt_number}")
    
    c.save()
    return filepath


    def generate_scheduled_pawn_contract(self, filepath, contract_data):
        """
        Generates the Scheduled Pawn Contract (Empeño Programado).
        """
        # Reuse Pawn Contract logic but with different title and clauses
        # For brevity, we'll copy the structure but change the title
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
        from reportlab.lib.units import cm
        
        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                rightMargin=2.5*cm, leftMargin=2.5*cm,
                                topMargin=2.5*cm, bottomMargin=2.5*cm)
        
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, fontName='Helvetica', fontSize=10, leading=14))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=12, leading=16))
        
        story = []
        
        story.append(Paragraph("CONTRATO DE CREDITO PRENDARIO PROGRAMADO", styles['Center']))
        story.append(Spacer(1, 12))
        
        # Intro
        intro_text = f"En la ciudad de Huamanga, Ayacucho, a los <b>{contract_data['dia']}</b> días del mes de <b>{contract_data['mes']}</b> del año <b>{contract_data['anio']}</b>, se celebra el presente contrato entre:"
        story.append(Paragraph(intro_text, styles['Justify']))
        story.append(Spacer(1, 12))
        
        part1 = """1. <b>EL ACREEDOR:</b> CORPORACIÓN EL CANGURO S.A.C., con RUC N° 20614279924."""
        story.append(Paragraph(part1, styles['Justify']))
        
        part2 = f"""2. <b>EL DEUDOR:</b> <b>{contract_data['cliente_nombre']}</b>, con DNI N° <b>{contract_data['cliente_dni']}</b>, domiciliado en <b>{contract_data['cliente_direccion']}</b>."""
        story.append(Paragraph(part2, styles['Justify']))
        story.append(Spacer(1, 12))
        
        story.append(Paragraph("CLAUSULAS:", styles['Heading3']))
        
        clauses = [
            f"PRIMERA: EL ACREEDOR otorga un préstamo de <b>S/ {contract_data['monto_prestamo']} ({contract_data['monto_texto']})</b>.",
            f"SEGUNDA: El préstamo devengará un interés compensatorio del <b>{contract_data.get('tasa_interes_base', contract_data['tasa_interes'])}%</b> y gastos administrativos del <b>2%</b>, totalizando <b>{contract_data.get('tasa_total', contract_data['tasa_interes'])}%</b>.",
            f"TERCERA: EL DEUDOR entrega en garantía prendaria los siguientes bienes:",
        ]
        
        for clause in clauses:
            story.append(Paragraph(clause, styles['Justify']))
            story.append(Spacer(1, 6))
            
        # Items
        for item in contract_data['items']:
            item_desc = f"• <b>{item['tipo']} {item['marca']}</b>: <b>{item['descripcion']}</b>. Estado: <b>{item['estado']}</b>."
            story.append(Paragraph(item_desc, styles['Justify'], bulletText="•"))
        story.append(Spacer(1, 6))
        
        clause4 = f"CUARTA: El pago se realizará de forma PROGRAMADA según el cronograma acordado, siendo el total a pagar de <b>S/ {contract_data['total_pagar']} ({contract_data['total_texto']})</b>."
        story.append(Paragraph(clause4, styles['Justify']))
        story.append(Spacer(1, 30))
        
        # Signatures
        sig_data = [
            ["_______________________", "_______________________"],
            ["EL ACREEDOR", "EL DEUDOR"],
            ["Corporación El Canguro", f"{contract_data['cliente_nombre']}"]
        ]
        sig_table = Table(sig_data, colWidths=[8*cm, 8*cm])
        
        # Keep signatures together
        signature_block = KeepTogether([
            sig_table
        ])
        
        story.append(signature_block)
        
        doc.build(story)
        return filepath

    def generate_notification(self, filepath, data):
        """
        Generates a Notification Letter.
        data: type, client_name, client_address, loan_id, amount, date
        """
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
        from reportlab.lib.units import cm
        
        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                rightMargin=2.5*cm, leftMargin=2.5*cm,
                                topMargin=2.5*cm, bottomMargin=2.5*cm)
        
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, fontName='Helvetica', fontSize=11, leading=14))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=14, leading=16))
        
        story = []
        
        # Header
        story.append(Paragraph(data['type'].upper(), styles['Center']))
        story.append(Spacer(1, 24))
        
        # Date
        story.append(Paragraph(f"Ayacucho, {data['date']}", styles['Justify']))
        story.append(Spacer(1, 12))
        
        # Client Info
        story.append(Paragraph(f"Señor(a):<br/><b>{data['client_name']}</b><br/>{data['client_address']}", styles['Justify']))
        story.append(Spacer(1, 24))
        
        # Body
        story.append(Paragraph("De nuestra mayor consideración:", styles['Justify']))
        story.append(Spacer(1, 12))
        
        body = ""
        if data['type'] == "Cobranza Preventiva":
            body = f"Por medio de la presente, le recordamos cordialmente que su crédito N° {data['loan_id']} mantiene un saldo pendiente. Le invitamos a acercarse a nuestras oficinas para regularizar su situación y evitar mayores gastos."
        elif data['type'] == "Aviso de Vencimiento":
            body = f"Le informamos que su crédito N° {data['loan_id']} ha vencido. El monto pendiente es de S/ {data['amount']:.2f}. Agradeceremos realizar el pago a la brevedad posible."
        elif data['type'] == "Notificación de Mora":
            body = f"Nos dirigimos a usted para informarle que su crédito N° {data['loan_id']} se encuentra en situación de MORA. Esto está generando intereses adicionales diarios. Le instamos a cancelar la deuda inmediatamente."
        elif data['type'] == "Ultimo Aviso antes de Remate":
            body = f"Habiendo agotado las gestiones de cobranza previas, le comunicamos que tiene un plazo de 48 horas para cancelar su deuda de S/ {data['amount']:.2f}. De lo contrario, procederemos al REMATE de la garantía prendaria conforme a ley."
        elif data['type'] == "Notificación Pre-Judicial":
            body = f"Ante su incumplimiento reiterado en el pago del crédito N° {data['loan_id']}, le notificamos que su expediente está siendo derivado a nuestra área legal para el inicio de las acciones judiciales correspondientes, lo cual incrementará su deuda con costos y costas procesales."
            
        story.append(Paragraph(body, styles['Justify']))
        story.append(Spacer(1, 24))
        
        story.append(Paragraph("Atentamente,", styles['Justify']))
        story.append(Spacer(1, 36))
        
        story.append(Paragraph("__________________________<br/>AREA DE COBRANZAS<br/>CORPORACIÓN EL CANGURO S.A.C.", styles['Center']))
        
        doc.build(story)
        return filepath

    def generate_affidavit(self, filepath, data):
        """
        Generates Affidavit of Lawful Origin (Declaración Jurada).
        """
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
        from reportlab.lib.units import cm
        
        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                rightMargin=2.5*cm, leftMargin=2.5*cm,
                                topMargin=2.5*cm, bottomMargin=2.5*cm)
        
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, fontName='Helvetica', fontSize=11, leading=14))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=14, leading=16))
        
        story = []
        
        story.append(Paragraph("DECLARACIÓN JURADA DE PROCEDENCIA LÍCITA", styles['Center']))
        story.append(Spacer(1, 24))
        
        text = f"Yo, <b>{data['client_name']}</b>, identificado con DNI N° {data['client_dni']}, con domicilio en {data['client_address']}, en pleno uso de mis facultades, DECLARO BAJO JURAMENTO:"
        story.append(Paragraph(text, styles['Justify']))
        story.append(Spacer(1, 12))
        
        story.append(Paragraph("1. Que soy propietario(a) legítimo(a) de los siguientes bienes muebles:", styles['Justify']))
        story.append(Spacer(1, 6))
        
        for item in data['items']:
            item_desc = f"• {item['item_type']} {item['brand']}: {item['description']}"
            story.append(Paragraph(item_desc, styles['Justify'], bulletText="•"))
        story.append(Spacer(1, 12))
        
        text2 = "2. Que dichos bienes tienen procedencia lícita y no están sujetos a ningún gravamen, embargo, ni proceso judicial o administrativo pendiente."
        story.append(Paragraph(text2, styles['Justify']))
        story.append(Spacer(1, 6))
        
        text3 = "3. Que asumo total responsabilidad civil y penal en caso de que esta declaración resulte falsa, liberando a CORPORACIÓN EL CANGURO S.A.C. de toda responsabilidad."
        story.append(Paragraph(text3, styles['Justify']))
        story.append(Spacer(1, 24))
        
        story.append(Paragraph(f"Huamanga, {data['date']}", styles['Justify']))
        story.append(Spacer(1, 48))
        
        # Signature
        story.append(Paragraph("__________________________<br/>Firma del Declarante<br/>DNI: " + data['client_dni'], styles['Center']))
        
        doc.build(story)
        return filepath

def generate_detailed_payment_receipt(filepath, payment_data, client_data, loan_data, user_data, extra_info=None):
    """
    Generates a detailed Payment Receipt PDF.
    extra_info: dict with keys 'total_debt', 'total_paid', 'remaining_balance', 'next_payment_date', 'final_due_date'
    """
    from reportlab.lib.pagesizes import A5
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle
    
    c = canvas.Canvas(filepath, pagesize=A5)
    width, height = A5
    
    # --- Header ---
    c.setFillColor(colors.HexColor('#4285F4')) # Google Blue roughly
    c.rect(0, height - 2.5*cm, width, 2.5*cm, fill=True, stroke=False)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 1.0*cm, "CORPORACION EL CANGURO S.A.C.")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, height - 1.5*cm, "RUC: 20614279924")
    c.drawCentredString(width/2, height - 1.9*cm, "Av. MARISCAL CASERES 850")
    
    # --- Title ---
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height - 3.5*cm, "RECIBO DE PAGO")
    
    # --- Receipt Details ---
    c.setFont("Helvetica", 9)
    c.drawString(1.5*cm, height - 4.2*cm, f"Recibo N°: REC-{payment_data.get('transaction_id', '???')}")
    c.drawRightString(width - 1.5*cm, height - 4.2*cm, f"Fecha: {payment_data.get('date', '')}")
    
    y = height - 5.0*cm
    
    # --- Client Data ---
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor('#4285F4'))
    c.drawString(1.5*cm, y, "DATOS DEL CLIENTE")
    c.setFillColor(colors.black)
    y -= 0.5*cm
    
    c.setFont("Helvetica", 9)
    c.drawString(2*cm, y, f"Nombre: {client_data.get('first_name', '')} {client_data.get('last_name', '')}")
    y -= 0.4*cm
    c.drawString(2*cm, y, f"DNI: {client_data.get('dni', '')}")
    y -= 0.8*cm
    
    # --- Loan Data ---
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor('#4285F4'))
    c.drawString(1.5*cm, y, "DATOS DEL PRÉSTAMO")
    c.setFillColor(colors.black)
    y -= 0.5*cm
    
    c.setFont("Helvetica", 9)
    c.drawString(2*cm, y, f"Préstamo ID: {loan_data.get('id', '')}")
    y -= 0.4*cm
    loan_type_map = {'rapid': 'Rapidiario', 'rapidiario': 'Rapidiario', 'empeno': 'Empeño', 'bancario': 'Bancario'}
    loan_type = loan_type_map.get(loan_data.get('loan_type', ''), loan_data.get('loan_type', '').capitalize())
    c.drawString(2*cm, y, f"Tipo: {loan_type}")
    y -= 0.4*cm
    c.drawString(2*cm, y, f"Monto Original: S/ {loan_data.get('amount', 0):.2f}")
    y -= 0.8*cm

    # --- Payment Details Box ---
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    
    # Details Table
    details_data = [
        ['DETALLES DEL PAGO', ''],
        ['Monto Pagado:', f"S/ {payment_data.get('amount', 0):.2f}"],
        ['Concepto:', payment_data.get('description', '')],
        ['Método de Pago:', payment_data.get('payment_method', '').capitalize()]
    ]
    
    t = Table(details_data, colWidths=[4*cm, 7*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E3F2FD')), # Header bg
        ('SPAN', (0,0), (-1,0)), # Span header
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        
        ('FONTNAME', (0,1), (0,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('ALIGN', (0,1), (0,-1), 'LEFT'),
        
        ('FONTNAME', (1,1), (1,1), 'Helvetica-Bold'), # Amount bold
        ('TEXTCOLOR', (1,1), (1,1), colors.HexColor('#4CAF50')), # Green amount
        ('FONTSIZE', (1,1), (1,1), 12),
        
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    
    t_w, t_h = t.wrapOn(c, width, height)
    t.drawOn(c, (width - t_w)/2, y - t_h)
    
    y = y - t_h - 1.0*cm
    
    # --- Debt Summary Section (Requested Features) ---
    if extra_info:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(1.5*cm, y, "ESTADO DE CUENTA:")
        y -= 0.6*cm
        
        # Summary Data
        summary_data = [
            # Header Row
            ['Deuda Total', 'Total Pagado', 'SALDO PENDIENTE'],
            # Value Row
            [f"S/ {extra_info.get('total_debt', 0):.2f}", 
             f"S/ {extra_info.get('total_paid', 0):.2f}",
             f"S/ {extra_info.get('remaining_balance', 0):.2f}"]
        ]
        
        sum_table = Table(summary_data, colWidths=[3.5*cm, 3.5*cm, 3.5*cm])
        sum_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 8),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('TEXTCOLOR', (2,0), (2,1), colors.red), # Pending red
            ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
        ]))
        st_w, st_h = sum_table.wrapOn(c, width, height)
        sum_table.drawOn(c, (width - st_w)/2, y - st_h)
        
        y = y - st_h - 0.8*cm
        
        # Dates
        c.setFont("Helvetica", 8)
        if extra_info.get('next_payment_date'):
            c.drawString(1.5*cm, y, f"Próxima Fecha de Pago: {extra_info['next_payment_date']}")
        
        if extra_info.get('final_due_date'):
            c.drawRightString(width - 1.5*cm, y, f"Vencimiento Final: {extra_info['final_due_date']}")
            
        y -= 0.6*cm

    # --- Footer ---
    y = 2.0*cm
    c.setLineWidth(0.5)
    c.line(1.5*cm, y, 6.5*cm, y)
    c.setFont("Helvetica", 7)
    c.drawCentredString(4.0*cm, y - 0.3*cm, "Firma del Cliente")
    
    c.line(width - 6.5*cm, y, width - 1.5*cm, y)
    c.drawCentredString(width - 4.0*cm, y - 0.3*cm, f"Atendido por: {user_data.get('username', 'Cajero')}")
    
    c.drawCentredString(width/2, 0.8*cm, "¡Gracias por su puntualidad!")
    
    c.save()
    return filepath



