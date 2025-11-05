import streamlit as st
import pandas as pd
from typing import List, Dict

from app.config.settings import settings

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
        # Calcular total pagado
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
    if st.button("📥 Descargar CSV"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Descargar CSV",
            data=csv,
            file_name=f"registros_horarios_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )