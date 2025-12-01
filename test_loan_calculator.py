"""
Script de prueba para el módulo de cálculo de préstamos
"""
from datetime import date
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.loan_calculator import (
    calcular_cuota_rapidiario,
    calcular_cuota_empeno,
    calcular_cuota_bancario,
    calcular_dias_laborables
)

print("=" * 60)
print("PRUEBAS DE CÁLCULO DE PRÉSTAMOS")
print("=" * 60)

# Test 1: Rapidiario
print("\n1. RAPIDIARIO - Préstamo de S/ 1000 al 5% (inicio: Lunes 2 Dic 2025)")
print("-" * 60)
fecha_inicio = date(2025, 12, 2)  # Martes
resultado = calcular_cuota_rapidiario(1000, 5, fecha_inicio, 'Diario')
print(f"   Fecha inicio: {fecha_inicio.strftime('%d/%m/%Y')} ({['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'][fecha_inicio.weekday()]})")
print(f"   Fecha vencimiento: {resultado['fecha_vencimiento'].strftime('%d/%m/%Y')}")
print(f"   Días laborables: {resultado['dias_laborables']} días")
print(f"   Total interés: S/ {resultado['total_interes']:.2f}")
print(f"   Total a pagar: S/ {resultado['total_pagar']:.2f}")
print(f"   Número de cuotas: {len(resultado['cuotas'])}")
print(f"   Monto por cuota: S/ {resultado['cuotas'][0][2]:.2f}")

# Test 2: Rapidiario iniciando Viernes
print("\n2. RAPIDIARIO - Préstamo de S/ 1000 al 5% (inicio: Viernes 5 Dic 2025)")
print("-" * 60)
fecha_inicio_viernes = date(2025, 12, 5)  # Viernes
resultado_viernes = calcular_cuota_rapidiario(1000, 5, fecha_inicio_viernes, 'Diario')
print(f"   Fecha inicio: {fecha_inicio_viernes.strftime('%d/%m/%Y')} ({['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'][fecha_inicio_viernes.weekday()]})")
print(f"   Días laborables: {resultado_viernes['dias_laborables']} días (debería ser ~25)")
print(f"   Total a pagar: S/ {resultado_viernes['total_pagar']:.2f}")
print(f"   Monto por cuota: S/ {resultado_viernes['cuotas'][0][2]:.2f}")

# Test 3: Casa de Empeño
print("\n3. CASA DE EMPEÑO - Préstamo de S/ 2000 al 5% (inicio: 15 Ene 2025)")
print("-" * 60)
fecha_empeno = date(2025, 1, 15)
resultado_empeno = calcular_cuota_empeno(2000, 5, fecha_empeno)
print(f"   Fecha inicio: {fecha_empeno.strftime('%d/%m/%Y')}")
print(f"   Fecha vencimiento: {resultado_empeno['fecha_vencimiento'].strftime('%d/%m/%Y')} (debe ser 15/02/2025)")
print(f"   Total interés: S/ {resultado_empeno['total_interes']:.2f}")
print(f"   Total a pagar: S/ {resultado_empeno['total_pagar']:.2f}")
print(f"   Número de cuotas: {len(resultado_empeno['cuotas'])}")

# Test 4: Préstamo Bancario
print("\n4. PRÉSTAMO BANCARIO - S/ 1000 a 3 meses (inicio: 1 Dic 2025)")
print("-" * 60)
fecha_bancario = date(2025, 12, 1)
resultado_bancario = calcular_cuota_bancario(1000, 3, fecha_bancario)
print(f"   Fecha inicio: {fecha_bancario.strftime('%d/%m/%Y')}")
print(f"   Tasa mensual: {resultado_bancario['tasa_mensual']:.2f}% (base 10% + incremento)")
print(f"   Total interés: S/ {resultado_bancario['total_interes']:.2f}")
print(f"   Total a pagar: S/ {resultado_bancario['total_pagar']:.2f}")
print(f"   Número de cuotas: {len(resultado_bancario['cuotas'])}")
print(f"   Monto por cuota: S/ {resultado_bancario['cuotas'][0][2]:.2f}")
print(f"   Capital por cuota: S/ {resultado_bancario['capital_por_cuota']:.2f}")
print(f"   Interés por cuota: S/ {resultado_bancario['interes_por_cuota']:.2f}")

# Test 5: Préstamo Bancario a 6 meses (mayor interés)
print("\n5. PRÉSTAMO BANCARIO - S/ 1000 a 6 meses (inicio: 1 Dic 2025)")
print("-" * 60)
resultado_bancario_6 = calcular_cuota_bancario(1000, 6, fecha_bancario)
print(f"   Tasa mensual: {resultado_bancario_6['tasa_mensual']:.2f}% (aumenta con plazo)")
print(f"   Total interés: S/ {resultado_bancario_6['total_interes']:.2f}")
print(f"   Total a pagar: S/ {resultado_bancario_6['total_pagar']:.2f}")
print(f"   Monto por cuota: S/ {resultado_bancario_6['cuotas'][0][2]:.2f}")

print("\n" + "=" * 60)
print("TODAS LAS PRUEBAS COMPLETADAS")
print("=" * 60)
