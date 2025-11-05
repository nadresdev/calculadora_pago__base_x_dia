import os
from typing import Dict, Any

class Settings:
    """Configuración de la aplicación con validación de variables de entorno"""
    
    # Google Sheets
    GOOGLE_SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Configuración de negocio
    VALOR_HORA: int = 15500
    BONO_6H: int = 100000
    TOLERANCIA_MINUTOS: int = 1
    HORAS_MAXIMO_TURNO: int = 16
    
    # App
    REGISTROS_POR_PAGINA: int = 10
    APP_TITLE: str = "🕒 Sistema de Registro de Horarios"
    
    # Recargos predefinidos
    RECARGOS = [0, 5000, 10000, 15000, 20000, 25000, 30000, 35000, 40000]
    
    @property
    def google_credentials(self) -> Dict[str, str]:
        """Obtiene credenciales de Google Sheets desde secrets"""
        try:
            import streamlit as st
            if "google_sheets" not in st.secrets:
                raise ValueError("No se encontraron las credenciales en secrets.toml")
            
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
                "universe_domain": secrets.get("universe_domain", "googleapis.com")
            }
        except Exception as e:
            raise ValueError(f"Error cargando credenciales: {e}")

# Instancia global de configuración
settings = Settings()