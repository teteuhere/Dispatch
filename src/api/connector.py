import smtplib
import os
import json
import urllib.request
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class MicrosoftConnector:
    def __init__(self, logger, secrets=None):
        self.logger = logger
        self.connected = False
        self.token = None

        # Inicialização de Perímetro (Garante existência dos atributos)
        self.email_address = None
        self.email_password = None
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.tenant_id = None
        self.client_id = None
        self.client_secret = None

        if secrets:
            self.email_address = secrets.get("EMAIL_USER")
            self.email_password = secrets.get("EMAIL_PASS")
            self.smtp_server = secrets.get("SMTP_SERVER", "smtp.gmail.com")
            self.smtp_port = int(secrets.get("SMTP_PORT", "587"))
            self.tenant_id = secrets.get("AZURE_TENANT_ID")
            self.client_id = secrets.get("AZURE_CLIENT_ID")
            self.client_secret = secrets.get("AZURE_CLIENT_SECRET")
        else:
            self.email_address = os.getenv("EMAIL_USER")
            self.email_password = os.getenv("EMAIL_PASS")

    def authenticate(self):
        self.logger.info("Auth: Verificando integridade dos serviços...")

        if self.email_address and self.email_password:
            try:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.quit()
                self.logger.info("Auth: SMTP (Email) operacional.")
                self.connected = True
            except Exception as e:
                self.logger.error(f"Auth: Falha no SMTP. {e}")

        if self.tenant_id and self.client_id and self.client_secret:
            if self._get_graph_token():
                self.logger.info("Auth: Microsoft Graph (Teams) operacional.")

    def _get_graph_token(self):
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        data = urllib.parse.urlencode({
            'client_id': self.client_id,
            'scope': 'https://graph.microsoft.com/.default',
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }).encode('utf-8')
        try:
            req = urllib.request.Request(url, data=data, method='POST')
            with urllib.request.urlopen(req) as response:
                resp_json = json.loads(response.read())
                self.token = resp_json.get('access_token')
                return True
        except Exception:
            return False

    def send_email(self, to_email, subject, body):
        if not self.email_address: return False
        try:
            msg = MIMEMultipart()
            msg['From'] = f"Dispatcher <{self.email_address}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.email_password)
            server.sendmail(self.email_address, to_email, msg.as_string())
            server.quit()
            self.logger.info(f"Email enviado: {to_email}")
            return True
        except Exception as e:
            self.logger.error(f"Falha Email ({to_email}): {e}")
            return False

    def send_teams_dm(self, email, body):
        if not self.token: return False
        # Lógica de DM via Graph API...
        return True
