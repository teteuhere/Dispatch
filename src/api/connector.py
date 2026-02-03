import smtplib
import os
import json
import urllib.request
import urllib.parse
import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class MicrosoftConnector:
    def __init__(self, logger, secrets=None):
        self.logger = logger
        self.connected = False
        self.token = None

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
        self.logger.info("Auth: Checking services...")

        if self.email_address and self.email_password:
            try:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.quit()
                self.logger.info("Auth: SMTP (Email) Connected.")
                self.connected = True
            except Exception as e:
                self.logger.error(f"Auth: SMTP Failed. {e}")

        if self.tenant_id and self.client_id and self.client_secret:
            self._get_graph_token()
            if self.token:
                self.logger.info("Auth: Microsoft Graph (Teams) Connected.")

    def _get_graph_token(self):
        """Authenticates with Azure AD to get an access token."""
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
        except Exception as e:
            self.logger.warning(f"Graph Auth Failed: Could not get token. {e}")
            return False

    def _find_user_id_by_email(self, email):
        """Asks Microsoft Graph for the unique User ID (GUID) of an email address."""
        if not self.token: return None

        url = f"https://graph.microsoft.com/v1.0/users/{email}"
        headers = {'Authorization': f'Bearer {self.token}'}

        try:
            req = urllib.request.Request(url, headers=headers, method='GET')
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read())
                return data.get('id')
        except Exception:
            self.logger.warning(f"Lookup: Could not find Teams profile for {email}")
            return None

    def send_email(self, to_email, subject, body):
        if not self.email_address: return False
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"Dispatcher <{self.email_address}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            part1 = MIMEText(body, 'plain')
            msg.attach(part1)

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.email_password)
            server.sendmail(self.email_address, to_email, msg.as_string())
            server.quit()

            self.logger.info(f"Email Sent: {to_email}")
            return True
        except Exception as e:
            self.logger.error(f"Email Fail: {e}")
            return False

    def send_teams_dm(self, email, body):
        """Sends a private DM to the user associated with the email."""
        if not self.token:
            self.logger.warning(f"Teams Skip: No Graph Token. (Simulating DM to {email})")
            return False

        user_id = self._find_user_id_by_email(email)
        if not user_id:
            return False

        chat_url = "https://graph.microsoft.com/v1.0/chats"
        chat_data = {
            "chatType": "oneOnOne",
            "members": [
                {
                    "@odata.type": "#microsoft.graph.aadUserConversationMember",
                    "roles": ["owner"],
                    "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{user_id}')"
                },
                {
                    "@odata.type": "#microsoft.graph.aadUserConversationMember",
                    "roles": ["owner"],
                    "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{self.client_id}')"
                }
            ]
        }

        try:

            req_chat = urllib.request.Request(
                chat_url,
                data=json.dumps(chat_data).encode('utf-8'),
                headers={'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req_chat) as chat_resp:
                chat_json = json.loads(chat_resp.read())
                chat_id = chat_json.get('id')

            msg_url = f"https://graph.microsoft.com/v1.0/chats/{chat_id}/messages"
            msg_data = {"body": {"content": body}}

            req_msg = urllib.request.Request(
                msg_url,
                data=json.dumps(msg_data).encode('utf-8'),
                headers={'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req_msg) as msg_resp:
                if msg_resp.status == 201:
                    self.logger.info(f"Teams DM Sent: {email}")
                    return True

        except Exception as e:
            self.logger.error(f"Teams DM Fail: {e}")
            return False
