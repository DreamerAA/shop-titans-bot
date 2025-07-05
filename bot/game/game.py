import time

from bot.controller import BotController

# from bot.core.production import set_split_production  # noqa: E501
from bot.core.production import assemble_products, set_one_production
from bot.core.status import check_reconnect
from bot.core.trading import step_trading
from bot.settings import get_settings  # Инициализация настроек


def run_game_bot(controller: BotController):
    settings = get_settings()  # Инициализация настроек
    try:
        while not controller.should_stop():
            # Проверка на диалог переподключения
            check_reconnect()

            print("🔁 Starting trading cycle...")
            step_trading()
            if controller.should_stop():
                print("🛑 Stopping trading cycle as per user request.")
                break

            print("🛠 Assembling products...")
            assemble_products()

            if controller.should_stop():
                print("🛑 Stopping trading cycle as per user request.")
                break

            # Выберите одну из стратегий запуска производства:
            # Вариант 1: split production — использовать, если вы хотите делить
            # производственные мощности на разные товары.
            # Раскомментируйте и укажите нужные пары (путь до шаблона, количество).
            # set_split_production(
            #     [
            #         # ("obj/eclipse", 2),
            #         # ("obj/snake_blood_ointment", 2),
            #         # ("obj/corsair_boots", 2),
            #     ]
            # )
            # if controller.should_stop():
            #     print("🛑 Stopping trading cycle as per user request.")
            #     break

            # Вариант 2: one production — использовать, если вы хотите производить
            # только один тип товара.
            set_one_production(
                [
                    # Примеры шаблонов. Уберите комментарии с нужных строк
                    # или добавьте свои.
                    # "moonstone/perfect",
                    # "moonstone/excellent",
                    # "obj/sword_damocles",
                    # "obj/pliers_ash_like",
                    "obj/snake_elixir",
                    "obj/archivist_glasses",
                    "obj/stone_crusher",
                    # "obj/grimoire_collection",
                    # "moonstone/big",
                ]
            )
            if controller.should_stop():
                print("🛑 Stopping trading cycle as per user request.")
                break
            print(f"⏳ Waiting {settings.wt_cycle_min} minutes before next cycle...")
            settings.invalidate_screeenshot_cache()  # Очистка кэша скриншота перед следующим циклом
            time.sleep(60 * settings.wt_cycle_min)
    except Exception as e:
        print("❌ Bot encountered an unexpected error: ", str(e))
        controller.notify_exception(e)
