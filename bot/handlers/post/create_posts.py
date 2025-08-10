# bot/modules/create_post.py
import re
import uuid
from threading import Lock

from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from bot.core import storage

router: Router = Router(name="create_post_router")


class PostState(StatesGroup):
    waiting_for_text = State()
    waiting_for_privacy = State()
    waiting_for_id = State()
    waiting_for_image = State()
    waiting_for_buttons = State()
    preview = State()
    editing_choice = State()


post_id_lock: Lock = Lock()


# --- Utility functions ---
def make_inline_markup(rows: list[list[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cancel_button() -> InlineKeyboardMarkup:
    return make_inline_markup([[InlineKeyboardButton(text="Отмена", callback_data="cancel_creation")]])


def privacy_markup(is_private: bool) -> InlineKeyboardMarkup:
    toggle = InlineKeyboardButton(
        text="🔒 Приватный" if is_private else "🔓 Публичный",
        callback_data="toggle_privacy"
    )
    cont = InlineKeyboardButton(text="Продолжить ➡️", callback_data="continue_creation")
    return make_inline_markup([[toggle], [cont]])


def parse_buttons(text: str, post_id: str) -> list[list[dict]]:
    """
    Поддерживается синтаксис:
      Текст | msg:Только для боссов | 123,456 | msg:Для всех остальных
      Текст | ntf:Без алерта | 789 | msg:Нет доступа
    """
    rows: list[list[dict]] = []
    button_index = 0

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # каждая строка может содержать несколько кнопок через ';'
        btn_texts = [b.strip() for b in line.split(';') if b.strip()]
        row: list[dict] = []

        for raw in btn_texts:
            parts = [p.strip() for p in raw.split('|')]
            if len(parts) < 2:
                raise ValueError(f"Неверный формат кнопки: '{raw}'")

            btn = {"text": parts[0]}
            primary_notification = None
            primary_alert = False
            allowed_ids = None
            unauthorized_message = None

            # обрабатываем параметры слева направо
            for part in parts[1:]:
                # URL / void
                if part == "void":
                    btn["url"] = "http://void"
                elif part.startswith("http") or part.startswith("tg://"):
                    btn["url"] = part

                # первое уведомление (msg: — с алертом)
                elif part.startswith("msg:") and primary_notification is None:
                    primary_notification = part.split(":", 1)[1]
                    primary_alert = True

                # первое уведомление без алерта
                elif part.startswith(("ntf:", "notification:")) and primary_notification is None:
                    primary_notification = part.split(":", 1)[1]
                    primary_alert = False

                # список разрешённых ID
                elif re.fullmatch(r'\d+(?:\s*,\s*\d+)*', part):
                    allowed_ids = [int(x.strip()) for x in part.split(",")]

                # второе сообщение — для неавторизованных
                elif part.startswith("msg:") and primary_notification is not None and allowed_ids is not None:
                    unauthorized_message = part.split(":", 1)[1]

                # копирование текста
                elif part.startswith("copy:"):
                    btn["callback_data"] = f"copy_{uuid.uuid4().hex}"
                    btn["copy_text"] = part.split(":", 1)[1]

                # inline-параметры
                elif part.startswith("inline:"):
                    btn["switch_inline_query"] = part.split(":", 1)[1]
                elif part.startswith("inline_current:"):
                    btn["switch_inline_query_current_chat"] = part.split(":", 1)[1]
                elif part.startswith("inline_chosen:"):
                    btn["switch_inline_query_chosen_chat"] = part.split(":", 1)[1]

                # произвольный callback_data (если ещё не задан)
                else:
                    if "callback_data" not in btn and "url" not in btn:
                        btn["callback_data"] = part

            # если было уведомление — добавляем поля
            if primary_notification is not None:
                btn["callback_data"] = f"bt_{post_id}_{button_index}"
                button_index += 1
                btn["notification"] = primary_notification
                btn["show_alert"] = primary_alert

            if allowed_ids is not None:
                btn["allowed_ids"] = allowed_ids
            if unauthorized_message is not None:
                btn["unauthorized_message"] = unauthorized_message

            # финализируем кнопку
            row.append(btn)

        if row:
            rows.append(row)

    return rows


# --- Handlers ---
@router.message(F.text == "Создать пост📔")
async def start_creation(message: Message, state: FSMContext) -> None:
    await state.set_state(PostState.waiting_for_text)
    await state.update_data(private=False, buttons=[])
    await message.reply(
        text="Отправьте текст вашего поста:\n<i>Вы также можете использовать разметку</i>(<b>жирный</b>, <i>курсив</i> и <u>прочие</u>)!",
        reply_markup=cancel_button()
        )


@router.message(PostState.waiting_for_text)
async def got_text(message: Message, state: FSMContext) -> None:
    html_text = message.html_text or message.text or message.caption or ""
    await state.update_data(text=html_text)
    await show_preview(message, state)


@router.callback_query(F.data == "toggle_privacy")
async def toggle_privacy(cq: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    is_priv = not data.get('private', False)
    await state.update_data(private=is_priv)
    await cq.message.edit_reply_markup(reply_markup=privacy_markup(is_priv))
    await cq.answer()


@router.callback_query(F.data == "continue_creation")
async def continue_to_id(cq: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PostState.waiting_for_id)
    await cq.message.edit_text(
        "Введите уникальный ID поста (латиница, цифры, подчёрки):\n<i>Совет: инициалыРП_роль_тип_номер</i>\nПример: sgrp_dottore_post_4")
    await cq.answer()


@router.message(PostState.waiting_for_id)
async def got_id(message: Message, state: FSMContext) -> None:
    pid = message.text.strip()
    if not pid.replace('_', '').isalnum():
        await message.reply(text="ID должен содержать только латиницу, цифры и подчёркивания.",
                            reply_markup=cancel_button())
        return
    with post_id_lock:
        if not storage.is_post_available(pid):
            await message.reply(text="Этот ID уже занят, введите другой:", reply_markup=cancel_button())
            return

    # Создаем клавиатуру с кнопкой "Без изображения"
    image_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚫 Без изображения", callback_data="no_image")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_creation")]
    ])

    await state.update_data(post_id=pid)
    await state.set_state(PostState.waiting_for_image)
    await message.reply(
        text="Отправьте ссылку на изображение:\nПример: https://img4.teletype.in/files/f2/47/...\n\nСовет! Сохраняйте фотографии в teletype, а после копируйте ссылку на фотографию!\n\nИли нажмите 'Без изображения'.",
        reply_markup=image_markup
    )


