"""
Scheduler - Verifica vagas e agenda automaticamente
"""
import logging
import schedule
import time
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Usuario, HistoricoAlerta, HistoricoAgendamento
from api_handler import CitaconsularAPI
from notifier import EmailNotifier
from telegram_notifier import TelegramNotifier
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./citas.db")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "5"))

logger = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


class AgendadorVagas:

    def __init__(self):
        self.api      = CitaconsularAPI()
        self.email    = EmailNotifier()
        self.telegram = TelegramNotifier()

    def executar_uma_vez(self):
        self._verificar()

    def _verificar(self):
        logger.info(f"=== Verificação iniciada {datetime.now().strftime('%H:%M:%S')} ===")
        db = SessionLocal()
        try:
            # Buscar utilizadores prontos para agendar (têm passaporte + código)
            prontos = db.query(Usuario).filter(
                Usuario.agendada == False,
                Usuario.numero_passaporte != None,
                Usuario.numero_passaporte != "",
                Usuario.codigo_consulado  != None,
                Usuario.codigo_consulado  != "",
            ).all()

            # Buscar utilizadores pendentes (para alertar apenas)
            pendentes = db.query(Usuario).filter(
                Usuario.agendada == False
            ).all()

            if not pendentes:
                logger.info("Todos já agendados!")
                return

            # Verificar vagas via API
            tem_vaga, datas = self.api.verificar_disponibilidade(
                "bkt739959", "bkt332409"
            )

            if not tem_vaga:
                logger.info("Sem vagas disponíveis")
                return

            logger.info(f"✅ VAGAS ENCONTRADAS! {datas}")

            # Notificar TODOS por Telegram e Email
            for usuario in pendentes:
                # Telegram (instantâneo!)
                self.telegram.alerta_vaga(usuario.nome, usuario.servico, datas)
                # Email (backup)
                self.email.enviar_alerta_vaga(
                    usuario.email, usuario.nome, usuario.servico, datas
                )
                # Guardar alerta
                alerta = HistoricoAlerta(
                    usuario_id=usuario.id,
                    servico=usuario.servico,
                    data_disponivel=datetime.now(),
                    notificado=True
                )
                db.add(alerta)

            db.commit()

            # Agendar automaticamente quem está PRONTO
            for usuario in prontos:
                self._agendar(db, usuario, datas)

        except Exception as e:
            logger.error(f"Erro na verificação: {e}")
        finally:
            db.close()

    def _agendar(self, db, usuario, datas):
        """Tenta agendar automaticamente"""
        logger.info(f"Agendando: {usuario.nome}")
        try:
            from selenium_agendador import AgendadorSelenium
            agendador = AgendadorSelenium(headless=True)
            sucesso, mensagem, hora = agendador.agendar(
                nome=usuario.nome,
                servico=usuario.servico,
                numero_passaporte=usuario.numero_passaporte,
                codigo_consulado=usuario.codigo_consulado,
            )

            # Guardar resultado
            ag = HistoricoAgendamento(
                usuario_id=usuario.id,
                servico=usuario.servico,
                data_agendada=datetime.now(),
                hora_agendada=hora,
                status="sucesso" if sucesso else "falha",
                mensagem_erro=None if sucesso else mensagem
            )
            db.add(ag)

            if sucesso:
                usuario.agendada     = True
                usuario.hora_agendada = hora
                usuario.data_agendada = datetime.now()
                usuario.status        = "agendado"
                db.commit()
                # Notificar sucesso
                self.telegram.confirmacao_agendamento(
                    usuario.nome, usuario.servico, str(datetime.now().date()), hora or ""
                )
                self.email.enviar_confirmacao_agendamento(
                    usuario.email, usuario.nome, usuario.servico,
                    str(datetime.now().date()), hora or ""
                )
                logger.info(f"✅ {usuario.nome} agendado!")
            else:
                usuario.status = "erro"
                db.commit()
                self.telegram.erro(usuario.nome, mensagem)
                logger.warning(f"❌ Falha ao agendar {usuario.nome}: {mensagem}")

        except Exception as e:
            logger.error(f"Erro ao agendar {usuario.nome}: {e}")
            self.telegram.erro(usuario.nome, str(e))

    def agendar_verificacoes(self):
        logger.info(f"Verificações a cada {CHECK_INTERVAL} minuto(s)")
        schedule.every(CHECK_INTERVAL).minutes.do(self._verificar)
        # Primeira verificação imediata
        self._verificar()
        while True:
            schedule.run_pending()
            time.sleep(10)
