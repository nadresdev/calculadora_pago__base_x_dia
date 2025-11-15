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
def render_weekly_statistics(records: List[Dict]) -> None:
    """Renderiza estadísticas avanzadas por semana"""
    
    if not records:
        st.info("No hay registros históricos disponibles")
        return
    
    st.subheader("📈 Estadísticas Avanzadas por Semana")
    
    # Selector de rango de semanas
    col1, col2 = st.columns(2)
    with col1:
        semanas_atras = st.slider(
            "Número de semanas a analizar:",
            min_value=1,
            max_value=12,
            value=4,
            help="Selecciona cuántas semanas hacia atrás quieres analizar"
        )
    
    with col2:
        st.metric("Período analizado", f"{semanas_atras} semanas")
    
    # Obtener datos de las últimas N semanas
    weekly_data = calculate_weekly_stats(records, semanas_atras)
    
    if not weekly_data:
        st.warning("No hay suficientes datos para generar estadísticas")
        return
    
    # Crear pestañas para diferentes tipos de análisis
    tab1, tab2, tab3, tab4 = st.tabs([
        "💰 Ingresos por Día", 
        "📅 Ingresos por Semana", 
        "📊 Comparativas", 
        "💡 Insights"
    ])
    
    with tab1:
        render_daily_income_stats(weekly_data)
    
    with tab2:
        render_weekly_income_stats(weekly_data)
    
    with tab3:
        render_comparison_stats(weekly_data)
    
    with tab4:
        render_insights_and_recommendations(weekly_data)

def calculate_weekly_stats(records: List[Dict], weeks_back: int) -> List[Dict]:
    """Calcula estadísticas para las últimas N semanas"""
    
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(weeks=weeks_back)
    
    # Filtrar registros del período
    filtered_records = []
    for record in records:
        try:
            record_date = datetime.datetime.strptime(record['Fecha'], '%Y-%m-%d').date()
            if start_date <= record_date <= end_date:
                filtered_records.append(record)
        except (ValueError, KeyError):
            continue
    
    if not filtered_records:
        return []
    
    df = pd.DataFrame(filtered_records)
    
    # Convertir pagos a numérico
    try:
        df['Pago_Numerico'] = df['Pago con Recargo'].str.replace('$', '').str.replace(',', '').astype(float)
        df['Pago_Base_Numerico'] = df['Pago Base'].str.replace('$', '').str.replace(',', '').astype(float)
    except:
        df['Pago_Numerico'] = 0
        df['Pago_Base_Numerico'] = 0
    
    # Convertir fecha
    df['Fecha_DT'] = pd.to_datetime(df['Fecha'])
    
    # Agrupar por semana
    df['Semana'] = df['Fecha_DT'].dt.to_period('W')
    df['Dia_Semana'] = df['Fecha_DT'].dt.day_name()
    df['Mes'] = df['Fecha_DT'].dt.month_name()
    
    weekly_stats = []
    
    for semana in df['Semana'].unique():
        semana_data = df[df['Semana'] == semana]
        semana_start = semana.start_time.date()
        semana_end = semana.end_time.date()
        
        # Estadísticas por día de la semana
        daily_stats = {}
        for dia in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            dia_data = semana_data[semana_data['Dia_Semana'] == dia]
            daily_stats[dia] = {
                'total': dia_data['Pago_Numerico'].sum(),
                'registros': len(dia_data),
                'promedio': dia_data['Pago_Numerico'].mean() if len(dia_data) > 0 else 0
            }
        
        weekly_stats.append({
            'semana_numero': semana.week,
            'semana_rango': f"{semana_start.strftime('%d/%m')} - {semana_end.strftime('%d/%m')}",
            'semana_start': semana_start,
            'semana_end': semana_end,
            'total_semana': semana_data['Pago_Numerico'].sum(),
            'registros_semana': len(semana_data),
            'promedio_diario': semana_data['Pago_Numerico'].sum() / 7,
            'dias_trabajados': semana_data['Fecha'].nunique(),
            'daily_stats': daily_stats,
            'mayor_dia': semana_data.loc[semana_data['Pago_Numerico'].idxmax()] if len(semana_data) > 0 else None,
            'menor_dia': semana_data.loc[semana_data['Pago_Numerico'].idxmin()] if len(semana_data) > 0 else None
        })
    
    return sorted(weekly_stats, key=lambda x: x['semana_start'], reverse=True)

