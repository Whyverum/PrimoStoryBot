# bot/keyboards/decision.py

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Настройка экспорта
__all__ = ("get_decision_keyboard",)

def get_decision_keyboard(thread_id: int, kind: str) -> InlineKeyboardMarkup:
    """
    Создание клавиатуры принять\отклонить.

    :param thread_id: Айди запроса.
    :param kind: Вид предполагаемого действия.
    :return: Разметку клавиатуры для сообщения бота.
    """
    ikb: InlineKeyboardBuilder = InlineKeyboardBuilder()
    ikb.row(
        InlineKeyboardButton(text="✅ Принять", callback_data=f"{kind}:accept:{thread_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"{kind}:reject:{thread_id}")
    )
    return ikb.as_markup()
