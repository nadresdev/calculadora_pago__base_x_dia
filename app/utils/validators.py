from datetime import time, date
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Excepción personalizada para errores de validación"""
    pass

def validate_schedule(entrada: time, salida: time, fecha: date) -> Tuple[bool, Optional[str]]:
    """
    Valida que los horarios sean correctos
    
    Returns:
        Tuple[bool, Optional[str]]: (es_válido, mensaje_error)
    """
    try:
        # Validar horarios cruzados
        if salida <= entrada:
            return False, "❌ La hora de salida debe ser posterior a la hora de entrada"
        
        # Validar duración máxima del turno
        from datetime import datetime
        entrada_dt = datetime.combine(fecha, entrada)
        salida_dt = datetime.combine(fecha, salida)
        
        diferencia = salida_dt - entrada_dt
        horas_trabajadas = diferencia.total_seconds() / 3600
        
        if horas_trabajadas > 16:
            return False, "❌ El turno no puede ser mayor a 16 horas"
        
        if horas_trabajadas <= 0:
            return False, "❌ La duración del turno debe ser positiva"
            
        return True, None
        
    except Exception as e:
        logger.error(f"Error en validación de horarios: {e}")
        return False, "❌ Error validando los horarios"

def validate_future_date(selected_date: date) -> Tuple[bool, Optional[str]]:
    """Valida que la fecha no sea futura"""
    from datetime import date as today_date
    
    if selected_date > today_date.today():
        return False, "❌ No se pueden registrar horarios para fechas futuras"
    
    return True, None