# BotCode/utils/pagination.py
from typing import List
from aiogram.types import InlineKeyboardButton

# Настройка экспорта в модули
__all__ = ('create_pagination_buttons',)

def create_pagination_buttons(action: str,
                              page: int = 0,
                              total_posts: int = 0,
                              bt_page: int = 5) -> List[InlineKeyboardButton]:
    """Создает кнопки для пагинации."""
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(
            text="←", callback_data=f"{action}_page_{page - 1}"
        ))
    if (page + 1) * bt_page < total_posts:
        navigation_buttons.append(InlineKeyboardButton(
            text="→", callback_data=f"{action}_page_{page + 1}"
        ))
    return navigation_buttons
