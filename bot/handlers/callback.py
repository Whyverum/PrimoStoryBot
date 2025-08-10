from typing import Optional

from aiogram import Router, F
from aiogram.types import CallbackQuery
from bot.core import storage

router: Router = Router(name="callback_router")

@router.callback_query(F.data.startswith("bt_"))
@router.callback_query(F.data.startswith("show_alert_"))
async def handle_button_alert(callback_query: CallbackQuery) -> None:
    key: Optional[str] = callback_query.data
    user_id: int = callback_query.from_user.id

    # Получаем уведомление через хранилище
    notif = storage.get_notification(key)
    if not notif:
        await callback_query.answer()
        return

    # Проверяем права доступа
    allowed = notif.get("allowed_ids")
    if allowed and user_id not in allowed:
        msg = notif.get("unauthorized_message", "У вас нет доступа к этому уведомлению.")
        await callback_query.answer(text=msg, show_alert=True)
        return

    text = notif.get("text", "")
    show_alert = notif.get("show_alert", False)

    try:
        await callback_query.answer(text=text, show_alert=show_alert)
    except Exception:
        await callback_query.answer(text="Произошла ошибка при отображении уведомления.", show_alert=True)


@router.callback_query(F.data == "void")
async def handle_void_callback(callback_query: CallbackQuery) -> None:
    """
    Обработка пустых callback-запросов (void).
    Просто отвечает на callback без уведомления.
    """
    try:
        await callback_query.answer()
    except Exception:
        return
