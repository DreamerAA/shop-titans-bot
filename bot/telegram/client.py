import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from bot.botcontroller import BotController
from bot.telegram.commands import register_handlers
from bot.telegram.state import notification_queue


def run_telegram_bot(token: str, allowed_user_id: int, controller: BotController):
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    register_handlers(dp, allowed_user_id, controller)

    async def start():
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="Старт работы"),
                BotCommand(command="stop", description="Остановить бота"),
                BotCommand(command="screenshot", description="Сделать скриншот"),
                BotCommand(command="to_main", description="Клик в центре экрана"),
                BotCommand(command="find_and_click", description="Найти и кликнуть"),
                BotCommand(command="last_screenshot", description="Последний скриншот"),
            ]
        )
        await asyncio.gather(dp.start_polling(bot), telegram_notifier(bot, allowed_user_id))

    asyncio.run(start())


async def telegram_notifier(bot: Bot, allowed_user_id: int):
    while True:
        message = await notification_queue.get()
        try:
            await bot.send_message(chat_id=allowed_user_id, text=message)
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения в Telegram: {e}")
