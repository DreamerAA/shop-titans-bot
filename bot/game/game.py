import time

from bot.botcontroller import BotController
from bot.core.production import assemble_products, set_one_production, set_split_production
from bot.core.status import check_reconnect
from bot.core.trading import step_trading
from bot.settings import get_settings  # Инициализация настроек


def run_game_bot(controller: BotController):
    settings = get_settings()  # Инициализация настроек
    list_one_production = [
        # Примеры шаблонов. Уберите комментарии с нужных строк
        # или добавьте свои.
        "moonstone/perfect",
        # "obj/accessories/spicy_granite",
        # "obj/armor/centurion_armor",
        # "obj/accessories/comfortable_pendant",
        "obj/armor/ash_trees",
        # "moonstone/perfect",
        # "moonstone/big",
        # "obj/weapon/kunai",
    ]
    list_split_production = [
        #     ("obj/armor/corsair_gloves", 2),
        #     ("obj/armor/juggernaut_furnace", 2),
        #     ("obj/weapon/stellaria", 2),
    ]
    try:
        controller.set_game_running(True)
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
            if len(list_split_production) > 0:
                print("🔨 Setting split production...")
                set_split_production(list_split_production)
            if controller.should_stop():
                print("🛑 Stopping trading cycle as per user request.")
                break

            # Вариант 2: one production — использовать, если вы хотите производить
            # только один тип товара.
            if len(list_one_production) > 0:
                print("🔨 Setting one production...")
                set_one_production(list_one_production)

            if controller.should_stop():
                print("🛑 Stopping trading cycle as per user request.")
                break
            print(f"⏳ Waiting {settings.wt_cycle_min} minutes before next cycle...")
            settings.invalidate_screeenshot_cache()  # Очистка кэша скриншота перед следующим циклом
            time.sleep(60 * settings.wt_cycle_min)
        controller.set_game_running(False)
    except Exception as e:
        controller.set_game_running(False)  # Устанавливаем флаг остановки игры
        print("❌ Bot encountered an unexpected error: ", str(e))
        controller.notify_exception(e)
