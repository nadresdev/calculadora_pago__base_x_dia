import streamlit as st
import pandas as pd
from typing import List, Dict
from datetime import datetime

from app.config.settings import settings

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
    
    # Información adicional
    with st.expander("📋 Detalles del Cálculo"):
        st.write(f"**Tipo de cálculo:** {calculation_data.get('tipo_calculo', 'N/A')}")
        st.write(f"**Valor por hora:** $ {settings.VALOR_HORA:,.0f}")
        st.write(f"**Bono por 6 horas:** $ {settings.BONO_6H:,.0f}")
        st.write(f"**Recargo aplicado:** $ {calculation_data['recargo']:,.0f}")

def render_historical_data(records: List[Dict]) -> None:
    """Renderiza el historial de registros"""
    st.subheader("📊 Historial de Registros")
    
    if not records:
        st.info("No hay registros históricos disponibles")
        return
    
    # Convertir a DataFrame
    df = pd.DataFrame(records)
    
    # Mostrar estadísticas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_registros = len(df)
        st.metric("Total Registros", total_registros)
    
    with col2:
        # Calcular total pagado (asumiendo columna 'Pago con Recargo')
        try:
            total_pagado = sum(
                float(str(pago).replace('$', '').replace(',', '').strip()) 
                for pago in df['Pago con Recargo'] 
                if pago and str(pago).strip()
            )
            st.metric("Total Pagado", f"$ {total_pagado:,.0f}")
        except:
            st.metric("Total Pagado", "N/A")
    
    with col3:
        st.metric("Valor Hora", f"$ {settings.VALOR_HORA:,.0f}")
    
    with col4:
        st.metric("Bono 6h", f"$ {settings.BONO_6H:,.0f}")
    
    # Mostrar tabla de datos
    st.dataframe(
        df.tail(settings.REGISTROS_POR_PAGINA),
        use_container_width=True,
        hide_index=True
    )
    
    # Opción para descargar datos
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name=f"registros_horarios_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )