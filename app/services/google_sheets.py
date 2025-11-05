import gspread
import logging
from typing import List, Optional, Dict, Any
from google.oauth2.service_account import Credentials
from gspread.exceptions import GSpreadException

from app.config.settings import settings

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """Servicio para manejar operaciones con Google Sheets"""
    
    def __init__(self):
        self._client = None
        self._sheet = None
    
    @property
    def client(self):
        """Lazy initialization del cliente de Google Sheets"""
        if self._client is None:
            try:
                creds = Credentials.from_service_account_info(
                    settings.google_credentials, 
                    scopes=settings.GOOGLE_SCOPES
                )
                self._client = gspread.authorize(creds)
                logger.info("Cliente de Google Sheets inicializado correctamente")
            except Exception as e:
                logger.error(f"Error inicializando cliente: {e}")
                raise
        return self._client
    
    @property
    def sheet(self):
        """Lazy initialization de la hoja de cálculo"""
        if self._sheet is None:
            try:
                spreadsheet_name = settings.google_credentials["spreadsheet_name"]
                self._sheet = self.client.open(spreadsheet_name).sheet1
                self._ensure_headers()
                logger.info("Hoja de cálculo inicializada correctamente")
            except Exception as e:
                logger.error(f"Error accediendo a la hoja: {e}")
                raise
        return self._sheet
    
    def _ensure_headers(self) -> bool:
        """Verifica y crea los encabezados si no existen"""
        headers = [
            "Fecha", "Hora Entrada", "Hora Salida", "Recargo",
            "Horas Trabajadas", "Pago Base", "Pago con Recargo"
        ]
        
        try:
            current_data = self.sheet.get_all_values()
            
            if not current_data:
                self.sheet.append_row(headers)
                return True
            elif current_data[0] != headers:
                if current_data:
                    self.sheet.clear()
                self.sheet.append_row(headers)
                return True
            return False
            
        except GSpreadException as e:
            logger.error(f"Error asegurando headers: {e}")
            raise
    
    def append_record(self, record_data: Dict[str, Any]) -> bool:
        """Agrega un nuevo registro a la hoja"""
        try:
            record = [
                record_data["fecha"],
                record_data["hora_entrada"],
                record_data["hora_salida"],
                record_data["recargo"],
                record_data["horas_trabajadas"],
                record_data["pago_base"],
                record_data["pago_total"]
            ]
            
            self.sheet.append_row(record)
            logger.info(f"Registro agregado para fecha: {record_data['fecha']}")
            return True
            
        except GSpreadException as e:
            logger.error(f"Error agregando registro: {e}")
            return False
    
    def get_all_records(self) -> List[Dict]:
        """Obtiene todos los registros como diccionarios"""
        try:
            return self.sheet.get_all_records()
        except GSpreadException as e:
            logger.error(f"Error obteniendo registros: {e}")
            return []
    
    def check_duplicate(self, fecha: str, hora_entrada: str) -> bool:
        """Verifica si ya existe un registro para la misma fecha y hora"""
        try:
            records = self.get_all_records()
            for record in records:
                if (record.get('Fecha') == fecha and 
                    record.get('Hora Entrada') == hora_entrada):
                    return True
            return False
        except GSpreadException as e:
            logger.error(f"Error verificando duplicados: {e}")
            return False

# Instancia global del servicio
sheets_service = GoogleSheetsService()