import threading

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import FSInputFile, Message

from bot.botcontroller import BotController
from bot.control.interaction import find_and_click, to_main
from bot.game.game import run_game_bot
from bot.screen import get_screen_shot  # или другой метод
from bot.settings import Settings, get_settings, reset_settings
from bot.telegram.state import notification_queue
from bot.utility import save_cv_image

router = Router()

_controller: BotController = None
_settings: Settings = None


def register_handlers(dp, allowed_user_id: int, controller: BotController):
    global _controller
    _controller = controller

    global _settings
    _settings = get_settings()

    dp.include_router(router)

    @router.message(CommandStart())
    async def cmd_start(message: Message):
        if message.from_user.id != allowed_user_id:
            await message.answer("⛔ Доступ запрещён")
            return
        if _controller.is_game_running():
            notification_queue.put_nowait("⚠️ Бот уже запущен.")
            return
        reset_settings()
        _controller.start()
        threading.Thread(target=run_game_bot, args=(_controller,), daemon=True).start()
        await message.answer("✅ Бот запущен.")

    @router.message(Command("stop"))
    async def cmd_stop(message: Message):
        if message.from_user.id != allowed_user_id:
            await message.answer("⛔ Доступ запрещён")
            return
        if not _controller.is_game_running():
            notification_queue.put_nowait("⚠️ Бот уже остановлен.")
            return
        _controller.stop()
        await message.answer("🛑 Бот остановлен.")
        # Здесь можно вставить хук для graceful shutdown

    @router.message(Command("to_main"))
    async def cmd_to_main(message: Message):
        if message.from_user.id != allowed_user_id:
            await message.answer("⛔ Доступ запрещён")
            return
        to_main()
        await message.answer("🔄 Перешёл в главное меню.")

    @router.message(Command("find_and_click"))
    async def cmd_find_and_click(message: Message):
        if message.from_user.id != allowed_user_id:
            await message.answer("⛔ Доступ запрещён")
            return
        parts = message.text.strip().split()

        if len(parts) != 2:
            await message.answer(
                "⚠️ Пожалуйста, укажите название элемента: /find_and_click <название>"
            )
            return
        result = find_and_click(parts[1])
        if result is not None:
            await message.answer(f"✅ Найдено и кликнуто: {parts[1]}")
        else:
            await message.answer(f"❌ Не удалось найти элемент: {parts[1]}")

    @router.message(Command("screenshot"))
    async def cmd_screenshot(message: Message):
        if message.from_user.id != allowed_user_id:
            await message.answer("⛔ Доступ запрещён")
            return
        try:
            _settings.invalidate_screeenshot_cache()
            screenshot = get_screen_shot(cache=False)  # Сохраняем скриншот в кэш
            save_cv_image("tg_screenshot", screenshot)
            photo = FSInputFile("./bot/data/tg_screenshot.png")
            await message.answer_photo(photo=photo)
        except TelegramBadRequest:
            await message.answer("❌ Не удалось отправить скриншот.")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")

    @router.message(Command("last_screenshot"))
    async def cmd_last_screenshot(message: Message):
        if message.from_user.id != allowed_user_id:
            await message.answer("⛔ Доступ запрещён")
            return
        try:
            photo = FSInputFile("./bot/data/last_screenshot.png")
            await message.answer_photo(photo=photo)
        except TelegramBadRequest:
            await message.answer("❌ Не удалось отправить скриншот.")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")


def exception_handler(exc: Exception):
    msg = f"🚨 Game bot crashed:\n<pre>{str(exc)}</pre>"
    # Добавляем в очередь
    notification_queue.put_nowait(msg)
