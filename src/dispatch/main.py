import time
import json
from datetime import datetime
from utils.logger import setup_logger
from api.connector import MicrosoftConnector

# -- PARAMETRIZAÇÃO --
CONFIG_PATH = "config/targets.json"

def load_intel():
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def main():
    logger = setup_logger()
    logger.info("SYSTEM BOOT. Inicializando integração...")

    # Carrega informações
    config = load_intel()
    if not config:
        logger.critical("INTEL MISSING. config/targets. não encontrado. Abortando.")
        return

    trigger_time = config['mission_config']['trigger_time']
    logger.info(f"ENVIO SETADO. Tempo: {trigger_time} diario.")

    comms = MicrosoftConnector(logger)
    comms.authenticate()

    mission_accomplished_today = False

    try:
        while True:
            now = datetime.now()
            current_time = now.strftime("%H:%M")

            if current_time == trigger_time:
                if not mission_accomplished_today:
                    logger.info("H-HOUR CHEGOU. Executando ordens.")

                    for operative in config['operatives']:
                        email = operative['email']

                        # Phase 1: Identify
                        target_id = comms.find_user_id(email)

                        # Phase 2: Engage
                        if target_id:
                            comms.send_dispatch(target_id, "TEAMS_MESSAGE")
                            comms.send_dispatch(target_id, "EMAIL_ALERT")
                        else:
                            logger.warning(f"Alvo {email} desconhecido. Não pode ser localizado.")

                    mission_accomplished_today = True
                    logger.info("COMPLETO. Se preparando para o proximo ciclo.")

            else:
                if current_time != trigger_time:
                    mission_accomplished_today = False

            time.sleep(30)

    except KeyboardInterrupt:
        logger.info("MANUAL OVERRIDE. Sistema desligando.")
    except Exception as e:
        logger.error(f"SYSTEM FAILURE: {str(e)}")
        raise e

if __name__ == "__main__":
    main()
