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
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Hoja principal con los datos
        df.to_excel(writer, sheet_name='Registros', index=False)
        
        # Hoja de resumen
        summary_data = {
            'Metrica': ['Total Registros', 'Total Pagado', 'Promedio por Día', 'Días con Registros'],
            'Valor': [
                len(df),
                df['Pago_Numerico'].sum() if 'Pago_Numerico' in df.columns else 0,
                len(df) / 7 if len(df) > 0 else 0,
                df['Fecha'].nunique() if 'Fecha' in df.columns else 0
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
    
    return output.getvalue()

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
    
    # Mostrar estadísticas de la semana
    st.subheader(f"📊 Estadísticas de la Semana")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_registros = len(df)
        st.metric("Total Registros", total_registros)
    
    with col2:
        total_pagado = df['Pago_Numerico'].sum() if 'Pago_Numerico' in df.columns else 0
        st.metric("Total Pagado", f"$ {total_pagado:,.0f}")
    
    with col3:
        promedio_dia = total_pagado / 7 if total_pagado > 0 else 0
        st.metric("Promedio por Día", f"$ {promedio_dia:,.0f}")
    
    with col4:
        dias_registros = df['Fecha'].nunique() if 'Fecha' in df.columns else 0
        st.metric("Días con Registros", dias_registros)
    
    # Mostrar tabla de datos
    st.subheader(f"📋 Registros de la Semana")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    
    # SECCIÓN DE GRÁFICAS - TOTAL PAGADO POR DÍA
    st.subheader("📈 Total Pagado por Día")
    
    try:
        # Convertir fecha a datetime
        df['Fecha_DT'] = pd.to_datetime(df['Fecha'])
        
        # Agrupar por día y sumar el total pagado
        daily_totals = df.groupby(df['Fecha_DT'].dt.date)['Pago_Numerico'].sum()
        
        if not daily_totals.empty:
            # Convertir a DataFrame para Streamlit
            daily_totals_df = pd.DataFrame({
                'Día': daily_totals.index,
                'Total Pagado': daily_totals.values
            })
            
            # Ordenar por fecha
            daily_totals_df = daily_totals_df.sort_values('Día')
            
            # Formatear la columna de día para mejor visualización
            daily_totals_df['Día_Formateado'] = daily_totals_df['Día'].apply(
                lambda x: x.strftime('%a %d/%m')
            )
            
            # Mostrar gráfico de barras del total pagado por día
            st.bar_chart(
                daily_totals_df.set_index('Día_Formateado')['Total Pagado'],
                color="#FF4B4B"  # Color rojo para destacar
            )
            
            # También mostrar tabla con los totales por día
            with st.expander("📋 Ver detalles de pagos por día"):
                # Formatear los valores para la tabla
                display_df = daily_totals_df.copy()
                display_df['Total Pagado Formateado'] = display_df['Total Pagado'].apply(
                    lambda x: f"$ {x:,.0f}"
                )
                
                st.dataframe(
                    display_df[['Día_Formateado', 'Total Pagado Formateado']].rename(
                        columns={'Día_Formateado': 'Día', 'Total Pagado Formateado': 'Total Pagado'}
                    ),
                    hide_index=True,
                    use_container_width=True
                )
                
                # Estadísticas adicionales
                col1, col2 = st.columns(2)
                with col1:
                    max_pago = daily_totals_df['Total Pagado'].max()
                    st.metric("Mayor pago en un día", f"$ {max_pago:,.0f}")
                with col2:
                    min_pago = daily_totals_df['Total Pagado'].min()
                    st.metric("Menor pago en un día", f"$ {min_pago:,.0f}")
        else:
            st.info("No hay datos de pagos para generar el gráfico")
            
    except Exception as e:
        st.error(f"No se pudo generar el gráfico de pagos por día: {e}")
        # Para debugging, puedes descomentar la siguiente línea:
        # st.write(f"DataFrame columns: {df.columns.tolist()}")
        # st.write(f"Sample data: {df[['Fecha', 'Pago con Recargo', 'Pago_Numerico']].head()}")
    
    # GRÁFICA ADICIONAL: Comparación Pago Base vs Recargos
    try:
        st.subheader("💰 Composición de Pagos")
        
        if 'Pago_Base_Numerico' in df.columns and 'Pago_Numerico' in df.columns:
            # Calcular totales
            total_base = df['Pago_Base_Numerico'].sum()
            total_recargos = df['Pago_Numerico'].sum() - total_base
            
            if total_base > 0 or total_recargos > 0:
                # Crear DataFrame para el gráfico
                composicion_data = pd.DataFrame({
                    'Tipo': ['Pago Base', 'Recargos'],
                    'Monto': [total_base, total_recargos]
                })
                
                # Mostrar métricas
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Pago Base", f"$ {total_base:,.0f}")
                with col2:
                    st.metric("Total Recargos", f"$ {total_recargos:,.0f}")
                
                # Mostrar gráfico de torta si hay datos
                if total_base + total_recargos > 0:
                    try:
                        import plotly.express as px
                        
                        fig = px.pie(
                            composicion_data,
                            values='Monto',
                            names='Tipo',
                            title="Distribución: Pago Base vs Recargos",
                            color='Tipo',
                            color_discrete_map={'Pago Base': '#1f77b4', 'Recargos': '#ff7f0e'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    except ImportError:
                        # Fallback a gráfico de barras si plotly no está disponible
                        st.bar_chart(composicion_data.set_index('Tipo')['Monto'])
            else:
                st.info("No hay datos suficientes para mostrar la composición de pagos")
                
    except Exception as e:
        st.info("No se pudo generar la gráfica de composición de pagos")
    
    # Botones de descarga
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
        # Descargar Excel
        if 'OPENPYXL_AVAILABLE' in globals() and OPENPYXL_AVAILABLE:
            excel_data = create_excel_download(df, week_start, week_end)
            st.download_button(
                label="📊 Descargar Excel",
                data=excel_data,
                file_name=f"registros_semana_{week_start.strftime('%Y%m%d')}_{week_end.strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
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