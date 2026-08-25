"""
Notificações via Telegram Bot
"""
import logging
import os
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

class TelegramNotifier:

    def __init__(self):
        self.token   = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.base    = f"https://api.telegram.org/bot{self.token}"

    def _send(self, text: str) -> bool:
        if not self.token or not self.chat_id:
            logger.warning("Telegram não configurado")
            return False
        try:
            r = requests.post(
                f"{self.base}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            return r.ok
        except Exception as e:
            logger.error(f"Erro Telegram: {e}")
            return False

    def alerta_vaga(self, nome, servico, datas):
        datas_txt = "\n".join([f"📅 {d}" for d in datas[:5]])
        msg = (
            f"🚨 <b>VAGA ENCONTRADA!</b>\n\n"
            f"👤 <b>{nome}</b>\n"
            f"🎯 Serviço: <b>{servico.upper()}</b>\n\n"
            f"<b>Datas disponíveis:</b>\n{datas_txt}\n\n"
            f"⚡ <i>Sistema a tentar agendar automaticamente...</i>\n"
            f"🕐 {datetime.now().strftime('%H:%M:%S')}"
        )
        return self._send(msg)

    def confirmacao_agendamento(self, nome, servico, data, hora):
        msg = (
            f"✅ <b>AGENDAMENTO CONFIRMADO!</b>\n\n"
            f"👤 <b>{nome}</b>\n"
            f"🎯 Serviço: <b>{servico.upper()}</b>\n"
            f"📅 Data: <b>{data}</b>\n"
            f"🕐 Hora: <b>{hora}</b>\n\n"
            f"📌 <b>Lembre-se:</b>\n"
            f"• Chegue 15 min antes\n"
            f"• Traga todos os documentos\n"
            f"• Leve o passaporte\n\n"
            f"🎉 <i>Boa sorte!</i>"
        )
        return self._send(msg)

    def erro(self, nome, descricao):
        msg = (
            f"⚠️ <b>ERRO no Agendamento</b>\n\n"
            f"👤 <b>{nome}</b>\n"
            f"❌ {descricao}\n\n"
            f"🕐 {datetime.now().strftime('%H:%M:%S')}"
        )
        return self._send(msg)

    def sistema_iniciado(self, total_usuarios):
        msg = (
            f"🚀 <b>Sistema Iniciado!</b>\n\n"
            f"👥 Monitorando <b>{total_usuarios}</b> pessoas\n"
            f"🔄 Verificação a cada 5 minutos\n"
            f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        )
        return self._send(msg)
