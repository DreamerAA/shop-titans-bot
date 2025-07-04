import time
import traceback

from bot.core.production import set_split_production  # noqa: E501
from bot.core.production import assemble_products, set_one_production
from bot.core.status import check_reconnect
from bot.core.trading import step_trading
from bot.settings import settings


def run_bot():
    while True:
        # Проверка на диалог переподключения
        check_reconnect()

        print("🔁 Starting trading cycle...")
        step_trading()

        print("🛠 Assembling products...")
        assemble_products()

        # Выберите одну из стратегий запуска производства:
        # Вариант 1: split production — использовать, если вы хотите делить
        # производственные мощности на разные товары.
        # Раскомментируйте и укажите нужные пары (путь до шаблона, количество).
        set_split_production(
            [
                # ("obj/eclipse", 2),
                # ("obj/snake_blood_ointment", 2),
                # ("obj/corsair_boots", 2),
            ]
        )

        # Вариант 2: one production — использовать, если вы хотите производить
        # только один тип товара.
        set_one_production(
            [
                # Примеры шаблонов. Уберите комментарии с нужных строк
                # или добавьте свои.
                # "moonstone/perfect",
                "moonstone/excellent",
                # "obj/stone_crusher",
                # "obj/sword_damocles",
                # "obj/snake_elixir",
                # "obj/pliers_ash_like",
                "obj/archivist_glasses",
                # "obj/grimoire_collection",
                # "moonstone/big",
            ]
        )

        print(f"⏳ Waiting {settings.wt_cycle_min} minutes before next cycle...")
        time.sleep(60 * settings.wt_cycle_min)


if __name__ == "__main__":
    try:
        print("🖱 Mouse position on start:", settings.mouse.position)
        run_bot()

    except KeyboardInterrupt:
        print("🛑 Bot was manually stopped by user.")

    except Exception as e:
        print("❌ Bot encountered an unexpected error: ", str(e))
        print(traceback.format_exc())
        # TODO: В будущем можно вставить уведомление в Telegram или лог-файл
        # send_error_to_telegram(traceback.format_exc())  # <- пример
