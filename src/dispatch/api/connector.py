import smtplib
import os
import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class MicrosoftConnector:
    def __init__(self, logger, secrets=None):
        self.logger = logger
        self.connected = False

        # Load Creds (Secret or Env)
        if secrets:
            self.email_address = secrets.get("EMAIL_USER")
            self.email_password = secrets.get("EMAIL_PASS")
            self.smtp_server = secrets.get("SMTP_SERVER", "smtp.gmail.com")
            self.smtp_port = int(secrets.get("SMTP_PORT", "587"))
        else:
            self.email_address = os.getenv("EMAIL_USER")
            self.email_password = os.getenv("EMAIL_PASS")
            self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            self.smtp_port = int(os.getenv("SMTP_PORT", "587"))

    def authenticate(self):
        self.logger.info("RADIO CHECK: Connecting to SMTP...")
        if not self.email_address or not self.email_password:
            self.logger.error("RADIO SILENCE: No credentials found.")
            return

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.email_password)
            server.quit()
            self.connected = True
            self.logger.info("LINK ESTABLISHED: Channel Open.")
        except Exception as e:
            self.logger.error(f"CONNECTION FAILED: {e}")
            self.connected = False

    # UPDATED: No defaults. You must supply the intel.
    def send_dispatch(self, target_id, message_type, subject, body):
        if not self.connected:
            self.logger.error("ERRO: Sistema offline.")
            return False

        if message_type == "EMAIL_ALERT":
            return self._send_real_email(target_id, subject, body)
        elif message_type == "TEAMS_MESSAGE":
            # Just logging the body to prove we received it
            self.logger.info(f"[TEAMS SIM] To: {target_id} | Msg: {body[:20]}...")
            return True

    def _send_real_email(self, to_email, subject, body):
        try:
            # PURE TRANSPORT LAYER - No logic, just delivery
            msg = MIMEMultipart('alternative')
            msg['From'] = f"Dispatch Central <{self.email_address}>"
            msg['To'] = to_email
            msg['Subject'] = subject  # <--- No 'if else'. Pure passthrough.
            msg['Date'] = email.utils.formatdate(localtime=True)
            msg['Message-ID'] = email.utils.make_msgid()
            msg['User-Agent'] = "Microsoft Outlook 16.0"

            # 1. Plain Text Version (The raw order)
            part1 = MIMEText(body, 'plain')

            # 2. HTML Version (The pretty order)
            # We wrap YOUR body text in a professional container
            html_text = f"""
            <html>
              <body style="font-family: 'Segoe UI', Arial, sans-serif; color: #222; background-color: #f9f9f9; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: #fff; padding: 30px; border-left: 5px solid #0078d4; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h2 style="color: #2c3e50; margin-top: 0;">{subject}</h2>
                    <p style="font-size: 16px; line-height: 1.5; color: #444;">{body}</p>
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #888;">
                        <p>DISPATCH CENTRAL - AUTOMATED SYSTEM<br>Do not reply to this frequency.</p>
                    </div>
                </div>
              </body>
            </html>
            """
            part2 = MIMEText(html_text, 'html')

            msg.attach(part1)
            msg.attach(part2)

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.email_password)
            server.sendmail(self.email_address, to_email, msg.as_string())
            server.quit()

            self.logger.info(f"PAYLOAD DELIVERED: {to_email}")
            return True
        except Exception as e:
            self.logger.error(f"DELIVERY FAILURE: {e}")
            return False
