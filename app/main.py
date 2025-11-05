import streamlit as st
import datetime
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
def banner_reglas():
    """Banner en la parte superior de la app con las reglas y tarifas"""
    
    st.markdown("""
    <style>
    .banner-rules {
        background: linear-gradient(90deg, #1f77b4 0%, #2e8b57 100%);
        color: white;
        padding: 1rem;
        border-radius: 0 0 15px 15px;
        margin: -1rem -1rem 2rem -1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border-bottom: 3px solid #ffd700;
    }
    .banner-title {
        text-align: center;
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    .banner-content {
        display: flex;
        justify-content: space-around;
        align-items: center;
        flex-wrap: wrap;
        gap: 1rem;
    }
    .banner-item {
        text-align: center;
        padding: 0.5rem 1rem;
        background: rgba(255,255,255,0.15);
        border-radius: 8px;
        min-width: 120px;
        backdrop-filter: blur(10px);
    }
    .banner-label {
        font-size: 0.85rem;
        opacity: 0.9;
        margin-bottom: 0.3rem;
    }
    .banner-value {
        font-size: 1.1rem;
        font-weight: bold;
    }
    .banner-highlight {
        background: rgba(255,215,0,0.2);
        border: 1px solid rgba(255,215,0,0.5);
    }
    /* Responsive */
    @media (max-width: 768px) {
        .banner-content {
            flex-direction: column;
            gap: 0.5rem;
        }
        .banner-item {
            min-width: 90%;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="banner-rules">
        <div class="banner-title">📊 REGLAS Y TARIFAS APLICADAS</div>
        <div class="banner-content">
            <div class="banner-item">
                <div class="banner-label">Hora Normal</div>
                <div class="banner-value">$15,500</div>
            </div>
            <div class="banner-item banner-highlight">
                <div class="banner-label">Bono 6 Horas</div>
                <div class="banner-value">$100,000</div>
            </div>
            <div class="banner-item">
                <div class="banner-label">Hora Extra</div>
                <div class="banner-value">$15,500</div>
            </div>
            <div class="banner-item">
                <div class="banner-label">Menos de 6h</div>
                <div style="font-size: 0.8rem;">Horas × $15,500</div>
            </div>
            <div class="banner-item">
                <div class="banner-label">Más de 6h</div>
                <div style="font-size: 0.8rem;">$100k + extras</div>
            </div>
            <div class="banner-item">
                <div class="banner-label">Recargos</div>
                <div style="font-size: 0.8rem;">+ Pago base</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Configuración
class AppConfig:
    VALOR_HORA = 15500
    BONO_6H = 100000
    TOLERANCIA_MINUTOS = 1
    RECARGOS = [0, 5000, 10000, 15000, 20000, 25000, 30000, 35000, 40000]
    
    @property
    def credentials(self):
        if "google_sheets" not in st.secrets:
            st.error("❌ No se encontraron las credenciales en secrets.toml")
            return None
            
        secrets = st.secrets["google_sheets"]
        return {
            "type": secrets["type"],
            "project_id": secrets["project_id"],
            "private_key_id": secrets["private_key_id"],
            "private_key": secrets["private_key"].replace('\\n', '\n'),
            "client_email": secrets["client_email"],
            "client_id": secrets["client_id"],
            "auth_uri": secrets["auth_uri"],
            "token_uri": secrets["token_uri"],
            "auth_provider_x509_cert_url": secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": secrets["client_x509_cert_url"],
        }

config = AppConfig()

@st.cache_resource
def get_google_sheets_client():
    """Conecta con Google Sheets"""
    try:
        creds = Credentials.from_service_account_info(
            config.credentials,
            scopes=["https://www.googleapis.com/auth/spreadsheets",
                   "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds)
        spreadsheet_name = st.secrets["google_sheets"]["spreadsheet_name"]
        sheet = client.open(spreadsheet_name).sheet1
        return sheet
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        return None

def ensure_headers(sheet):
    """Asegura que los encabezados existan"""
    headers = ["Fecha", "Hora Entrada", "Hora Salida", "Recargo", 
               "Horas Trabajadas", "Pago Base", "Pago con Recargo"]
    
    try:
        data = sheet.get_all_values()
        if not data or data[0] != headers:
            if data:
                sheet.clear()
            sheet.append_row(headers)
            return True
        return False
    except Exception as e:
        st.error(f"Error con encabezados: {e}")
        return False

def validate_schedule(entrada, salida):
    """Valida los horarios"""
    if salida <= entrada:
        st.error("❌ La hora de salida debe ser posterior a la entrada")
        return False
    return True

def calculate_hours(entrada, salida):
    """Calcula horas trabajadas"""
    entrada_dt = datetime.datetime.combine(datetime.date.today(), entrada)
    salida_dt = datetime.datetime.combine(datetime.date.today(), salida)
    diferencia = salida_dt - entrada_dt
    
    total_segundos = diferencia.total_seconds()
    horas_int = int(total_segundos // 3600)
    minutos = int((total_segundos % 3600) // 60)
    total_horas = total_segundos / 3600
    
    return {
        "horas_formateadas": f"{horas_int:02d}:{minutos:02d}",
        "total_horas": total_horas
    }

def calculate_payment(horas):
    """Calcula el pago"""
    tolerancia = config.TOLERANCIA_MINUTOS / 60
    
    if horas < 6 - tolerancia:
        return horas * config.VALOR_HORA, "horas_normales"
    elif abs(horas - 6) <= tolerancia:
        return config.BONO_6H, "bono_6h"
    else:
        horas_extra = horas - 6
        return config.BONO_6H + (horas_extra * config.VALOR_HORA), "horas_extra"

def main():
    """Aplicación principal"""
    st.set_page_config(
        page_title="🕒 Registro de Horarios",
        page_icon="🕒",
        layout="centered"
    )
    
        # 1. MOSTRAR BANNER (esto va inmediatamente después de set_page_config)
    banner_reglas()
    
    st.title("🕒 Registro de Horarios con Recargos")
    
    # Conexión a Google Sheets
    sheet = get_google_sheets_client()
    if not sheet:
        st.stop()
    
    # Verificar encabezados
    ensure_headers(sheet)
    
    # Formulario
    st.subheader("📝 Nuevo Registro")
    
    fecha = st.date_input("Fecha:", datetime.date.today())
    
    col1, col2 = st.columns(2)
    with col1:
        hora_entrada = st.time_input("Hora Entrada", datetime.time(8, 0))
    with col2:
        hora_salida = st.time_input("Hora Salida", datetime.time(17, 0))
    
    recargo = st.selectbox(
        "Recargo:",
        options=config.RECARGOS,
        format_func=lambda x: f"$ {x:,}" if x else "Sin recargo"
    )
    
    # Validación y cálculos
    if validate_schedule(hora_entrada, hora_salida):
        hours_data = calculate_hours(hora_entrada, hora_salida)
        pago_base, tipo_calculo = calculate_payment(hours_data["total_horas"])
        pago_total = pago_base + recargo
        
        # Mostrar resultados
        st.subheader("💰 Resultados")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Horas Trabajadas", hours_data["horas_formateadas"])
        with col2:
            st.metric("Pago Base", f"$ {pago_base:,.0f}")
        with col3:
            st.metric("Pago Total", f"$ {pago_total:,.0f}")
        
        # Guardar
        if st.button("💾 Guardar Registro", type="primary"):
            try:
                fila = [
                    str(fecha),
                    hora_entrada.strftime("%I:%M %p"),
                    hora_salida.strftime("%I:%M %p"),
                    recargo,
                    hours_data["horas_formateadas"],
                    f"$ {pago_base:,.0f}",
                    f"$ {pago_total:,.0f}"
                ]
                
                sheet.append_row(fila)
                st.success("✅ Registro guardado correctamente!")
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")
    
    # Historial
    st.markdown("---")
    if st.checkbox("📊 Mostrar historial"):
        try:
            records = sheet.get_all_records()
            if records:
                df = pd.DataFrame(records)
                st.dataframe(df.tail(10), use_container_width=True)
            else:
                st.info("No hay registros aún")
        except Exception as e:
            st.error(f"Error cargando historial: {e}")

if __name__ == "__main__":
    main()