# BotCode/handlers/inline.py
from aiogram import Router
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InputTextMessageContent,
    InlineQueryResultArticle,
    SwitchInlineQueryChosenChat,
    CopyTextButton,
)
from aiogram.utils.markdown import hide_link

from bot.core import storage
from bot.loggers import logs

router: Router = Router(name="inline_send")



def build_markup(buttons_def: list[list[dict]]) -> InlineKeyboardMarkup | None:
    """
    Создаёт InlineKeyboardMarkup из списка описаний кнопок.
    Поддерживает URL, callback, inline-моды.
    Обрабатывает "void"-кнопки как callback_data="void".
    Для switch_inline_query_chosen_chat устанавливает хотя бы один allow_* True.
    """
    if not buttons_def:
        return None

    rows: list[list[InlineKeyboardButton]] = []
    for row_idx, row in enumerate(buttons_def):
        if not isinstance(row, list):
            logs.warning(f"Некорректный формат ряда кнопок: {row}")
            continue

        kb_row: list[InlineKeyboardButton] = []
        for col_idx, b in enumerate(row):
            if not isinstance(b, dict):
                logs.warning(f"Некорректный формат кнопки в ряду {row_idx}: {b}")
                continue

            text = b.get("text", "")
            if not text:
                logs.warning(f"Пустой текст кнопки в ряду {row_idx}, колонке {col_idx}")
                continue

            btn = None
            try:
                if "url" in b:
                    url = b["url"]
                    if url.lower().endswith("void"):
                        btn = InlineKeyboardButton(text=text, callback_data="void")
                    else:
                        btn = InlineKeyboardButton(text=text, url=url)
                elif "switch_inline_query" in b:
                    btn = InlineKeyboardButton(
                        text=text,
                        switch_inline_query=b["switch_inline_query"]
                    )
                elif "switch_inline_query_current_chat" in b:
                    btn = InlineKeyboardButton(
                        text=text,
                        switch_inline_query_current_chat=b["switch_inline_query_current_chat"]
                    )
                elif "switch_inline_query_chosen_chat" in b:
                    query = b["switch_inline_query_chosen_chat"]
                    if isinstance(query, dict):
                        siqcc = SwitchInlineQueryChosenChat(
                            query=query.get("query", ""),
                            allow_user_chats=query.get("allow_user_chats", True),
                            allow_group_chats=query.get("allow_group_chats", True),
                            allow_channel_chats=query.get("allow_channel_chats", True),
                            allow_bot_chats=query.get("allow_bot_chats", False),
                        )
                    else:
                        siqcc = SwitchInlineQueryChosenChat(
                            query=query,
                            allow_user_chats=True,
                            allow_group_chats=True,
                            allow_channel_chats=True,
                            allow_bot_chats=False,
                        )
                    btn = InlineKeyboardButton(
                        text=text,
                        switch_inline_query_chosen_chat=siqcc
                    )
                elif "copy_text" in b:
                    btn = InlineKeyboardButton(
                        text=text,
                        copy_text=CopyTextButton(text=b["copy_text"])
                    )
                elif "callback_data" in b:
                    btn = InlineKeyboardButton(
                        text=text,
                        callback_data=b["callback_data"]
                    )
            except Exception as e:
                logs.error(f"Ошибка при создании кнопки в ряду {row_idx}, колонке {col_idx}: {e}")
                continue

            if btn:
                kb_row.append(btn)

        if kb_row:
            rows.append(kb_row)

    if not rows:
        return None

    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    """
    Обрабатывает инлайн-запросы для поиска и отправки постов.
    Фильтрует посты по приватности и поисковому запросу.
    """
    # Перезагружаем все посты из файлов на случай изменений
    storage.load_all_posts()

    query = inline_query.query or ""
    user_id = inline_query.from_user.id
    username = inline_query.from_user.username or f"user_{user_id}"

    logs.debug(f"Получен инлайн-запрос от {username} (ID: {user_id}): {query}")

    results = []
    for post_id, post in storage.global_posts.items():
        try:
            # Проверка приватности
            if post.get("private") and post.get("user_id") != user_id:
                continue

            # Проверка поискового запроса
            if query and query.lower() not in post_id.lower():
                continue

            # Тело сообщения
            text = post.get("text", "")
            image = post.get("image", "")
            if image and image.startswith("http"):
                text = f"{hide_link(image)}{text}"

            # Клавиатура
            markup = build_markup(post.get("buttons", []))

            results.append(
                InlineQueryResultArticle(
                    id=post_id,
                    title=f"Пост {post_id}",
                    description=(post.get("text", "")[:100] + "...") if len(post.get("text", "")) > 100 else post.get(
                        "text", ""),
                    input_message_content=InputTextMessageContent(message_text=text),
                    reply_markup=markup
                )
            )
        except Exception as e:
            logs.error(f"Ошибка при обработке поста {post_id}: {e}")
            continue

    logs.info(f"Отправлено {len(results)} результатов для запроса '{query}' от {username} (ID: {user_id})")

    try:
        await inline_query.answer(results, cache_time=0, is_personal=True)
    except Exception as e:
        logs.error(f"Ошибка при отправке результатов инлайн-запроса: {e}")


__all__ = [
    'router',
    'inline_query_handler'
]
