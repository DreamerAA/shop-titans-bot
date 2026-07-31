import argparse
import threading
import traceback

from bot.botcontroller import BotController
from bot.game.game import run_game_bot
from bot.settings import get_settings
from bot.telegram.client import run_telegram_bot
from bot.telegram.commands import exception_handler


def run_telegram(controller: BotController):
    print("📱 Starting Telegram bot...")
    settings = get_settings()
    run_telegram_bot(
        token=settings.telegram_token,
        allowed_user_id=settings.allowed_user_id,
        controller=controller,
    )


def run_game(controller: BotController):
    print("🎮 Starting game bot...")
    run_game_bot(controller)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run Shop Titans bot")
    parser.add_argument(
        "--config", type=str, default="configs/template.yaml", help="Path to config file"
    )

    args = parser.parse_args()

    # Пример: использовать путь до конфига
    settings = get_settings(config_path=args.config)
    controller = BotController(args.config)

    controller.set_exception_callback(exception_handler)

    try:
        if settings.telegram_token:

            # Поток 1: игровой бот
            threading.Thread(target=run_game, args=(controller,), daemon=True).start()

            # Поток 2: Telegram бот (блокирующий)
            run_telegram(controller)
        else:
            print("⚠️ Telegram token is not set. Running only game bot.")
            run_game(controller)

    except KeyboardInterrupt:
        print("🛑 Bot was manually stopped by user.")

    except Exception as e:
        print("❌ Bot encountered an unexpected error: ", str(e))
        print(traceback.format_exc())
