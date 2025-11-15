import streamlit as st
import pandas as pd
import datetime
from typing import List, Dict
import io

from app.config.settings import settings
from app.utils.date_utils import get_week_range, get_weeks_range, filter_records_by_week

def render_week_selector() -> tuple:
    """
    Renderiza el selector de semana y retorna (start_date, end_date)
    """
    st.subheader("📅 Seleccionar Semana")
    
    # Obtener semana actual por defecto
    current_start, current_end = get_week_range()
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Selector de fecha para navegar por semanas
        selected_date = st.date_input(
            "Selecciona una fecha para ver su semana:",
            value=datetime.date.today(),
            help="Se mostrarán los registros de la semana (lunes a domingo) de esta fecha"
        )
    
    with col2:
        # También ofrecer selector directo de semanas del año
        current_year = datetime.date.today().year
        weeks = get_weeks_range(current_year)
        week_options = [week[2] for week in weeks]
        
        # Encontrar la semana actual
        current_week_index = 0
        for i, (start, end, label) in enumerate(weeks):
            if start <= datetime.date.today() <= end:
                current_week_index = i
                break
        
        selected_week_label = st.selectbox(
            "Semana del año:",
            options=week_options,
            index=current_week_index
        )
        
        # Obtener las fechas de la semana seleccionada
        selected_week_index = week_options.index(selected_week_label)
        selected_start, selected_end, _ = weeks[selected_week_index]
    
    with col3:
        # Mostrar rango de la semana seleccionada
        st.metric(
            "Semana seleccionada",
            f"{selected_start.strftime('%d/%m')} - {selected_end.strftime('%d/%m')}"
        )
    
    return selected_start, selected_end

def create_excel_download(df: pd.DataFrame, week_start: datetime.date, week_end: datetime.date) -> bytes:
    """
    Crea un archivo Excel para descargar
    """
    try:
        # Verificar openpyxl
        import openpyxl
    except ImportError:
        raise ImportError("openpyxl no está instalado. Ejecuta: pip install openpyxl")
    
    try:
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja principal con los datos
            df.to_excel(writer, sheet_name='Registros', index=False)
            
            # Hoja de resumen
            total_registros = len(df)
            try:
                total_pagado = df['Pago_Numerico'].sum() if 'Pago_Numerico' in df.columns else 0
            except:
                total_pagado = 0
            
            summary_data = {
                'Metrica': [
                    'Semana', 
                    'Total Registros', 
                    'Total Pagado', 
                    'Promedio por Día', 
                    'Días con Registros',
                    'Fecha de Generación'
                ],
                'Valor': [
                    f"{week_start.strftime('%d/%m/%Y')} - {week_end.strftime('%d/%m/%Y')}",
                    total_registros,
                    f"$ {total_pagado:,.0f}",
                    f"$ {total_pagado/7:,.0f}" if total_pagado > 0 else "$ 0",
                    df['Fecha'].nunique() if 'Fecha' in df.columns else 0,
                    datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Resumen', index=False)
            
            # Ajustar anchos de columnas
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        return output.getvalue()
        
    except Exception as e:
        raise Exception(f"Error creando archivo Excel: {str(e)}")

def render_historical_data(records: List[Dict]) -> None:
    """Renderiza el historial de registros con filtro por semana"""
    
    if not records:
        st.info("No hay registros históricos disponibles")
        return
    
    # Selector de semana
    week_start, week_end = render_week_selector()
    
    # Filtrar registros por semana
    filtered_records = filter_records_by_week(records, week_start, week_end)
    
    if not filtered_records:
        st.warning(f"📭 No hay registros para la semana del {week_start.strftime('%d/%m')} al {week_end.strftime('%d/%m')}")
        return
    
    # Convertir a DataFrame
    df = pd.DataFrame(filtered_records)
    
    # Preparar datos para cálculos
    try:
        # Convertir columnas de pago a numérico para cálculos
        df['Pago_Numerico'] = df['Pago con Recargo'].str.replace('$', '').str.replace(',', '').astype(float)
        df['Pago_Base_Numerico'] = df['Pago Base'].str.replace('$', '').str.replace(',', '').astype(float)
    except:
        df['Pago_Numerico'] = 0
        df['Pago_Base_Numerico'] = 0
    
    # ... (el resto del código de estadísticas y gráficas se mantiene igual) ...
    
    # SECCIÓN DE DESCARGA CORREGIDA - VERIFICACIÓN LOCAL
    st.subheader("💾 Descargar Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Descargar CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name=f"registros_semana_{week_start.strftime('%Y%m%d')}_{week_end.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            width='stretch'
        )
    
    with col2:
        # VERIFICAR openpyxl LOCALMENTE
        try:
            import openpyxl
            excel_available = True
        except ImportError:
            excel_available = False
            st.warning("⚠️ openpyxl no disponible para esta función")
        
        if excel_available:
            try:
                excel_data = create_excel_download(df, week_start, week_end)
                st.download_button(
                    label="📊 Descargar Excel",
                    data=excel_data,
                    file_name=f"registros_semana_{week_start.strftime('%Y%m%d')}_{week_end.strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width='stretch'
                )
            except Exception as e:
                st.error(f"❌ Error al generar Excel: {e}")
                # Botón deshabilitado con información del error
                st.button(
                    "📊 Descargar Excel (Error)",
                    disabled=True,
                    help=f"Error: {str(e)}",
                    width='stretch'
                )
        else:
            st.button(
                "📊 Descargar Excel (No disponible)",
                disabled=True,
                help="Instala openpyxl: pip install openpyxl",
                width='stretch'
            )

def render_weekly_summary(records: List[Dict]) -> None:
    """Muestra un resumen semanal rápido en el sidebar"""
    
    if not records:
        return
    
    with st.sidebar:
        st.subheader("📅 Resumen Semanal")
        
        # Semana actual
        current_start, current_end = get_week_range()
        current_week_records = filter_records_by_week(records, current_start, current_end)
        
        if current_week_records:
            df_current = pd.DataFrame(current_week_records)
            try:
                total_current = sum(
                    float(str(pago).replace('$', '').replace(',', '').strip()) 
                    for pago in df_current['Pago con Recargo'] 
                    if pago and str(pago).strip()
                )
            except:
                total_current = 0
            
            st.metric(
                "Esta semana",
                f"$ {total_current:,.0f}",
                help=f"Registros: {len(current_week_records)}"
            )
        else:
            st.info("Sin registros esta semana")
        
        # Semana pasada
        last_week_start = current_start - datetime.timedelta(days=7)
        last_week_end = current_end - datetime.timedelta(days=7)
        last_week_records = filter_records_by_week(records, last_week_start, last_week_end)
        
        if last_week_records:
            df_last = pd.DataFrame(last_week_records)
            try:
                total_last = sum(
                    float(str(pago).replace('$', '').replace(',', '').strip()) 
                    for pago in df_last['Pago con Recargo'] 
                    if pago and str(pago).strip()
                )
            except:
                total_last = 0
            
            st.metric(
                "Semana pasada",
                f"$ {total_last:,.0f}",
                help=f"Registros: {len(last_week_records)}"
            )