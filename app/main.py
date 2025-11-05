import streamlit as st
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importaciones de la aplicación
from app.config.settings import settings
from app.services.google_sheets import sheets_service
from app.components.banner import banner_reglas
from app.components.forms import render_schedule_form, render_results
from app.components.dashboard import render_historical_data
from app.utils.calculators import calculate_worked_hours, calculate_payment

def main():
    """Función principal de la aplicación"""
    
    # 1. Configuración de página (SIEMPRE primero)
    st.set_page_config(
        page_title=settings.APP_TITLE,
        page_icon="🕒",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 2. Banner con reglas
    banner_reglas()
    
    # 3. Título principal
    st.title("🕒 Registro de Horarios")
    
    try:
        # 4. Formulario de registro
        form_data = render_schedule_form()
        
        if form_data:
            # 5. Cálculos
            hours_data = calculate_worked_hours(
                form_data["hora_entrada"],
                form_data["hora_salida"],
                form_data["fecha"]
            )
            
            payment_data = calculate_payment(hours_data["total_horas"])
            
            # 6. Preparar datos para mostrar
            calculation_result = {
                **hours_data,
                **payment_data,
                "recargo": form_data["recargo"],
                "pago_total": payment_data["pago_base"] + form_data["recargo"]
            }
            
            # 7. Mostrar resultados
            render_results(calculation_result)
            
            # 8. Botón de guardado
            if st.button("💾 Guardar Registro", type="primary", use_container_width=True):
                # Preparar datos para guardar
                record_data = {
                    "fecha": str(form_data["fecha"]),
                    "hora_entrada": form_data["hora_entrada"].strftime("%I:%M %p"),
                    "hora_salida": form_data["hora_salida"].strftime("%I:%M %p"),
                    "recargo": form_data["recargo"],
                    "horas_trabajadas": calculation_result["horas_formateadas"],
                    "pago_base": f"$ {payment_data['pago_base']:,.0f}",
                    "pago_total": f"$ {calculation_result['pago_total']:,.0f}"
                }
                
                # Guardar en Google Sheets
                if sheets_service.append_record(record_data):
                    st.success("✅ Registro guardado correctamente!")
                    st.balloons()
                else:
                    st.error("❌ Error al guardar el registro")
        
        # 9. Historial
        st.markdown("---")
        if st.checkbox("📊 Mostrar historial de registros"):
            records = sheets_service.get_all_records()
            render_historical_data(records)
            
    except Exception as e:
        logger.error(f"Error en la aplicación: {e}")
        st.error("🚨 Ocurrió un error inesperado. Por favor, recarga la página.")

if __name__ == "__main__":
    main()