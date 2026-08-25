"""
Notificações por Email
"""
import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailNotifier:

    def __init__(self):
        self.sender   = os.getenv("EMAIL_SENDER", "")
        self.password = os.getenv("EMAIL_PASSWORD", "")

    def _enviar(self, destinatario, subject, html):
        if not self.sender or not self.password:
            logger.warning("Email não configurado")
            return
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = self.sender
            msg["To"]      = destinatario
            msg.attach(MIMEText(html, "html"))
            with smtplib.SMTP("smtp.gmail.com", 587) as s:
                s.starttls()
                s.login(self.sender, self.password)
                s.send_message(msg)
            logger.info(f"Email enviado para {destinatario}")
        except Exception as e:
            logger.error(f"Erro email: {e}")

    def enviar_alerta_vaga(self, destinatario, nome, servico, datas):
        datas_txt = "".join([f"<li>📅 {d}</li>" for d in datas[:5]])
        self._enviar(
            destinatario,
            f"🎉 Vaga disponível para {servico}!",
            f"""
            <h2>Olá {nome}! 👋</h2>
            <p>Encontrámos vagas para <b>{servico.upper()}</b>:</p>
            <ul>{datas_txt}</ul>
            <p>⚡ O sistema está a tentar agendar automaticamente!</p>
            <p>🕐 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            """
        )

    def enviar_confirmacao_agendamento(self, destinatario, nome, servico, data, hora):
        self._enviar(
            destinatario,
            f"✅ Agendamento Confirmado - {servico}",
            f"""
            <h2>✅ Agendamento Confirmado!</h2>
            <p><b>Nome:</b> {nome}</p>
            <p><b>Serviço:</b> {servico}</p>
            <p><b>Data:</b> {data}</p>
            <p><b>Hora:</b> {hora}</p>
            <hr>
            <p>📌 Lembre-se de trazer o passaporte!</p>
            """
        )

    def enviar_erro(self, destinatario, nome, erro):
        self._enviar(
            destinatario,
            "⚠️ Erro no Agendamento",
            f"""
            <h2>⚠️ Erro</h2>
            <p>Olá {nome},</p>
            <p>{erro}</p>
            <p>🕐 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            """
        )
