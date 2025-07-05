import argparse

from bot.settings import get_settings  # можно переопределить для Telegram, если нужно
from bot.telegram.client import run_telegram_bot

# Пример запуска напрямую (можно отключить при запуске как модуль)
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run Shop Titans bot")
    parser.add_argument(
        "--config", type=str, default="configs/template.yaml", help="Path to config file"
    )

    args = parser.parse_args()

    settings = get_settings(config_path=args.config)
    run_telegram_bot(token=settings.telegram_token, allowed_user_id=settings.allowed_user_id)
