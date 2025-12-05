
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from utils.pdf_generator import PDFGenerator

def test_contracts():
    generator = PDFGenerator()
    
    # Dummy data
    contract_data = {
        'dia': '04',
        'mes': 'Diciembre',
        'anio': '2025',
        'cliente_nombre': 'Juan Perez',
        'cliente_dni': '12345678',
        'cliente_direccion': 'Av. Siempre Viva 123',
        'cliente_ocupacion': 'Comerciante',
        'monto_prestamo': '1000.00',
        'monto_texto': 'MIL CON 00/100 SOLES',
        'tasa_interes': '5',
        'tasa_interes_base': '3',
        'tasa_total': '5',
        'interes_monto': '50.00',
        'interes_texto': 'CINCUENTA CON 00/100 SOLES',
        'total_pagar': '1050.00',
        'total_texto': 'MIL CINCUENTA CON 00/100 SOLES',
        'mora_diaria': '1.00',
        'mora_texto': 'UN SOL',
        'cuota_diaria': '45.00',
        'dias_plazo': '24',
        'items': [
            {
                'tipo': 'Laptop',
                'marca': 'Dell',
                'descripcion': 'Core i7 16GB RAM',
                'estado': 'Bueno',
                'valor': '1500.00'
            }
        ]
    }
    
    print("Generating Pawn Contract...")
    try:
        generator.generate_pawn_contract('test_pawn.pdf', contract_data)
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")

    print("Generating Rapidiario Contract...")
    try:
        generator.generate_rapidiario_contract('test_rapidiario.pdf', contract_data)
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")

    print("Generating Scheduled Pawn Contract...")
    try:
        generator.generate_scheduled_pawn_contract('test_scheduled.pdf', contract_data)
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_contracts()
