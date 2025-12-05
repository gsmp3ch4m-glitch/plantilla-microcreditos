import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from src.utils.pdf_generator import PDFGenerator
    
    print("Testing PDF Generation for Simulation...")
    
    generator = PDFGenerator()
    filename = "test_simulation.pdf"
    filepath = os.path.join(generator.reports_dir, filename)
    
    # Mock Data
    sim_data = {
        'monto': 1000.00,
        'tasa': 10.0,
        'tipo': 'rapidiario',
        'fecha_inicio': datetime.now(),
        'total_interes': 200.00,
        'total_pagar': 1200.00
    }
    
    schedule = [
        (1, datetime.now(), 100.00),
        (2, datetime.now(), 100.00),
        (3, datetime.now(), 100.00)
    ]
    
    path = generator.generate_simulation_report(filepath, sim_data, schedule)
    
    if os.path.exists(path):
        print(f"SUCCESS: PDF created at {path}")
        print(f"Size: {os.path.getsize(path)} bytes")
    else:
        print("FAILURE: PDF file not found.")
        
except Exception as e:
    print(f"FAILURE: Error during PDF generation: {e}")
    import traceback
    traceback.print_exc()
