"""
Módulo de Cálculo de Préstamos
Contiene la lógica de cálculo para los tres tipos de préstamos:
- Rapidiario: 30 días excluyendo domingos
- Casa de Empeño: 1 mes calendario
- Préstamo Bancario: Cuotas mensuales con interés progresivo
"""

from datetime import datetime, timedelta, date
import calendar


def calcular_dias_laborables(fecha_inicio, dias_totales=30):
    """
    Calcula cuántos días laborables hay excluyendo domingos.
    
    Args:
        fecha_inicio: Fecha de inicio del préstamo (datetime.date)
        dias_totales: Número total de días del período (default: 30)
    
    Returns:
        int: Número de días laborables (excluyendo domingos)
    """
    dias_laborables = 0
    fecha_actual = fecha_inicio
    
    for i in range(dias_totales):
        # 6 = Domingo en Python (0=Lunes, 6=Domingo)
        if fecha_actual.weekday() != 6:
            dias_laborables += 1
        fecha_actual += timedelta(days=1)
    
    return dias_laborables


def calcular_vencimiento_rapidiario(fecha_inicio):
    """
    Calcula la fecha de vencimiento para Rapidiario (30 días después).
    
    Args:
        fecha_inicio: Fecha de inicio del préstamo
    
    Returns:
        tuple: (fecha_vencimiento, dias_laborables)
    """
    fecha_vencimiento = fecha_inicio + timedelta(days=30)
    dias_laborables = calcular_dias_laborables(fecha_inicio, 30)
    
    return fecha_vencimiento, dias_laborables


def calcular_vencimiento_empeno(fecha_inicio):
    """
    Calcula la fecha de vencimiento para Casa de Empeño.
    Retorna la misma fecha del mes siguiente.
    Maneja casos especiales (ej: 31 de enero → 28/29 de febrero)
    
    Args:
        fecha_inicio: Fecha de inicio del préstamo
    
    Returns:
        date: Fecha de vencimiento (mismo día del mes siguiente)
    """
    mes_siguiente = fecha_inicio.month + 1
    año = fecha_inicio.year
    
    if mes_siguiente > 12:
        mes_siguiente = 1
        año += 1
    
    # Manejar días que no existen en el mes siguiente
    try:
        fecha_vencimiento = fecha_inicio.replace(month=mes_siguiente, year=año)
    except ValueError:
        # Si el día no existe, usar el último día del mes
        ultimo_dia = calendar.monthrange(año, mes_siguiente)[1]
        fecha_vencimiento = fecha_inicio.replace(day=ultimo_dia, month=mes_siguiente, year=año)
    
    return fecha_vencimiento


def calcular_tasa_bancario(meses, tasa_base=10.0, incremento=1.0):
    """
    Calcula la tasa de interés mensual para préstamo bancario.
    La tasa aumenta con el plazo.
    
    Args:
        meses: Número de meses del préstamo
        tasa_base: Tasa base mensual (default: 10%)
        incremento: Incremento por mes adicional (default: 1%)
    
    Returns:
        float: Tasa de interés mensual en porcentaje
    """
    tasa_mensual = tasa_base + (incremento * max(0, meses - 1))
    return tasa_mensual


def calcular_cuota_rapidiario(monto, tasa_interes, fecha_inicio, frecuencia='Diario'):
    """
    Calcula las cuotas para Rapidiario.
    
    Args:
        monto: Monto del préstamo
        tasa_interes: Tasa de interés total (%)
        fecha_inicio: Fecha de inicio
        frecuencia: 'Diario' o 'Semanal'
    
    Returns:
        dict: {
            'total_interes': float,
            'total_pagar': float,
            'cuotas': [(numero, fecha, monto), ...],
            'dias_laborables': int
        }
    """
    import math
    
    fecha_vencimiento, dias_laborables = calcular_vencimiento_rapidiario(fecha_inicio)
    
    # Calcular interés total
    total_interes = monto * (tasa_interes / 100)
    total_pagar = monto + total_interes
    
    cuotas = []
    
    if frecuencia == 'Diario':
        # Dividir entre días laborables solamente
        monto_por_cuota_exacto = total_pagar / dias_laborables
        
        # Redondear hacia arriba a múltiplos de 0.10
        monto_por_cuota = math.ceil(monto_por_cuota_exacto * 10) / 10
        
        fecha_actual = fecha_inicio
        numero_cuota = 1
        
        for i in range(30):
            fecha_actual = fecha_inicio + timedelta(days=i+1)
            # Solo agregar cuota si no es domingo
            if fecha_actual.weekday() != 6:
                cuotas.append((numero_cuota, fecha_actual, monto_por_cuota))
                numero_cuota += 1
        
        # Ajustar última cuota para que el total sea exacto
        if cuotas:
            total_cuotas = sum(c[2] for c in cuotas)
            diferencia = total_pagar - total_cuotas
            ultima_cuota = list(cuotas[-1])
            ultima_cuota[2] = ultima_cuota[2] + diferencia
            cuotas[-1] = tuple(ultima_cuota)
            
    elif frecuencia == 'Semanal':
        # Pago semanal (cada 7 días)
        num_cuotas = 4  # Aproximadamente 4 semanas en 30 días
        monto_por_cuota_exacto = total_pagar / num_cuotas
        
        # Redondear hacia arriba a múltiplos de 0.10
        monto_por_cuota = math.ceil(monto_por_cuota_exacto * 10) / 10
        
        for i in range(1, num_cuotas + 1):
            fecha_cuota = fecha_inicio + timedelta(weeks=i)
            cuotas.append((i, fecha_cuota, monto_por_cuota))
        
        # Ajustar última cuota
        if cuotas:
            total_cuotas = sum(c[2] for c in cuotas)
            diferencia = total_pagar - total_cuotas
            ultima_cuota = list(cuotas[-1])
            ultima_cuota[2] = ultima_cuota[2] + diferencia
            cuotas[-1] = tuple(ultima_cuota)
    
    return {
        'total_interes': total_interes,
        'total_pagar': total_pagar,
        'cuotas': cuotas,
        'dias_laborables': dias_laborables,
        'fecha_vencimiento': fecha_vencimiento
    }