@router.callback_query(F.data == "no_image", PostState.waiting_for_image)
async def no_image_callback(cq: CallbackQuery, state: FSMContext):
    await state.update_data(image='')
    await state.set_state(PostState.waiting_for_buttons)
    await cq.message.delete()

    buttons_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚫 Без кнопок", callback_data="no_buttons")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_creation")]
    ])

    await cq.message.answer(
        text="""Отправьте кнопки по шаблону:
Кнопка заглушка | void
Уведомление | msg:Для вас!
Уведомление в закрепе | ntf:Сообщение
Кнопка ссылка | https://google.com
Копирование | copy:Текст для копирования

Для уведомлений с ограничением:
Уведомление | msg:Для вас! | 123,456 | msg:Для всех остальных!
Уведомление без алерта | ntf:Сообщение | 789 | msg:Нет доступа

Разделять кнопки через ;  
Кнопка1 | void ; Кнопка2 | void ; ....

Или нажмите "Без кнопок".""",
        reply_markup=buttons_markup,
        parse_mode=None
    )
    await cq.answer()


@router.message(PostState.waiting_for_image)
async def got_image(message: Message, state: FSMContext) -> None:
    img: str = message.text.strip()
    if img.lower() in ('нет', 'no', 'none', 'без изображения'):
        img: str = ''

    await state.update_data(image=img)
    await show_preview(message, state)


@router.callback_query(PostState.waiting_for_buttons, F.data == "no_buttons")
async def no_buttons_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(buttons=[])
    await show_preview(callback.message, state)
    await callback.answer()


