# app/utils/date_utils.py
import datetime
from typing import Tuple, List
import pandas as pd

def get_week_range(date: datetime.date = None) -> Tuple[datetime.date, datetime.date]:
    """
    Obtiene el rango de una semana (lunes a domingo) para una fecha dada.
    Si no se proporciona fecha, usa la fecha actual.
    """
    if date is None:
        date = datetime.date.today()
    
    # Encontrar el lunes de la semana
    start_date = date - datetime.timedelta(days=date.weekday())
    # El domingo de la semana
    end_date = start_date + datetime.timedelta(days=6)
    
    return start_date, end_date

def get_week_number(date: datetime.date) -> int:
    """Obtiene el número de semana del año"""
    return date.isocalendar()[1]

def get_weeks_range(year: int = None) -> List[Tuple[datetime.date, datetime.date, str]]:
    """
    Obtiene todas las semanas de un año con sus rangos y etiquetas
    """
    if year is None:
        year = datetime.date.today().year
    
    weeks = []
    # Empezar desde el primer lunes del año
    start_date = datetime.date(year, 1, 1)
    # Ajustar al primer lunes
    start_date = start_date + datetime.timedelta(days=(0 - start_date.weekday()))
    
    for week in range(53):  # Máximo 53 semanas en un año
        week_start = start_date + datetime.timedelta(weeks=week)
        week_end = week_start + datetime.timedelta(days=6)
        
        # Si la semana empieza en el año siguiente, terminar
        if week_start.year > year:
            break
            
        label = f"Semana {week + 1} ({week_start.strftime('%d/%m')} - {week_end.strftime('%d/%m')})"
        weeks.append((week_start, week_end, label))
    
    return weeks

def filter_records_by_week(records: List[dict], start_date: datetime.date, end_date: datetime.date) -> List[dict]:
    """
    Filtra registros por rango de fechas
    """
    filtered = []
    for record in records:
        try:
            record_date = datetime.datetime.strptime(record['Fecha'], '%Y-%m-%d').date()
            if start_date <= record_date <= end_date:
                filtered.append(record)
        except (ValueError, KeyError):
            continue
    return filtered