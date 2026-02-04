"""
MISSION SUMMARY:
Módulo de logística de inteligência. Responsável por ler e manipular
o arquivo de colaboradores (CSV) de forma segura.
"""
import csv
import os
from typing import List, Dict, Optional

class IntelManager:
    def __init__(self, csv_path: str, logger):
        self.csv_path = csv_path
        self.logger = logger
        self._ensure_intel_exists()

    def _ensure_intel_exists(self):
        if not os.path.exists(self.csv_path):
            self.logger.warning(f"INTEL MISSING: {self.csv_path} não encontrado. Criando arquivo vazio.")
            os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
            with open(self.csv_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "Email"]) # Header

    def list_operatives(self) -> List[Dict[str, str]]:
        """Retorna a lista de opertivos cadastrados."""
        operatives = []
        try:
            with open(self.csv_path, mode='r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row and row['Email']: # Filtra linhas vazias
                        operatives.append(row)
            return operatives
        except Exception as e:
            self.logger.error(f"INTEL CORRUPTED: Falha ao ler CSV. {e}")
            return []

    def add_operative(self, name: str, email: str) -> bool:
        """Adiciona um novo alvo ao arquivo."""
        # Verifica duplicatas simples
        current_ops = self.list_operatives()
        for op in current_ops:
            if op['Email'] == email:
                self.logger.warning(f"DUPLICATA: Alvo {email} já consta no banco de dados.")
                return False

        try:
            with open(self.csv_path, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([name, email])
            self.logger.info(f"RECRUTAMENTO: {name} ({email}) adicionado ao sistema.")
            return True
        except Exception as e:
            self.logger.error(f"FALHA DE ESCRITA: {e}")
            return False

    def remove_operative(self, email: str) -> bool:
        """Remove um alvo baseado no email."""
        operatives = self.list_operatives()
        found = False
        new_list = []

        for op in operatives:
            if op['Email'] == email:
                found = True
                continue
            new_list.append(op)

        if found:
            try:
                with open(self.csv_path, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Name", "Email"]) # Recria header
                    for op in new_list:
                        writer.writerow([op['Name'], op['Email']])
                self.logger.info(f"BAIXA CONFIRMADA: {email} removido.")
                return True
            except Exception as e:
                self.logger.error(f"FALHA DE REMOÇÃO: {e}")
                return False
        else:
            self.logger.warning(f"ALVO INEXISTENTE: {email} não encontrado.")
            return False