def render_daily_income_stats(weekly_data: List[Dict]) -> None:
    """Muestra ingresos por día de la semana"""
    
    st.subheader("💰 Ingresos por Día de la Semana")
    
    # Preparar datos para el heatmap
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    days_esp = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    
    heatmap_data = []
    for semana in weekly_data:
        for dia_eng, dia_esp in zip(days_order, days_esp):
            heatmap_data.append({
                'Semana': semana['semana_rango'],
                'Día': dia_esp,
                'Ingresos': semana['daily_stats'][dia_eng]['total'],
                'Registros': semana['daily_stats'][dia_eng]['registros']
            })
    
    heatmap_df = pd.DataFrame(heatmap_data)
    
    if not heatmap_df.empty:
        # Gráfico de heatmap
        try:
            import plotly.express as px
            
            pivot_df = heatmap_df.pivot(index='Día', columns='Semana', values='Ingresos')
            pivot_df = pivot_df.reindex(days_esp)
            
            fig = px.imshow(
                pivot_df,
                title="Heatmap de Ingresos por Día y Semana",
                color_continuous_scale='Viridis',
                aspect="auto"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
        except ImportError:
            st.info("Instala plotly para ver el heatmap: pip install plotly")
        
        # Tabla detallada
        with st.expander("📋 Ver tabla detallada por día"):
            display_df = heatmap_df.copy()
            display_df['Ingresos_Formateado'] = display_df['Ingresos'].apply(lambda x: f"$ {x:,.0f}")
            display_df['Promedio por Registro'] = (display_df['Ingresos'] / display_df['Registros']).apply(lambda x: f"$ {x:,.0f}" if x > 0 else "$ 0")
            
            st.dataframe(
                display_df[['Semana', 'Día', 'Ingresos_Formateado', 'Registros', 'Promedio por Registro']],
                hide_index=True,
                use_container_width=True
            )
    
    # Promedios por día de la semana
    st.subheader("📊 Promedios por Día de la Semana")
    
    promedios_dia = []
    for dia_eng, dia_esp in zip(days_order, days_esp):
        total_dia = sum(semana['daily_stats'][dia_eng]['total'] for semana in weekly_data)
        registros_dia = sum(semana['daily_stats'][dia_eng]['registros'] for semana in weekly_data)
        promedio_dia = total_dia / len(weekly_data) if len(weekly_data) > 0 else 0
        
        promedios_dia.append({
            'Día': dia_esp,
            'Ingreso Promedio': promedio_dia,
            'Total Registros': registros_dia,
            'Promedio por Registro': total_dia / registros_dia if registros_dia > 0 else 0
        })
    
    promedios_df = pd.DataFrame(promedios_dia)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras de promedios
        if not promedios_df.empty:
            st.bar_chart(promedios_df.set_index('Día')['Ingreso Promedio'])
    
    with col2:
        # Métricas destacadas
        mejor_dia = promedios_df.loc[promedios_df['Ingreso Promedio'].idxmax()]
        peor_dia = promedios_df.loc[promedios_df['Ingreso Promedio'].idxmin()]
        
        st.metric("Mejor día", mejor_dia['Día'], f"$ {mejor_dia['Ingreso Promedio']:,.0f}")
        st.metric("Peor día", peor_dia['Día'], f"$ {peor_dia['Ingreso Promedio']:,.0f}")

def render_weekly_income_stats(weekly_data: List[Dict]) -> None:
    """Muestra ingresos y tendencias por semana"""
    
    st.subheader("📅 Evolución de Ingresos Semanales")
    
    # Preparar datos para gráfico de tendencia
    trend_data = []
    for semana in weekly_data:
        trend_data.append({
            'Semana': semana['semana_rango'],
            'Ingresos': semana['total_semana'],
            'Registros': semana['registros_semana'],
            'Promedio Diario': semana['promedio_diario'],
            'Días Trabajados': semana['dias_trabajados']
        })
    
    trend_df = pd.DataFrame(trend_data)
    
    if not trend_df.empty:
        # Gráfico de tendencia
        col1, col2 = st.columns(2)
        
        with col1:
            st.line_chart(trend_df.set_index('Semana')['Ingresos'])
            st.caption("Evolución de ingresos semanales")
        
        with col2:
            st.bar_chart(trend_df.set_index('Semana')['Días Trabajados'])
            st.caption("Días con registros por semana")
        
        # Métricas de tendencia
        if len(trend_df) > 1:
            ingreso_actual = trend_df.iloc[0]['Ingresos']
            ingreso_anterior = trend_df.iloc[1]['Ingresos']
            variacion = ((ingreso_actual - ingreso_anterior) / ingreso_anterior * 100) if ingreso_anterior > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Ingreso Semana Actual",
                    f"$ {ingreso_actual:,.0f}",
                    f"{variacion:+.1f}%"
                )
            with col2:
                st.metric(
                    "Registros Semana Actual",
                    trend_df.iloc[0]['Registros']
                )
            with col3:
                st.metric(
                    "Eficiencia por Día",
                    f"$ {trend_df.iloc[0]['Promedio Diario']:,.0f}"
                )
        
        # Tabla resumen semanal
        st.subheader("📋 Resumen por Semana")
        
        display_trend = trend_df.copy()
        display_trend['Ingresos_Formateado'] = display_trend['Ingresos'].apply(lambda x: f"$ {x:,.0f}")
        display_trend['Promedio Diario Formateado'] = display_trend['Promedio Diario'].apply(lambda x: f"$ {x:,.0f}")
        display_trend['Eficiencia'] = (display_trend['Ingresos'] / display_trend['Registros']).apply(lambda x: f"$ {x:,.0f}" if x > 0 else "$ 0")
        
        st.dataframe(
            display_trend[['Semana', 'Ingresos_Formateado', 'Registros', 'Días Trabajados', 'Promedio Diario Formateado', 'Eficiencia']],
            hide_index=True,
            use_container_width=True
        )

