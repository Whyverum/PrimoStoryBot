# main.py
# Основной код проекта, который и соединяет в себе все его возможности

from asyncio import run
from middleware.loggers import setup_logging
from bot import *

async def main() -> None:
    """Входная точка проекта. Запуск бота."""
    # Запуск логирования
    setup_logging()

    # Получение информации о боте
    await BotInfo.setup(bot)

    # Подключение главного маршрутизатора
    dp.include_router(router)

    # Включение опроса бота
    await dp.start_polling(bot)


# Вечная загрузка бота
if __name__ == "__main__":
    run(main())
