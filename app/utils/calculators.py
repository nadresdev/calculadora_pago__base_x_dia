from datetime import time, datetime
from typing import Dict, Any
import logging

from app.config.settings import settings

logger = logging.getLogger(__name__)

def calculate_worked_hours(entrada: time, salida: time, fecha) -> Dict[str, Any]:
    """
    Calcula horas trabajadas y información relacionada
    
    Returns:
        Dict con horas, minutos y total en decimal
    """
    try:
        entrada_dt = datetime.combine(fecha, entrada)
        salida_dt = datetime.combine(fecha, salida)
        
        diferencia = salida_dt - entrada_dt
        total_segundos = diferencia.total_seconds()
        
        horas = int(total_segundos // 3600)
        minutos = int((total_segundos % 3600) // 60)
        total_horas = total_segundos / 3600
        
        return {
            "horas": horas,
            "minutos": minutos,
            "total_horas": total_horas,
            "horas_formateadas": f"{horas:02d}:{minutos:02d}"
        }
        
    except Exception as e:
        logger.error(f"Error calculando horas trabajadas: {e}")
        raise

def calculate_payment(horas_trabajadas: float) -> Dict[str, float]:
    """
    Calcula el pago según las reglas de negocio
    
    Returns:
        Dict con pago_base y detalles del cálculo
    """
    try:
        tolerancia = settings.TOLERANCIA_MINUTOS / 60
        
        if horas_trabajadas < 6 - tolerancia:
            pago_base = horas_trabajadas * settings.VALOR_HORA
            tipo_calculo = "horas_normales"
            
        elif abs(horas_trabajadas - 6) <= tolerancia:
            pago_base = settings.BONO_6H
            tipo_calculo = "bono_6h"
            
        else:
            horas_extra = horas_trabajadas - 6
            pago_base = settings.BONO_6H + (horas_extra * settings.VALOR_HORA)
            tipo_calculo = "horas_extra"
        
        return {
            "pago_base": pago_base,
            "tipo_calculo": tipo_calculo,
            "valor_hora": settings.VALOR_HORA,
            "bono_6h": settings.BONO_6H
        }
        
    except Exception as e:
        logger.error(f"Error calculando pago: {e}")
        raise