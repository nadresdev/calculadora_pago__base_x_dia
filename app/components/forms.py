import streamlit as st
from datetime import date, time
from typing import Tuple, Optional, Dict, Any

from app.config.settings import settings
from app.utils.validators import validate_schedule, validate_future_date

def render_schedule_form() -> Optional[Dict[str, Any]]:
    """
    Renderiza el formulario de registro y retorna los datos validados
    
    Returns:
        Dict con los datos del formulario o None si hay errores
    """
    st.subheader("📝 Nuevo Registro de Horario")
    
    # Selección de fecha
    fecha = st.date_input(
        "Selecciona la fecha:",
        value=date.today(),
        help="Selecciona la fecha del turno trabajado"
    )
    
    # Validación de fecha
    is_valid_date, date_error = validate_future_date(fecha)
    if not is_valid_date:
        st.error(date_error)
        return None
    
    # Selección de horarios
    col1, col2 = st.columns(2)
    with col1:
        hora_entrada = st.time_input(
            "Hora de Entrada 🏢",
            value=time(8, 0),
            help="Hora a la que comenzaste tu turno"
        )
    with col2:
        hora_salida = st.time_input(
            "Hora de Salida 🏠", 
            value=time(17, 0),
            help="Hora a la que finalizaste tu turno"
        )
    
    # Validación de horarios
    is_valid_schedule, schedule_error = validate_schedule(hora_entrada, hora_salida, fecha)
    if not is_valid_schedule:
        st.error(schedule_error)
        return None
    
    # Selección de recargo
    recargo = st.selectbox(
        "Recargo adicional:",
        options=settings.RECARGOS,
        format_func=lambda x: f"$ {x:,}" if x else "Sin recargo",
        help="Recargo adicional por condiciones especiales de trabajo"
    )
    
    return {
        "fecha": fecha,
        "hora_entrada": hora_entrada,
        "hora_salida": hora_salida,
        "recargo": recargo
    }

def render_results(calculation_data: Dict[str, Any]) -> None:
    """Renderiza los resultados del cálculo"""
    st.subheader("💰 Resumen de Pago")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Horas Trabajadas",
            value=calculation_data["horas_formateadas"],
            help="Total de horas trabajadas en el turno"
        )
    
    with col2:
        st.metric(
            label="Pago Base",
            value=f"$ {calculation_data['pago_base']:,.0f}",
            help="Pago calculado según horas trabajadas"
        )
    
    with col3:
        st.metric(
            label="Pago Total",
            value=f"$ {calculation_data['pago_total']:,.0f}",
            delta=f"$ {calculation_data['recargo']:,.0f}" if calculation_data['recargo'] > 0 else None,
            delta_color="off",
            help="Pago base más recargos adicionales"
        )