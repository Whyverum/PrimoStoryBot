from math import ceil
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardButton, InlineKeyboardMarkup,
    SwitchInlineQueryChosenChat, CopyTextButton
)
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.markdown import hide_link

from BotCode.core.storage import storage
from BotCode.utils.pagination import create_pagination_buttons
from BotCode.utils import textmd2
from BotCode.config import PARSE_MODE

router = Router(name="posts_manager")

PAGE_SIZE = 5

async def send_posts_list(
    message: Message = None,
    callback_query: CallbackQuery = None,
    page: int = 0
) -> None:
    """Отправляет список постов пользователя с пагинацией."""
    user_id = message.from_user.id if message else callback_query.from_user.id
    posts = storage.load_user_posts(user_id)

    if not posts:
        msg = "Нет сохранённых постов."
        if message:
            await message.answer(msg)
        else:
            await callback_query.answer(msg, show_alert=True)
        return

    post_ids = list(posts.keys())
    total = len(post_ids)
    pages = ceil(total / PAGE_SIZE)
    page = max(0, min(page, pages - 1))

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    current_ids = post_ids[start:end]

    rows: list[list[InlineKeyboardButton]] = []
    for pid in current_ids:
        post = posts[pid]
        priv = "🔒" if post.get("private") else "🔓"
        btn = InlineKeyboardButton(
            text=f"{priv} Пост {pid}",
            callback_data=f"view_post_{pid}"
        )
        rows.append([btn])

    # Пагинация
    nav_buttons = create_pagination_buttons(
        action="open_post_list",
        page=page,
        total_posts=total,
        bt_page=PAGE_SIZE
    )
    if nav_buttons:
        rows.append(nav_buttons)

    # Кнопка закрытия
    rows.append([InlineKeyboardButton(text="Закрыть❌", callback_data="cancel_list")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)
    header = "Список ваших постов:"

    try:
        if callback_query:
            await callback_query.message.edit_text(header, reply_markup=keyboard)
        else:
            await message.answer(header, reply_markup=keyboard)
    except TelegramBadRequest:
        if callback_query:
            await callback_query.message.delete()
            await callback_query.message.answer(header, reply_markup=keyboard)
        else:
            await message.answer(header, reply_markup=keyboard)

# --- Хендлеры списка ---
@router.message(F.text.lower() == "посмотреть список📋")
async def cmd_list(message: Message):
    await send_posts_list(message=message)

@router.callback_query(F.data == "open_post_list")
async def cb_open_list(cq: CallbackQuery):
    await send_posts_list(callback_query=cq)
    await cq.answer()

@router.callback_query(lambda c: c.data and c.data.startswith("open_post_list_page_"))
async def cb_paginate(cq: CallbackQuery):
    try:
        page = int(cq.data.rsplit("_", 1)[-1])
    except ValueError:
        await cq.answer("Некорректная страница", show_alert=True)
        return
    await send_posts_list(callback_query=cq, page=page)
    await cq.answer()

@router.callback_query(F.data == "cancel_list")
async def cb_cancel(cq: CallbackQuery):
    await cq.message.delete()
    await cq.answer()

# --- Просмотр отдельного поста ---
@router.callback_query(lambda c: c.data and c.data.startswith("view_post_"))
async def view_post_callback(cq: CallbackQuery):
    pid = cq.data.replace("view_post_", "")
    uid = cq.from_user.id
    posts = storage.load_user_posts(uid)
    if pid not in posts:
        await cq.answer("Пост не найден", show_alert=True)
        return

    post = posts[pid]
    text = textmd2(post.get("text", ""))
    img = post.get("image", "")
    if img.startswith("http"):
        text = f"{hide_link(img)}{text}"

    rows: list[list[InlineKeyboardButton]] = []
    for row in post.get("buttons", []):
        btns: list[InlineKeyboardButton] = []
        for b in row:
            if "copy_text" in b:
                btns.append(
                    InlineKeyboardButton(
                        text=b["text"],
                        copy_text=CopyTextButton(text=b["copy_text"])
                    )
                )
            elif "switch_inline_query" in b:
                btns.append(
                    InlineKeyboardButton(
                        text=b["text"],
                        switch_inline_query=b["switch_inline_query"]
                    )
                )
            elif "switch_inline_query_current_chat" in b:
                btns.append(
                    InlineKeyboardButton(
                        text=b["text"],
                        switch_inline_query_current_chat=b["switch_inline_query_current_chat"]
                    )
                )
            elif "switch_inline_query_chosen_chat" in b:
                raw = b["switch_inline_query_chosen_chat"]
                cfg = raw if isinstance(raw, dict) else {
                    "query": raw,
                    "allow_user_chats": True
                }
                btns.append(
                    InlineKeyboardButton(
                        text=b["text"],
                        switch_inline_query_chosen_chat=SwitchInlineQueryChosenChat(**cfg)
                    )
                )
            elif "url" in b:
                url = b["url"]
                if url.lower().endswith("void"):
                    btns.append(
                        InlineKeyboardButton(text=b["text"], callback_data="void")
                    )
                else:
                    btns.append(
                        InlineKeyboardButton(text=b["text"], url=url)
                    )
            elif "callback_data" in b:
                btns.append(
                    InlineKeyboardButton(text=b["text"], callback_data=b["callback_data"])
                )
        if btns:
            rows.append(btns)

    # Удалить / назад
    rows.append([
        InlineKeyboardButton(text="Удалить❌", callback_data=f"delete_post_{pid}"),
        InlineKeyboardButton(text="Назад◀️", callback_data="open_post_list")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)

    await cq.message.answer(text=text, reply_markup=keyboard, parse_mode=PARSE_MODE)
    await cq.message.delete()
    await cq.answer()

# --- Удаление поста ---
@router.callback_query(lambda c: c.data and c.data.startswith("delete_post_"))
async def delete_post_callback(cq: CallbackQuery):
    pid = cq.data.replace("delete_post_", "")
    uid = cq.from_user.id
    if storage.delete_user_post(uid, pid):
        await cq.answer(f"Пост {pid} удалён")
        await send_posts_list(callback_query=cq)
    else:
        await cq.answer("Не удалось удалить пост", show_alert=True)
