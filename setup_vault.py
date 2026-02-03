from cryptography.fernet import Fernet
import json
import os

CONFIG_DIR = "config"
KEY_PATH = os.path.join(CONFIG_DIR, "master.key")
VAULT_PATH = os.path.join(CONFIG_DIR, "secrets.enc")

def load_key():
    """Carrega a chave existente ou cria uma nova."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

    if os.path.exists(KEY_PATH):
        print(f"[i] Chave mestra encontrada.")
        with open(KEY_PATH, "rb") as kf:
            return kf.read()
    else:
        print(f"[+] Gerando NOVA chave mestra...")
        key = Fernet.generate_key()
        with open(KEY_PATH, "wb") as kf:
            kf.write(key)
        return key

def load_current_secrets(key):
    """Tenta descriptografar os dados atuais para usar como padrão."""
    if not os.path.exists(VAULT_PATH):
        return {}

    try:
        with open(VAULT_PATH, "rb") as vf:
            encrypted_data = vf.read()
        cipher = Fernet(key)
        decrypted_json = cipher.decrypt(encrypted_data).decode()
        return json.loads(decrypted_json)
    except Exception:
        print("[!] Aviso: Não foi possível ler o cofre anterior (pode estar corrompido ou chave mudou).")
        return {}

def ask_input(label, current_value):
    """
    Pergunta ao usuário. Se ele der apenas ENTER, mantém o valor antigo.
    Mostra o valor antigo mascarado para segurança.
    """
    display_value = ""
    if current_value:
        visible_part = current_value[:3] if len(current_value) > 3 else "***"
        display_value = f" [Atual: {visible_part}***]"

    user_input = input(f"{label}{display_value}: ").strip()

    if not user_input and current_value:
        return current_value
    return user_input

def encrypt_data(key):
    print("\n--- CONFIGURAÇÃO DO COFRE ---")
    print("Dica: Pressione ENTER para manter o valor atual mostrado entre colchetes.\n")

    current_data = load_current_secrets(key)

    email = ask_input("Email User", current_data.get("EMAIL_USER"))
    password = ask_input("Email Password (App Password)", current_data.get("EMAIL_PASS"))

    print("\n--- CREDENCIAIS TEAMS (AZURE) ---")
    tenant = ask_input("Azure Tenant ID", current_data.get("AZURE_TENANT_ID"))
    client = ask_input("Azure Client ID", current_data.get("AZURE_CLIENT_ID"))
    secret = ask_input("Azure Client Secret", current_data.get("AZURE_CLIENT_SECRET"))

    data = {
        "EMAIL_USER": email,
        "EMAIL_PASS": password,
        "SMTP_SERVER": "smtp.gmail.com",
        "SMTP_PORT": "587",
        "AZURE_TENANT_ID": tenant,
        "AZURE_CLIENT_ID": client,
        "AZURE_CLIENT_SECRET": secret
    }

    cipher = Fernet(key)
    encrypted_data = cipher.encrypt(json.dumps(data).encode())

    with open(VAULT_PATH, "wb") as f:
        f.write(encrypted_data)
    print(f"\n[OK] Cofre atualizado e trancado em: {VAULT_PATH}")

if __name__ == "__main__":
    key = load_key()
    encrypt_data(key)
