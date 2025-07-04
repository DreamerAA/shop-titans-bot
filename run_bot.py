import time
from logic.status import check_reconnect
from logic.production import assemble_products, set_split_production, set_one_production
from logic.trading import step_trading
from settings import settings


def run_bot():
    wait_time_minutes = 2
    while True:
        check_reconnect()
        print("Trading...")
        step_trading()
        print("Assembling products...")
        assemble_products()

        # set_split_production(
        #     [
        #         ("obj/eclipse", 2),
        #         ("obj/snake_blood_ointment", 2),
        #         ("obj/corsair_boots", 2),
        #     ]
        # )
        print("Setting one production...")
        set_one_production(
            [
                # "moonstone/perfect",
                "moonstone/excellent",
                # "obj/stone_crusher",
                # "obj/sword_damocles",
                # "obj/snake_elixir",
                # "obj/pliers_ash_like",
                "obj/archivist_glasses",
                # "obj/grimoire_collection",
                #         "moonstone/big",
            ]
        )
        print(f"Waiting {wait_time_minutes} minutes...")
        time.sleep(60 * wait_time_minutes)


try:
    print("mouse.position: ", settings.mouse.position)
    run_bot()


except KeyboardInterrupt:
    print("🛑 Бот остановлен.")