def render_comparison_stats(weekly_data: List[Dict]) -> None:
    """Muestra comparativas y análisis de varianza"""
    
    st.subheader("📊 Análisis Comparativo")
    
    if len(weekly_data) < 2:
        st.info("Se necesitan al menos 2 semanas para análisis comparativo")
        return
    
    # Comparativa entre semanas
    comparacion_data = []
    for i, semana in enumerate(weekly_data):
        comparacion_data.append({
            'Semana': f"Semana {i+1}",
            'Rango': semana['semana_rango'],
            'Ingresos': semana['total_semana'],
            'Eficiencia': semana['total_semana'] / semana['registros_semana'] if semana['registros_semana'] > 0 else 0
        })
    
    comparacion_df = pd.DataFrame(comparacion_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de comparación
        st.bar_chart(comparacion_df.set_index('Semana')['Ingresos'])
        st.caption("Comparación de ingresos semanales")
    
    with col2:
        # Gráfico de eficiencia
        st.bar_chart(comparacion_df.set_index('Semana')['Eficiencia'])
        st.caption("Eficiencia (ingreso por registro)")
    
    # Análisis de varianza
    st.subheader("📈 Análisis de Variabilidad")
    
    ingresos = [semana['total_semana'] for semana in weekly_data]
    if len(ingresos) > 1:
        promedio = sum(ingresos) / len(ingresos)
        max_ingreso = max(ingresos)
        min_ingreso = min(ingresos)
        variabilidad = ((max_ingreso - min_ingreso) / promedio * 100) if promedio > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Promedio Semanal", f"$ {promedio:,.0f}")
        with col2:
            st.metric("Mejor Semana", f"$ {max_ingreso:,.0f}")
        with col3:
            st.metric("Peor Semana", f"$ {min_ingreso:,.0f}")
        with col4:
            st.metric("Variabilidad", f"{variabilidad:.1f}%")

def render_insights_and_recommendations(weekly_data: List[Dict]) -> None:
    """Genera insights y recomendaciones basadas en los datos"""
    
    st.subheader("💡 Insights y Recomendaciones")
    
    if len(weekly_data) < 2:
        st.info("Se necesitan más datos para generar insights significativos")
        return
    
    # Análisis de días más productivos
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    days_esp = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    
    promedios_dia = []
    for dia_eng, dia_esp in zip(days_order, days_esp):
        total_dia = sum(semana['daily_stats'][dia_eng]['total'] for semana in weekly_data)
        promedios_dia.append({'Día': dia_esp, 'Total': total_dia})
    
    promedios_dia.sort(key=lambda x: x['Total'], reverse=True)
    
    # Insights
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**🎯 Días Más Productivos**")
        for i, dia in enumerate(promedios_dia[:3]):
            if dia['Total'] > 0:
                st.write(f"{i+1}. **{dia['Día']}**: ${dia['Total']:,.0f}")
    
    with col2:
        st.info("**📅 Tendencia Semanal**")
        
        # Calcular tendencia
        ingresos_semanales = [semana['total_semana'] for semana in weekly_data]
        if len(ingresos_semanales) > 1:
            tendencia = ingresos_semanales[0] - ingresos_semanales[1]
            if tendencia > 0:
                st.success(f"↗️ Mejora de ${tendencia:,.0f}")
            else:
                st.warning(f"↘️ Disminución de ${abs(tendencia):,.0f}")
    
    # Recomendaciones
    st.subheader("🚀 Recomendaciones Accionables")
    
    # Análisis de consistencia
    dias_trabajados = [semana['dias_trabajados'] for semana in weekly_data]
    consistencia = sum(dias_trabajados) / (len(weekly_data) * 7) * 100
    
    if consistencia < 60:
        st.error("**⚠️ Baja Consistencia**")
        st.write(f"Solo trabajas el {consistencia:.1f}% de los días. Considera establecer una rutina más constante.")
    
    # Análisis de días débiles
    dia_mas_debil = promedios_dia[-1]
    if dia_mas_debil['Total'] > 0:
        st.warning("**📊 Oportunidad de Mejora**")
        st.write(f"El {dia_mas_debil['Día']} es tu día menos productivo. Considera estrategias para mejorarlo.")
    
    # Meta semanal
    promedio_semanal = sum(semana['total_semana'] for semana in weekly_data) / len(weekly_data)
    st.success("**🎯 Meta Sugerida**")
    st.write(f"Basado en tu desempeño, una meta semal realista sería: **${promedio_semanal * 1.1:,.0f}** (10% más que tu promedio)")
    
    # Eficiencia
    total_ingresos = sum(semana['total_semana'] for semana in weekly_data)
    total_registros = sum(semana['registros_semana'] for semana in weekly_data)
    eficiencia_promedio = total_ingresos / total_registros if total_registros > 0 else 0
    
    st.info("**💰 Eficiencia Actual**")
    st.write(f"Ganas **${eficiencia_promedio:,.0f}** por registro en promedio")
    
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