"""
Agendador Automático via Selenium
Suporta formulário em Espanhol, Português e Inglês
"""
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

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
        except ImportError:
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

    def _clicar_texto(self, textos, timeout=10):
        for texto in textos:
            try:
                el = self._wait(timeout).until(EC.element_to_be_clickable((
                    By.XPATH,
                    f"//*[contains(translate(normalize-space(text()),"
                    f"'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
                    f"'{texto.lower()}')]"
                )))
                el.click()
                time.sleep(1.5)
                return True
            except:
                continue
        return False

    def _passo_cloudflare(self, timeout=15):
        fim = time.time() + timeout
        while time.time() < fim:
            try:
                if "cloudflare" not in self.driver.page_source.lower():
                    return True
            except: pass
            time.sleep(2)
        return True

    def _passo_login(self, numero_passaporte, codigo_consulado):
        try:
            wait = self._wait(10)
            campo_pass = wait.until(EC.presence_of_element_located((
                By.XPATH,
                "//input[@name='username' or @name='pasaporte' or "
                "@placeholder='Pasaporte' or @type='text'][1]"
            )))
            campo_pass.clear()
            campo_pass.send_keys(numero_passaporte)

            campo_senha = wait.until(EC.presence_of_element_located((
                By.XPATH,
                "//input[@name='password' or @type='password']"
            )))
            campo_senha.clear()
            campo_senha.send_keys(codigo_consulado)
            time.sleep(1)
            self._clicar_texto(TEXTOS["acesso"])
            time.sleep(2)
            return True
        except Exception as e:
            logger.error(f"Erro no login: {e}")
            return False

    def agendar(self, nome, servico, numero_passaporte, codigo_consulado):
        logger.info(f"=== Agendando {nome} ===")
        hora_agendada = None
        try:
            self._iniciar()
            self.driver.get(BASE_URL)
            time.sleep(3)

            self._passo_cloudflare()
            self._clicar_texto(TEXTOS["continuar"])
            self._clicar_texto(TEXTOS["aceitar"])
            self._clicar_texto([servico, "visado", "solicitud"])
            time.sleep(2)

            for _ in range(60):
                page = self.driver.page_source.lower()
                sem_vaga = any(t in page for t in TEXTOS["sem_vagas"])
                if not sem_vaga:
                    try:
                        botoes = self.driver.find_elements(
                            By.XPATH,
                            "//div[contains(@class,'timeslot') or "
                            "contains(@class,'hueco')]"
                            "| //button[contains(text(),':')]"
                        )
                        if botoes:
                            hora_agendada = botoes[0].text.strip()
                            botoes[0].click()
                            time.sleep(2)
                            break
                    except: pass
                try:
                    btn = self.driver.find_element(
                        By.XPATH,
                        "//button[contains(@class,'next') or contains(text(),'>')]"
                    )
                    btn.click()
                    time.sleep(1.5)
                except: break

            if not hora_agendada:
                return False, "Nenhuma vaga disponível", None

            ok = self._passo_login(numero_passaporte, codigo_consulado)
            if not ok:
                return False, "Erro no login", None

            self._clicar_texto(TEXTOS["confirmar"])
            time.sleep(3)

            logger.info(f"✅ {nome} agendado às {hora_agendada}!")
            return True, "Sucesso!", hora_agendada

        except Exception as e:
            logger.error(f"Erro: {e}")
            return False, str(e), None
        finally:
            self._fechar()
