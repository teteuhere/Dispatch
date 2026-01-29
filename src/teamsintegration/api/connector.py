import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class MicrosoftConnector:
    def __init__(self, logger):
        self.logger = logger
        self.connected = False
        self.email_address = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_PASS")
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))

    def authenticate(self):
        self.logger.info("INICIANDO CONEXÃO SMTP (Munição Real)...")
        if not self.email_address or not self.email_password:
            self.logger.error("FALHA: Credenciais de e-mail não encontradas nas variáveis de ambiente.")
            return

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.email_password)
            server.quit()
            self.connected = True
            self.logger.info("CONEXÃO SMTP ESTABELECIDA. Pronto para disparo.")
        except Exception as e:
            self.logger.error(f"FALHA NA AUTENTICAÇÃO SMTP: {e}")
            self.connected = False

    def find_user_id(self, email):
        return email

    def send_dispatch(self, target_id, message_type):
        if not self.connected:
            self.logger.error("ERRO: Sistema offline. Não é possível disparar.")
            return False

        if message_type == "EMAIL_ALERT":
            return self._send_real_email(target_id)
        elif message_type == "TEAMS_MESSAGE":
            self.logger.info(f"[SIMULAÇÃO] Enviando mensagem Teams para {target_id} (API Indisponível).")
            return True

    def _send_real_email(self, to_email):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = "ALERTA DE SEGURANÇA: Procedimento de Fechamento"

            body = "Por favor, feche a planilha. O protocolo de segurança exige esta ação imediata."
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_address, to_email, text)
            server.quit()

            self.logger.info(f"DISPARO CONFIRMADO: E-mail enviado para {to_email}")
            return True
        except Exception as e:
            self.logger.error(f"FALHA NO DISPARO DE E-MAIL: {e}")
            return False
