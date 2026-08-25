"""
Agendador Automático via Selenium
Suporta formulário em Espanhol, Português e Inglês
"""
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

# Mapeamento de textos em 3 idiomas
TEXTOS = {
    "continuar": ["continue", "continuar", "siguiente", "next"],
    "aceitar":   ["aceitar",  "aceptar",   "accept",   "acepto"],
    "acesso":    ["access",   "acceso",    "aceder",   "entrar"],
    "confirmar": ["confirmar","confirm",   "confirme", "aceptar cita"],
    "sem_vagas": ["no hay horas", "no slots", "sem vagas", "no available"],
}

PUBLIC_KEY = "2a6f108852f93a6a84463685beccc087b"
BASE_URL   = f"https://www.citaconsular.es/es/hosteds/widgetdefault/{PUBLIC_KEY}/"

class AgendadorSelenium:

    def __init__(self, headless=True):
        self.headless = headless
        self.driver   = None

    def _iniciar(self):
        try:
            import undetected_chromedriver as uc
            opts = uc.ChromeOptions()
            if self.headless:
                opts.add_argument("--headless=new")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--window-size=1280,900")
            self.driver = uc.Chrome(options=opts)
            logger.info("Chrome (undetected) iniciado")
        except ImportError:
            # Fallback para Selenium normal
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            opts = Options()
            if self.headless:
                opts.add_argument("--headless")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
            )
            self.driver = webdriver.Chrome(options=opts)

    def _fechar(self):
        if self.driver:
            try: self.driver.quit()
            except: pass
            self.driver = None

    def _wait(self, segundos=10):
        return WebDriverWait(self.driver, segundos)

    def _clicar_texto(self, textos_possiveis, timeout=10):
        """Clica num elemento que contenha qualquer um dos textos (multi-idioma)"""
        for texto in textos_possiveis:
            try:
                el = self._wait(timeout).until(EC.element_to_be_clickable(
                    (By.XPATH,
                     f"//*[contains(translate(normalize-space(text()),"
                     f"'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
                     f"'{texto.lower()}')]")
                ))
                el.click()
                logger.info(f"Clicado: '{texto}'")
                time.sleep(1.5)
                return True
            except:
                continue
        return False

    def _passo_cloudflare(self, timeout=15):
        """Aguarda Cloudflare ser resolvido automaticamente"""
        logger.info("Aguardando Cloudflare...")
        fim = time.time() + timeout
        while time.time() < fim:
            try:
                # Se já não estiver na página Cloudflare, passou
                if "cloudflare" not in self.driver.page_source.lower():
                    logger.info("✅ Cloudflare passado")
                    return True
            except: pass
            time.sleep(2)
        logger.warning("⚠️ Cloudflare pode não ter passado")
        return True  # Tenta continuar mesmo assim

    def _passo_continuar(self):
        """Clica em Continue / Continuar"""
        logger.info("Passo: Continuar...")
        return self._clicar_texto(TEXTOS["continuar"])

    def _passo_aceitar_termos(self):
        """Clica em Aceitar / Aceptar"""
        logger.info("Passo: Aceitar termos...")
        return self._clicar_texto(TEXTOS["aceitar"])

    def _passo_selecionar_servico(self, servico):
        """Seleciona o serviço (visado, passaporte, etc)"""
        logger.info(f"Passo: Selecionar serviço '{servico}'...")
        try:
            # Tentar clicar no serviço pelo texto
            self._clicar_texto([servico, "visado", "solicitud"])
            time.sleep(2)
            return True
        except:
            logger.warning(f"Serviço '{servico}' não encontrado")
            return False

    def _passo_selecionar_data_hora(self):
        """
        Navega pelas datas e seleciona o primeiro horário disponível
        Retorna (data, hora) ou (None, None)
        """
        logger.info("Passo: Procurar data e hora disponível...")
        
        for tentativa in range(60):  # Até 60 dias à frente
            page = self.driver.page_source.lower()
            
            # Verificar se há vagas na data atual
            sem_vaga = any(t in page for t in TEXTOS["sem_vagas"])
            
            if not sem_vaga:
                # Há vagas! Tentar clicar num horário (botões azuis)
                try:
                    botoes = self.driver.find_elements(
                        By.XPATH,
                        "//div[contains(@class,'timeslot') or contains(@class,'time-slot') "
                        "or contains(@class,'hueco') or contains(@class,'slot')]"
                        "| //button[contains(@class,'time') or contains(text(),':')]"
                    )
                    if botoes:
                        hora_texto = botoes[0].text.strip()
                        botoes[0].click()
                        logger.info(f"✅ Horário selecionado: {hora_texto}")
                        time.sleep(2)
                        return hora_texto
                except Exception as e:
                    logger.warning(f"Erro ao selecionar horário: {e}")

            # Avançar para próximo dia
            try:
                btn_proximo = self.driver.find_element(
                    By.XPATH,
                    "//button[contains(@class,'next') or contains(@aria-label,'siguiente') "
                    "or contains(@aria-label,'next') or contains(text(),'>')]"
                    "| //*[contains(@class,'arrow-right') or contains(@class,'chevron-right')]"
                )
                btn_proximo.click()
                time.sleep(1.5)
            except:
                logger.warning("Botão próximo dia não encontrado")
                break

        logger.warning("Nenhuma vaga encontrada após navegar")
        return None

    def _passo_login(self, numero_passaporte, codigo_consulado):
        """
        Preenche o formulário de login:
        - Número do passaporte
        - Código do consulado (senha)
        Suporta campos em ES/PT/EN
        """
        logger.info("Passo: Login com passaporte e código...")
        try:
            wait = self._wait(10)

            # Campo passaporte (pode chamar-se de várias formas)
            campo_pass = wait.until(EC.presence_of_element_located((
                By.XPATH,
                "//input[@name='username' or @name='pasaporte' or @name='passport' "
                "or @placeholder='Pasaporte' or @type='text'][1]"
            )))
            campo_pass.clear()
            campo_pass.send_keys(numero_passaporte)
            logger.info(f"Passaporte inserido: {numero_passaporte}")

            # Campo senha / código do consulado
            campo_senha = wait.until(EC.presence_of_element_located((
                By.XPATH,
                "//input[@name='password' or @type='password' "
                "or @placeholder='Password' or @placeholder='Contraseña']"
            )))
            campo_senha.clear()
            campo_senha.send_keys(codigo_consulado)
            logger.info("Código do consulado inserido")

            time.sleep(1)

            # Clicar em Access / Acceso / Aceder
            self._clicar_texto(TEXTOS["acesso"])
            time.sleep(2)
            logger.info("✅ Login efectuado")
            return True

        except Exception as e:
            logger.error(f"Erro no login: {e}")
            return False

    def _passo_confirmar(self):
        """Clica em Confirmar / Aceptar para finalizar agendamento"""
        logger.info("Passo: Confirmar agendamento...")
        sucesso = self._clicar_texto(TEXTOS["confirmar"])
        if sucesso:
            time.sleep(3)
            # Verificar se agendou com sucesso
            page = self.driver.page_source.lower()
            palavras_sucesso = ["confirmad", "confirmed", "confirmado", "sucesso", "success", "cita"]
            if any(p in page for p in palavras_sucesso):
                logger.info("✅ Agendamento confirmado!")
                return True
        return False

    def agendar(self, nome, servico, numero_passaporte, codigo_consulado):
        """
        Fluxo completo de agendamento:
        1. Cloudflare
        2. Continue / Continuar
        3. Aceitar termos
        4. Selecionar serviço
        5. Selecionar data/hora (navega automaticamente)
        6. Login (passaporte + código)
        7. Confirmar
        
        Returns: (sucesso: bool, mensagem: str, hora: str)
        """
        logger.info(f"=== Iniciando agendamento para {nome} ===")
        hora_agendada = None

        try:
            self._iniciar()
            self.driver.get(BASE_URL)
            time.sleep(3)

            # 1. Cloudflare
            self._passo_cloudflare()

            # 2. Continuar
            self._passo_continuar()

            # 3. Aceitar termos
            self._passo_aceitar_termos()

            # 4. Selecionar serviço
            self._passo_selecionar_servico(servico)

            # 5. Selecionar data/hora
            hora_agendada = self._passo_selecionar_data_hora()
            if not hora_agendada:
                return False, "Nenhuma vaga disponível", None

            # 6. Login
            ok_login = self._passo_login(numero_passaporte, codigo_consulado)
            if not ok_login:
                return False, "Erro no login (passaporte/código inválido?)", None

            # 7. Confirmar
            ok_confirmar = self._passo_confirmar()
            if ok_confirmar:
                logger.info(f"✅ {nome} agendado às {hora_agendada}!")
                return True, "Agendamento realizado com sucesso!", hora_agendada
            else:
                return False, "Erro ao confirmar agendamento", None

        except Exception as e:
            logger.error(f"Erro no agendamento de {nome}: {e}")
            return False, str(e), None

        finally:
            self._fechar()

    def verificar_vagas(self, servico="visado"):
        """
        Verifica rapidamente se há vagas disponíveis
        sem fazer agendamento.
        Returns: (tem_vaga: bool, datas: list)
        """
        logger.info("Verificando vagas via Selenium...")
        try:
            self._iniciar()
            self.driver.get(BASE_URL)
            time.sleep(3)
            self._passo_cloudflare()
            self._passo_continuar()
            self._passo_aceitar_termos()
            self._passo_selecionar_servico(servico)

            datas_com_vaga = []
            for _ in range(30):
                page = self.driver.page_source.lower()
                sem_vaga = any(t in page for t in TEXTOS["sem_vagas"])
                if not sem_vaga:
                    # Tentar extrair data actual
                    try:
                        data_el = self.driver.find_element(
                            By.XPATH,
                            "//*[contains(@class,'date') or contains(@class,'fecha')]"
                        )
                        datas_com_vaga.append(data_el.text.strip())
                    except:
                        datas_com_vaga.append("Data disponível")
                    break

                # Próximo dia
                try:
                    btn = self.driver.find_element(
                        By.XPATH,
                        "//button[contains(@class,'next') or contains(text(),'>')]"
                        "| //*[contains(@class,'arrow-right')]"
                    )
                    btn.click()
                    time.sleep(1)
                except:
                    break

            return len(datas_com_vaga) > 0, datas_com_vaga

        except Exception as e:
            logger.error(f"Erro ao verificar vagas: {e}")
            return False, []
        finally:
            self._fechar()
