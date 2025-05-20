# main.py
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from BotCode.config import BOT_TOKEN, BOT_DEBUG_TOKEN, DEBUG_MODE, PARSE_MODE

dp: Dispatcher = Dispatcher()
TOKEN: str = BOT_DEBUG_TOKEN if DEBUG_MODE else BOT_TOKEN
bot: Bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(
        parse_mode=PARSE_MODE,
        link_preview_show_above_text=True,
    )
)

async def main() -> None:
    from aiogram.types import User
    from BotCode.loggers import logs
    from BotCode.handlers import router as main_router

    bot_info: User = await bot.get_me()
    logs.start(text=f"Бот @{bot_info.username} запущен!")

    dp.include_router(main_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    from asyncio import run
    run(main())
