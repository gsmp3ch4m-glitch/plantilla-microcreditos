import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.pdf_generator import PDFGenerator
from utils.number_to_text import numero_a_letras
from datetime import datetime

def test_contract_generation():
    print("Initializing PDFGenerator...")
    generator = PDFGenerator()
    
    # Simulate Data
    contract_data = {
        'dia': 3,
        'mes': 'Diciembre',
        'anio': 2025,
        'cliente_nombre': 'Juan Perez',
        'cliente_dni': '12345678',
        'cliente_direccion': 'Av. Los Libertadores 123',
        'monto_prestamo': '1,000.00',
        'monto_texto': numero_a_letras(1000.00),
        'tasa_interes': 5.0,
        'tasa_total': 7.0,
        'interes_monto': '50.00',
        'interes_texto': numero_a_letras(50.00),
        'total_pagar': '1,070.00',
        'total_texto': numero_a_letras(1070.00),
        'mora_diaria': '1.07',
        'mora_texto': numero_a_letras(1.07),
        'items': [
            {
                'tipo': 'Laptop',
                'marca': 'HP',
                'descripcion': 'Modelo Pavilion 15, Core i5',
                'estado': 'Bueno',
                'valor': '1,500.00'
            },
            {
                'tipo': 'Celular',
                'marca': 'Samsung',
                'descripcion': 'Galaxy S21, 128GB',
                'estado': 'Regular',
                'valor': '800.00'
            }
        ]
    }
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_contrato_{timestamp}.pdf"
    filepath = os.path.join(generator.reports_dir, filename)
    
    print(f"Generating contract at {filepath}...")
    try:
        path = generator.generate_pawn_contract(filepath, contract_data)
        print(f"Contract generated successfully: {path}")
        os.startfile(path)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_contract_generation()
