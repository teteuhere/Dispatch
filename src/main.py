import sys
import os
import json
import time
from cryptography.fernet import Fernet
from utils.logger import setup_logger
from utils.intel_manager import IntelManager
from api.connector import MicrosoftConnector

# Mission Assets
CONTACTS_PATH = "config/header.csv"
EMAIL_CONFIG_PATH = "config/body.json"

class EmailCLI:
    def __init__(self):
        self.logger = setup_logger()
        self.contact_manager = IntelManager(CONTACTS_PATH, self.logger)
        secrets = self._load_secrets()
        self.email_service = MicrosoftConnector(self.logger, secrets=secrets)
        self.email_config = self._load_email_config()

    def _load_secrets(self):
        key_path = "config/master.key"
        vault_path = "config/secrets.enc"
        if not os.path.exists(key_path) or not os.path.exists(vault_path):
            self.logger.error("Segurança: Cofre não encontrado. Rode setup_vault.py.")
            return None
        try:
            with open(key_path, "rb") as kf: key = kf.read()
            with open(vault_path, "rb") as vf: encrypted_data = vf.read()
            cipher = Fernet(key)
            return json.loads(cipher.decrypt(encrypted_data).decode())
        except Exception as e:
            self.logger.critical(f"Falha de Descriptografia: {e}")
            return None

    def _load_email_config(self):
        try:
            with open(EMAIL_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"subject": "Notificação de Sistema", "body": "Reporte obrigatório."}

    def main_menu(self):
        """Menu de contingência acessado via CTRL+C."""
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\n" + "="*40 + "\n   DISPATCH: TERMINAL DE CONTROLE\n" + "="*40)
            print("[1] Reiniciar Despacho\n[2] Gerenciar Contatos\n[3] Check de Conexão\n[0] Sair")
            choice = input("Opção >> ").strip()
            if choice == '1':
                self.run_dispatch()
                sys.exit(0) # Encerra após completar o re-envio
            elif choice == '2': self.manage_contacts()
            elif choice == '3': self.check_connection()
            elif choice == '0': sys.exit(0)

    def check_connection(self):
        self.email_service.authenticate()
        input("\n[Enter para continuar]")

    def run_dispatch(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(">>> INICIANDO DESPACHO AUTOMÁTICO...")
        print(">>> Pressione CTRL+C para INTERROMPER e abrir opções.\n")

        contacts = self.contact_manager.list_operatives()
        if not contacts:
            self.logger.error("colaboradores não encontrados no header.csv.")
            return

        subject = self.email_config.get("subject")
        body = self.email_config.get("body")

        try:
            for contact in contacts:
                print(f"Enviando: {contact['Name']} ({contact['Email']})")
                self.email_service.send_email(contact['Email'], subject, body)
                self.email_service.send_teams_dm(contact['Email'], body)
                time.sleep(1.2) # Cadência tática

            print("\n[+] Missão concluída. Todos os colaboradores notificados.")
            print("[+] Encerrando sistema...")
            time.sleep(2)
            sys.exit(0) # Saída limpa após o loop

        except KeyboardInterrupt:
            print("\n\n[!] INTERRUPÇÃO TÁTICA. ENTRANDO NO MENU...")
            time.sleep(1)
            self.main_menu() # Desvia para o menu

if __name__ == "__main__":
    app = EmailCLI()
    # Início imediato da operação
    app.run_dispatch()
