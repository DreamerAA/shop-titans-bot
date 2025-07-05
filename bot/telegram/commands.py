from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.controller import BotController
from bot.screen import get_screen_shot  # или другой метод
from bot.settings import get_settings
from bot.telegram.state import notification_queue

router = Router()

_controller: BotController = None


def register_handlers(dp, allowed_user_id: int, controller: BotController):
    global _controller
    _controller = controller

    dp.include_router(router)
    settings = get_settings()

    @router.message(CommandStart())
    async def cmd_start(message: Message):
        if message.from_user.id != allowed_user_id:
            await message.answer("⛔ Доступ запрещён")
            return

        await message.answer("✅ Бот запущен. Введите /help для списка команд.")

    @router.message(Command("stop"))
    async def cmd_stop(message: Message):
        if message.from_user.id != allowed_user_id:
            await message.answer("⛔ Доступ запрещён")
            return
        _controller.stop()
        await message.answer("🛑 Бот будет остановлен (пока не реализовано).")
        # Здесь можно вставить хук для graceful shutdown

    @router.message(Command("screenshot"))
    async def cmd_screenshot(message: Message):
        if message.from_user.id != allowed_user_id:
            await message.answer("⛔ Доступ запрещён")
            return
        try:
            img_path = get_screen_shot()
            await message.answer_photo(photo=img_path)
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
            img = settings.get_screenshot_cached()
            await message.answer_photo(photo=img)
        except TelegramBadRequest:
            await message.answer("❌ Не удалось отправить скриншот.")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")


def exception_handler(exc: Exception):
    msg = f"🚨 Game bot crashed:\n<pre>{str(exc)}</pre>"
    # Добавляем в очередь
    notification_queue.put_nowait(msg)
