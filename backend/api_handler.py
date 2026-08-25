"""
Handler para a API do Citaconsular
"""
import requests
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

CITACONSULAR_BASE_URL = "https://www.citaconsular.es/onlinebookings/datetime/"
CITACONSULAR_PUBLICKEY = "2a6f108852f93a6a84463685beccc087b"

class CitaconsularAPI:

    def __init__(self):
        self.base_url = CITACONSULAR_BASE_URL
        self.publickey = CITACONSULAR_PUBLICKEY
        self.headers = {
            "referer": "https://www.citaconsular.es/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }

    def obter_datas_disponiveis(self, service_id, agenda_id, start_date=None, end_date=None):
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if not end_date:
            end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        params = {
            "callback": "",
            "type": "default",
            "publickey": self.publickey,
            "lang": "es",
            "services[]": service_id,
            "agendas[]": agenda_id,
            "src": f"https://www.citaconsular.es/es/hosteds/widgetdefault/{self.publickey}#services",
            "start": start_date,
            "end": end_date,
        }

        try:
            response = requests.get(
                self.base_url, headers=self.headers, params=params, timeout=10
            )
            response.raise_for_status()
            content = response.content[10:-2].decode("utf-8")
            data = json.loads(content)
            return data.get("Slots", [])
        except Exception as e:
            logger.error(f"Erro API: {e}")
            return []

    def verificar_disponibilidade(self, service_id, agenda_id):
        slots = self.obter_datas_disponiveis(service_id, agenda_id)
        datas = [s["date"] for s in slots if s.get("times")]
        return len(datas) > 0, datas

    def obter_horarios_disponiveis(self, service_id, agenda_id, data):
        slots = self.obter_datas_disponiveis(
            service_id, agenda_id, start_date=data, end_date=data
        )
        horarios = []
        for slot in slots:
            if slot["date"] == data and slot.get("times"):
                horarios.extend(slot["times"])
        return horarios
