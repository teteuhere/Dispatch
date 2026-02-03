"""
PROJECT SUMMARY:
Simple Dispatcher CLI (Email + Teams).
Manages contacts and sends bulk notifications using a defined configuration.
"""

import sys
import os
import json
import time
from dotenv import load_dotenv
from utils.logger import setup_logger
from utils.intel_manager import IntelManager
from api.connector import MicrosoftConnector

CONTACTS_PATH = "config/header.csv"
EMAIL_CONFIG_PATH = "config/body.json"
SECRETS_PATH = "config/secrets.json"

class EmailCLI:
    def __init__(self):
        load_dotenv()

        self.logger = setup_logger()

        self.contact_manager = IntelManager(CONTACTS_PATH, self.logger)

        secrets = self._load_secrets()
        self.email_service = MicrosoftConnector(self.logger, secrets=secrets)

        self.email_config = self._load_email_config()

    def _load_secrets(self):
        """Decrypts the secrets.enc file using master.key"""
        key_path = "config/master.key"
        vault_path = "config/secrets.enc"

        if not os.path.exists(key_path) or not os.path.exists(vault_path):
            self.logger.error("Security: Missing master.key or secrets.enc. Run setup_vault.py first.")
            return None

        try:
            with open(key_path, "rb") as kf:
                key = kf.read()

            with open(vault_path, "rb") as vf:
                encrypted_data = vf.read()

            cipher = Fernet(key)
            decrypted_json = cipher.decrypt(encrypted_data).decode()

            self.logger.info("Security: Vault unlocked successfully.")
            return json.loads(decrypted_json)

        except Exception as e:
            self.logger.critical(f"Security Breach: Could not decrypt vault. {e}")
            return None

    def _load_email_config(self):
        try:
            with open(EMAIL_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Config Error: Could not read {EMAIL_CONFIG_PATH}. {e}")
            return {"subject": "Notification", "body": "Default message."}

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        print("\n" + "="*40)
        print("   DISPATCH COMMAND CENTRAL")
        print("="*40)

    def main_menu(self):
        while True:
            self.print_header()
            print("[1] Start Dispatch (Email + Teams)")
            print("[2] Manage Contacts (CSV)")
            print("[3] Check Connection")
            print("[0] Exit")
            print("-" * 40)

            choice = input("Select option >> ").strip()

            if choice == '1':
                self.run_dispatch()
            elif choice == '2':
                self.manage_contacts()
            elif choice == '3':
                self.check_connection()
            elif choice == '0':
                print("Exiting application.")
                sys.exit(0)
            else:
                print("Invalid option. Please try again.")

    def manage_contacts(self):
        while True:
            self.clear_screen()
            print("--- CONTACT MANAGEMENT ---")
            print("[1] List Contacts")
            print("[2] Add Contact")
            print("[3] Remove Contact")
            print("[0] Back")

            choice = input("Option >> ").strip()

            if choice == '1':
                contacts = self.contact_manager.list_operatives()
                print(f"\nContacts found: {len(contacts)}")
                for i, contact in enumerate(contacts):
                    print(f"  {i+1}. {contact['Name']} <{contact['Email']}>")
                input("\n[Press Enter to continue]")

            elif choice == '2':
                name = input("Name: ")
                email = input("Email: ")
                if name and email:
                    self.contact_manager.add_operative(name, email)
                input("\n[Press Enter to continue]")

            elif choice == '3':
                email = input("Email to remove: ")
                if email:
                    self.contact_manager.remove_operative(email)
                input("\n[Press Enter to continue]")

            elif choice == '0':
                break

    def check_connection(self):
        print("Testing connections...")
        self.email_service.authenticate()
        if self.email_service.connected:
            print("Status: Connected.")
        else:
            print("Status: Disconnected. Check credentials.")
        input("\n[Press Enter to continue]")

    def run_dispatch(self):
        self.clear_screen()
        print("!!! DISPATCH PROTOCOL !!!")
        print("This will send Emails AND Teams notifications to ALL contacts.")
        confirm = input("Are you sure? (y/n): ").lower()

        if confirm != 'y':
            print("Operation cancelled.")
            return

        if not self.email_service.connected:
            self.email_service.authenticate()

        if not self.email_service.connected:
            self.logger.error("Error: No connection available.")
            input("[Enter]")
            return

        contacts = self.contact_manager.list_operatives()
        if not contacts:
            self.logger.warning("List is empty. No contacts to dispatch.")
            return

        subject = self.email_config.get("subject", "Notification")
        body = self.email_config.get("body", "...")

        print(f"Starting batch. Targets: {len(contacts)}")

        for contact in contacts:
            print(f"Engaging: {contact['Name']}...")

            self.email_service.send_email(contact['Email'], subject, body)

            self.email_service.send_teams_dm(contact['Email'], body)

            time.sleep(1)

        print(f"Batch finished.")
        input("\n[Press Enter to return]")

if __name__ == "__main__":
    app = EmailCLI()
    app.main_menu()