@router.callback_query(PostState.waiting_for_buttons, F.data == "finish_buttons")
async def finish_buttons_handler(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()

    # Формируем финальные кнопки
    final = []
    for row in data.get('buttons', []):
        final_row = []
        for b in row:
            btn = {"text": b["text"]}
            if "url" in b:
                btn["url"] = b["url"]
            if "switch_inline_query" in b:
                btn["switch_inline_query"] = b["switch_inline_query"]
            if "callback_data" in b:
                btn["callback_data"] = b["callback_data"]
                if "notification" in b:
                    btn["notification"] = b["notification"]
                    btn["show_alert"] = b.get("show_alert", False)
            final_row.append(btn)
        final.append(final_row)

    await state.update_data(buttons=final)
    await show_preview(callback.message, state)
    await callback.answer()


@router.callback_query(F.data == "cancel_creation")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Создание поста отменено")
    await callback.answer()


# --- Preview and Edit Handlers ---
async def show_preview(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    text = data.get('text', '')
    image = data.get('image', '')
    buttons = data.get('buttons', [])
    private = data.get('private', False)
    post_id = data.get('post_id', '')

    # Формируем текст предпросмотра
    preview_text = f"<b>ПРЕДПРОСМОТР ПОСТА</b>\n\n{text}\n\n"
    preview_text += f"🆔 ID: <code>{post_id}</code>\n"
    preview_text += f"🔒 Приватность: {'Приватный' if private else 'Публичный'}\n"

    if image:
        preview_text += f"🖼 Изображение: {image}\n"
    else:
        preview_text += f"🖼 Изображение: отсутствует\n"

    if buttons:
        preview_text += "\n🔘 Кнопки:\n"
        for row in buttons:
            preview_text += " | ".join([btn['text'] for btn in row]) + "\n"
    else:
        preview_text += "\n🔘 Кнопки: отсутствуют\n"

    # Клавиатура предпросмотра
    preview_markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Изменить", callback_data="edit_post"),
            InlineKeyboardButton(text="Подтвердить", callback_data="confirm_post")
        ],
        [
            InlineKeyboardButton(text="Отменить создание", callback_data="cancel_creation")
        ]
    ])

    await state.set_state(PostState.preview)
    await message.answer(preview_text, reply_markup=preview_markup, disable_web_page_preview=True)


@router.callback_query(PostState.preview, F.data == "edit_post")
async def edit_post_handler(cq: CallbackQuery, state: FSMContext) -> None:
    # Клавиатура выбора поля для редактирования
    edit_markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Текст", callback_data="edit_field:text"),
            InlineKeyboardButton(text="Изображение", callback_data="edit_field:image"),
        ],
        [
            InlineKeyboardButton(text="Кнопки", callback_data="edit_field:buttons"),
            InlineKeyboardButton(text="ID", callback_data="edit_field:id"),
        ],
        [
            InlineKeyboardButton(text="Приватность", callback_data="edit_field:privacy"),
            InlineKeyboardButton(text="Назад", callback_data="back_to_preview"),
        ]
    ])

    await cq.message.edit_text("Выберите что изменить:", reply_markup=edit_markup)
    await state.set_state(PostState.editing_choice)
    await cq.answer()


@router.callback_query(PostState.editing_choice, F.data == "back_to_preview")
async def back_to_preview(cq: CallbackQuery, state: FSMContext) -> None:
    await show_preview(cq.message, state)
    await cq.answer()


@router.callback_query(PostState.editing_choice, F.data.startswith("edit_field:"))
async def handle_field_edit(cq: CallbackQuery, state: FSMContext) -> None:
    field = cq.data.split(":")[1]

    if field == "text":
        await state.set_state(PostState.waiting_for_text)
        await cq.message.edit_text("Введите новый текст поста:", reply_markup=cancel_button())

    elif field == "image":
        await state.set_state(PostState.waiting_for_image)
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚫 Без изображения", callback_data="no_image")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_creation")]
        ])
        await cq.message.edit_text(
            "Отправьте новую ссылку на изображение или нажмите 'Без изображения':",
            reply_markup=markup
        )

    elif field == "buttons":
        await state.set_state(PostState.waiting_for_buttons)
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚫 Без кнопок", callback_data="no_buttons")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_creation")]
        ])
        await cq.message.edit_text(
            "Отправьте новые кнопки по шаблону или нажмите 'Без кнопок':",
            reply_markup=markup
        )

    elif field == "id":
        await state.set_state(PostState.waiting_for_id)
        await cq.message.edit_text("Введите новый ID поста:", reply_markup=cancel_button())

    elif field == "privacy":
        data = await state.get_data()
        await state.set_state(PostState.waiting_for_privacy)
        await cq.message.edit_text(
            "Измените приватность поста:",
            reply_markup=privacy_markup(data.get('private', False))
        )

    await cq.answer()


@router.callback_query(PostState.preview, F.data == "confirm_post")
async def confirm_post_handler(cq: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    post_id = data['post_id']

    # Сохранение поста в хранилище
    storage.save_post(post_id, {
        'text': data['text'],
        'image': data.get('image', ''),
        'buttons': data.get('buttons', []),
        'private': data['private'],
        'post_id': post_id
    })

    await cq.message.edit_text(f"✅ Пост успешно создан с ID: <code>{post_id}</code>")
    await state.clear()
    await cq.answer()
