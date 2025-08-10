"""
Модуль логирования для Telegram-бота.

Особенности:
* Вывод логов в консоль и/или файл
* Автоматическая ротация и удержание
* Форматирование с информацией о системе, типе события и пользователе
* Удобные методы для разных уровней логирования
"""

from sys import stderr
from pathlib import Path
from typing import Optional, Final, Union

from loguru import logger
from aiogram.types import Message, User

try:
    from configs.config import LogConfig
except ImportError:
    class LogConfig:
        """Запасные настройки логирования, если config недоступен."""
        CONSOLE: Final[bool] = True
        FILE: Final[bool] = True
        DIR: Final[Path] = Path('Logs')
        ROTATION: Final[str] = '100 MB'
        RETENTION: Final[str] = '7 days'

# Настройка экспорта в модули
__all__ = ['Logs', 'logs']


class Logs:
    """
    Класс для работы с логированием через loguru.
    """
    _SYSTEM_NAME: Final[str] = 'PRIMO'  # Исправлено: убран обратный слэш
    _LOG_FORMAT: Final[str] = (
        '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> <red>|</red> '  # Исправлено форматирование времени
        '<blue>{extra[system]}-{extra[log_type]}</blue> <red>| '
        '{extra[user]} |</red> <level>{message}</level>'
    )

    @staticmethod
    def _format_user(message: Optional[Message]) -> str:
        """
        Форматирует информацию о пользователе из сообщения.
        """
        if not message or not message.from_user:
            return '@System'
        user: User = message.from_user
        return f"@{user.username}" if user.username else f"id{user.id}"

    @classmethod
    def _log(cls,
             level: Union[str, int],
             text: str,
             log_type: str,
             message: Optional[Message] = None) -> None:
        """Внутренний метод логирования."""
        user_ctx = cls._format_user(message)
        logger.bind(
            system=cls._SYSTEM_NAME,
            user=user_ctx,
            log_type=log_type,
        ).log(level, text)

    @classmethod
    def setup(cls, start: bool = True) -> None:
        """Инициализация логирования: консоль и/или файл."""
        logger.remove()

        # Консольный вывод
        if getattr(LogConfig, 'CONSOLE', False):
            logger.add(
                stderr,
                format=cls._LOG_FORMAT,
                colorize=True,
                level='DEBUG',
                filter=lambda rec: rec['extra'].get('log_type') != 'DEBUG'
            )

        # Файловый вывод с ротацией
        if getattr(LogConfig, 'FILE', False):
            log_dir = getattr(LogConfig, 'DIR', Path('logs'))
            log_dir.mkdir(parents=True, exist_ok=True)
            logger.add(
                log_dir / 'bot.log',
                rotation=getattr(LogConfig, 'ROTATION', '100 MB'),
                retention=getattr(LogConfig, 'RETENTION', '7 days'),
                format=cls._LOG_FORMAT,
                level='DEBUG',
                enqueue=True,
                backtrace=True,
                diagnose=True
            )

        # Добавляем вызов start() если нужно
        if start:
            cls.start()

    @classmethod
    def start(cls, text: str = 'Запуск бота...', log_type: str = 'START') -> None:
        """Логирование старта приложения."""
        cls._log(level='INFO', text=text, log_type=log_type)

    @classmethod
    def debug(cls,
              text: str,
              log_type: str = 'DEBUG',
              message: Optional[Message] = None) -> None:
        cls._log(level='DEBUG', text=text, log_type=log_type, message=message)

    @classmethod
    def info(cls,
             text: str,
             log_type: str = 'INFO',
             message: Optional[Message] = None) -> None:
        cls._log(level='INFO', text=text, log_type=log_type, message=message)

    @classmethod
    def warning(cls,
                text: str,
                log_type: str = 'WARNING',
                message: Optional[Message] = None) -> None:
        cls._log(level='WARNING', text=text, log_type=log_type, message=message)

    @classmethod
    def error(cls,
              text: str,
              log_type: str = 'ERROR',
              message: Optional[Message] = None) -> None:
        cls._log(level='ERROR', text=text, log_type=log_type, message=message)

    @classmethod
    def exception(cls,
                  text: str,
                  exception: Exception,
                  log_type: str = 'EXCEPTION',
                  message: Optional[Message] = None) -> None:
        full_text = f"{text}\nException: {exception!r}"
        cls._log(level='ERROR', text=full_text, log_type=log_type, message=message)


# Инициализация экземпляра логгера
logs = Logs()
logs.setup()
