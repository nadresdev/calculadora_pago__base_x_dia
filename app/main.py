import streamlit as st
import logging
import pandas as pd

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Verificar dependencias
try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    logger.warning("openpyxl no está instalado. La exportación a Excel no estará disponible.")

# Importaciones de la aplicación
try:
    from app.config.settings import settings
    from app.services.google_sheets import sheets_service
    from app.components.banner import banner_reglas
    from app.components.forms import render_schedule_form, render_results
    from app.components.dashboard import render_historical_data, render_weekly_summary
    from app.utils.calculators import calculate_worked_hours, calculate_payment
except ImportError as e:
    logger.error(f"Error en importaciones: {e}")
    st.error(f"Error de configuración: {e}")
    st.stop()

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
    
    # Advertencia si openpyxl no está disponible
    if not OPENPYXL_AVAILABLE:
        st.warning("⚠️ El módulo 'openpyxl' no está instalado. La exportación a Excel no estará disponible. Ejecuta: `pip install openpyxl`")
    
    try:
        # Obtener registros una sola vez para reutilizar
        records = sheets_service.get_all_records()
        
        # 4. Resumen semanal en sidebar
        render_weekly_summary(records)
        
        # 5. Formulario de registro
        form_data = render_schedule_form()
        
        if form_data:
            # 6. Cálculos
            hours_data = calculate_worked_hours(
                form_data["hora_entrada"],
                form_data["hora_salida"],
                form_data["fecha"]
            )
            
            payment_data = calculate_payment(hours_data["total_horas"])
            
            # 7. Preparar datos para mostrar
            calculation_result = {
                **hours_data,
                **payment_data,
                "recargo": form_data["recargo"],
                "pago_total": payment_data["pago_base"] + form_data["recargo"]
            }
            
            # 8. Mostrar resultados
            render_results(calculation_result)
            
            # 9. Botón de guardado
            if st.button("💾 Guardar Registro", type="primary", width='stretch'):
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
                    # Actualizar los registros después de guardar
                    records = sheets_service.get_all_records()
                else:
                    st.error("❌ Error al guardar el registro")
        
        # 10. Historial con pestañas
        st.markdown("---")
        st.header("📊 Historial de Registros")
        
        # Crear pestañas para diferentes vistas
        tab1, tab2 = st.tabs(["📅 Registros por Semana", "📋 Todos los Registros"])
        
        with tab1:
            # Vista de registros por semana con filtros
            render_historical_data(records)
        
        with tab2:
            # Vista de todos los registros
            if records:
                df_all = pd.DataFrame(records)
                
                # Mostrar estadísticas generales
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Registros", len(df_all))
                with col2:
                    try:
                        total_general = sum(
                            float(str(pago).replace('$', '').replace(',', '').strip()) 
                            for pago in df_all['Pago con Recargo'] 
                            if pago and str(pago).strip()
                        )
                        st.metric("Total General", f"$ {total_general:,.0f}")
                    except:
                        st.metric("Total General", "N/A")
                with col3:
                    st.metric("Valor Hora", f"$ {settings.VALOR_HORA:,.0f}")
                
                # Mostrar tabla completa
                st.dataframe(df_all, use_container_width=True, hide_index=True)
                
                # Botones de descarga para todos los registros
                st.subheader("💾 Descargar Todos los Registros")
                col1, col2 = st.columns(2)
                
                with col1:
                    # Descargar CSV
                    csv_all = df_all.to_csv(index=False)
                    st.download_button(
                        label="📥 Descargar CSV Completo",
                        data=csv_all,
                        file_name="todos_los_registros.csv",
                        mime="text/csv",
                        width='stretch'
                    )
                
                with col2:
                    # Descargar Excel (solo si openpyxl está disponible)
                    if OPENPYXL_AVAILABLE:
                        try:
                            from app.components.dashboard import create_excel_download
                            import datetime
                            excel_all = create_excel_download(df_all, datetime.date.min, datetime.date.max)
                            st.download_button(
                                label="📊 Descargar Excel Completo",
                                data=excel_all,
                                file_name="todos_los_registros.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                width='stretch'
                            )
                        except Exception as e:
                            st.error(f"Error al generar Excel: {e}")
                    else:
                        st.button(
                            "📊 Descargar Excel (No disponible)",
                            disabled=True,
                            help="Instala openpyxl: pip install openpyxl",
                            width='stretch'
                        )
            else:
                st.info("No hay registros disponibles")
            
    except Exception as e:
        logger.error(f"Error en la aplicación: {e}")
        st.error("🚨 Ocurrió un error inesperado. Por favor, recarga la página.")

if __name__ == "__main__":
    main()