def calcular_cuota_empeno(monto, tasa_interes, fecha_inicio):
    """
    Calcula la cuota para Casa de Empeño (pago único al mes siguiente).
    
    Args:
        monto: Monto del préstamo
        tasa_interes: Tasa de interés mensual (%)
        fecha_inicio: Fecha de inicio
    
    Returns:
        dict: {
            'total_interes': float,
            'total_pagar': float,
            'cuotas': [(1, fecha_vencimiento, total)],
            'fecha_vencimiento': date
        }
    """
    import math
    
    fecha_vencimiento = calcular_vencimiento_empeno(fecha_inicio)
    
    # Interés simple mensual
    total_interes = monto * (tasa_interes / 100)
    total_pagar = monto + total_interes
    
    # Redondear el pago total a múltiplos de 0.10
    total_pagar_redondeado = math.ceil(total_pagar * 10) / 10
    
    cuotas = [(1, fecha_vencimiento, total_pagar_redondeado)]
    
    return {
        'total_interes': total_interes,
        'total_pagar': total_pagar_redondeado,
        'cuotas': cuotas,
        'fecha_vencimiento': fecha_vencimiento
    }


def calcular_cuota_bancario(monto, meses, fecha_inicio, tasa_mensual=10.0):
    """
    Calcula las cuotas para Préstamo Bancario Programado.
    El interés es mensual y se aplica sobre el monto total cada mes.
    
    Args:
        monto: Monto del préstamo
        meses: Número de meses
        fecha_inicio: Fecha de inicio
        tasa_mensual: Tasa de interés mensual (%) - la que ingresa el usuario
    
    Returns:
        dict: {
            'tasa_mensual': float,
            'total_interes': float,
            'total_pagar': float,
            'cuotas': [(numero, fecha, monto), ...],
        }
    """
    import math
    
    # La tasa mensual es la que el usuario ingresó
    # No se incrementa, se aplica tal cual cada mes
    
    # Calcular capital por cuota
    capital_por_cuota = monto / meses
    
    # Calcular interés mensual (se aplica sobre el monto total cada mes)
    interes_mensual = monto * (tasa_mensual / 100)
    
    # Total por cuota (capital + interés) - SIN REDONDEAR AÚN
    monto_por_cuota_exacto = capital_por_cuota + interes_mensual
    
    # Redondear hacia arriba a múltiplos de 0.10
    monto_por_cuota = math.ceil(monto_por_cuota_exacto * 10) / 10
    
    # Total a pagar
    total_interes = interes_mensual * meses
    total_pagar = monto + total_interes
    
    # Generar cuotas
    cuotas = []
    for i in range(1, meses + 1):
        # Calcular fecha de vencimiento (mismo día cada mes)
        mes_cuota = fecha_inicio.month + i
        año_cuota = fecha_inicio.year
        
        while mes_cuota > 12:
            mes_cuota -= 12
            año_cuota += 1
        
        try:
            fecha_cuota = fecha_inicio.replace(month=mes_cuota, year=año_cuota)
        except ValueError:
            # Manejar días que no existen
            ultimo_dia = calendar.monthrange(año_cuota, mes_cuota)[1]
            fecha_cuota = fecha_inicio.replace(day=ultimo_dia, month=mes_cuota, year=año_cuota)
        
        cuotas.append((i, fecha_cuota, monto_por_cuota))
    
    # Ajustar última cuota para que el total sea exacto
    if cuotas:
        total_cuotas = sum(c[2] for c in cuotas)
        diferencia = total_pagar - total_cuotas
        ultima_cuota = list(cuotas[-1])
        ultima_cuota[2] = ultima_cuota[2] + diferencia
        cuotas[-1] = tuple(ultima_cuota)
    
    return {
        'tasa_mensual': tasa_mensual,
        'total_interes': total_interes,
        'total_pagar': total_pagar,
        'cuotas': cuotas,
        'capital_por_cuota': capital_por_cuota,
        'interes_por_cuota': interes_mensual
    }


def obtener_info_prestamo(tipo_prestamo, monto, tasa_interes, fecha_inicio, **kwargs):
    """
    Función unificada para obtener información de cualquier tipo de préstamo.
    
    Args:
        tipo_prestamo: 'rapidiario', 'empeno', o 'bancario'
        monto: Monto del préstamo
        tasa_interes: Tasa de interés (%)
        fecha_inicio: Fecha de inicio (datetime.date)
        **kwargs: Parámetros adicionales según el tipo
            - frecuencia: Para rapidiario ('Diario' o 'Semanal')
            - meses: Para bancario (número de meses)
    
    Returns:
        dict: Información completa del préstamo
    """
    if tipo_prestamo == 'rapidiario':
        frecuencia = kwargs.get('frecuencia', 'Diario')
        return calcular_cuota_rapidiario(monto, tasa_interes, fecha_inicio, frecuencia)
    
    elif tipo_prestamo == 'empeno':
        return calcular_cuota_empeno(monto, tasa_interes, fecha_inicio)
    
    elif tipo_prestamo == 'bancario':
        meses = kwargs.get('meses', 3)
        # Usar la tasa de interés que ingresó el usuario como tasa mensual
        return calcular_cuota_bancario(monto, meses, fecha_inicio, tasa_interes)
    
    else:
        raise ValueError(f"Tipo de préstamo no válido: {tipo_prestamo}")
