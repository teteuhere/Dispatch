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
            print("\n" + "="*40 + "\n   TERMINAL DE COMANDO\n" + "="*40)
            print("[1] Iniciar/ Retomar Envio")
            print("[2] Adicionar emails alertados")
            print("[3] Mudar credenciais")
            print("[0] Sair")

            choice = input("Opção >> ").strip()
            if choice == '1':
                self.run_dispatch()
                sys.exit(0)
            elif choice == '2':
                self.menu_add_operative()
            elif choice == '3':
                self.menu_change_credentials()
            elif choice == '0':
                print("Evacuando perímetro...")
                sys.exit(0)

    def check_connection(self):
        self.email_service.authenticate()
        input("\n[Enter para continuar]")

    def run_dispatch(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(">>> INICIANDO DESPACHO AUTOMÁTICO...")
        print(">>> Pressione CTRL+C a qualquer momento para INTERROMPER e abrir o menu.\n")

        contacts = self.contact_manager.list_operatives()
        if not contacts:
            self.logger.error("Colaboradores não encontrados no header.csv.")
            time.sleep(2)
            self.main_menu()
            return

        subject = self.email_config.get("subject", "Notificação de Sistema")
        body = self.email_config.get("body", "Reporte obrigatório.")

        try:
            # O Temporizador (A Blitz)
            print("Enviando os emails em três segundos...")
            for i in range(3, 0, -1):
                print("{i}...")
                time.sleep(1)
            print("FOGO LIVRE!\n")

            # Disparo dos emails
            for contact in contacts:
                print("Enviando: {contact['Name']} ({contact['Email']})")
                self.email_service.send_email(contact['Email'], subject, body)
                self.email_service.send_teams_dm(contact['Email'], body)
                time.sleep(1.2) # Cadência tática

            print("\n[+] Missão concluída. Todos os colaboradores notificados.")
            time.sleep(2)
            sys.exit(0)

        except KeyboardInterrupt:
            print("\n\n[!] INTERRUPÇÃO TÁTICA CONFIRMADA. RETORNANDO À BASE...")
            time.sleep(1)
            self.main_menu()

    def menu_add_operative(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("--- ADICIONAR NOVO ALVO ---")
        nome = input("Nome do Operativo: ").strip()
        email = input("Email do Operativo: ").strip()

        if nome and email:
            self.contact_manager.add_operative(nome, email)
        else:
            print("[!] Dados inválidos. Operação cancelada.")

        input("\n[Enter para voltar ao menu]")

    def menu_change_credentials(self):
        """Emula a lógica do setup_vault.py de dentro do executável."""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("--- RECODIFICAÇÃO DO COFRE DE CREDENCIAIS ---")

        key_path = "config/master.key"
        vault_path = "config/secrets.enc"

        # Garante que a chave mestra existe
        if not os.path.exists(key_path):
            os.makedirs("config", exist_ok=True)
            key = Fernet.generate_key()
            with open(key_path, "wb") as kf:
                kf.write(key)
        else:
            with open(key_path, "rb") as kf:
                key = kf.read()

        email = input("Novo Email User: ").strip()
        password = input("Nova Senha (App Password): ").strip()
        tenant = input("Novo Azure Tenant ID: ").strip()
        client_id = input("Novo Azure Client ID: ").strip()
        secret = input("Novo Azure Client Secret: ").strip()

        data = {
            "EMAIL_USER": email,
            "EMAIL_PASS": password,
            "SMTP_SERVER": "smtp.gmail.com",
            "SMTP_PORT": "587",
            "AZURE_TENANT_ID": tenant,
            "AZURE_CLIENT_ID": client_id,
            "AZURE_CLIENT_SECRET": secret
        }

        cipher = Fernet(key)
        encrypted_data = cipher.encrypt(json.dumps(data).encode())

        with open(vault_path, "wb") as f:
            f.write(encrypted_data)

        print("\n[OK] Cofre trancado e atualizado.")

        # Recarrega as credenciais em memória
        secrets = self._load_secrets()
        self.email_service = MicrosoftConnector(self.logger, secrets=secrets)

        input("\n[Enter para voltar ao menu]")

if __name__ == "__main__":
    app = EmailCLI()
    # Início imediato da operação
    app.run_dispatch()
