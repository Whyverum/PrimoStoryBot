import uuid
from threading import Lock

from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from BotCode.core.storage import storage
from BotCode.utils import textmd2

router = Router()

class PostState(StatesGroup):
    waiting_for_text = State()
    waiting_for_privacy = State()
    waiting_for_id = State()
    waiting_for_image = State()
    waiting_for_buttons = State()

post_id_lock = Lock()

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

def parse_buttons(text: str) -> list[list[dict]]:
    rows: list[list[dict]] = []
    current: list[dict] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            if current:
                rows.append(current)
                current = []
            continue
        if '|' not in line:
            raise ValueError(f"Неверный формат кнопки: '{line}'")
        label, action = map(str.strip, line.split('|', 1))
        btn: dict = {"text": label}
        if action.startswith('notification:'):
            btn['notification'] = action.split(':', 1)[1]
            btn['show_alert'] = True
        elif action.startswith('copy:'):
            btn['callback_data'] = f"copy_{uuid.uuid4().hex}"
            btn['copy_text'] = action.split(':', 1)[1]
        elif action.startswith('switch_inline:'):
            btn['switch_inline_query'] = action.split(':', 1)[1]
        elif action.startswith('switch_inline_current:'):
            btn['switch_inline_query_current_chat'] = action.split(':', 1)[1]
        elif action.startswith('switch_inline_chosen:'):
            btn['switch_inline_query_chosen_chat'] = action.split(':', 1)[1]
        elif action.startswith(('http://', 'https://')):
            btn['url'] = action
        else:
            btn['callback_data'] = action
        current.append(btn)
    if current:
        rows.append(current)
    return rows

# --- Handlers ---
@router.message(F.text == "Создать пост📔")
async def start_creation(message: Message, state: FSMContext):
    await state.set_state(PostState.waiting_for_text)
    await state.update_data(private=False, buttons=[])
    await message.reply(
        textmd2(
            """Отправьте текст вашего поста:
Тест для проверки @userbotname
<b>Жирный</b>
<i>Курсив</i>
<u>Подчёркнутый</u>
<s>Зачёркнутый</s>
<code>Моноширинный</code>
<pre>Предварительно отформатированный</pre>
<a href=\"https://example.com\">Ссылка</a>
"""
        ),
        reply_markup=cancel_button(), parse_mode=None
    )

@router.message(PostState.waiting_for_text)
async def got_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text or message.caption or "")
    await state.set_state(PostState.waiting_for_privacy)
    data = await state.get_data()
    await message.reply(
        "Выберите приватность поста:",
        reply_markup=privacy_markup(data.get('private', False))
    )

@router.callback_query(lambda c: c.data == "toggle_privacy")
async def toggle_privacy(cq: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    is_priv = not data.get('private', False)
    await state.update_data(private=is_priv)
    await cq.message.edit_reply_markup(
        reply_markup=privacy_markup(is_priv)
    )
    await cq.answer()

@router.callback_query(lambda c: c.data == "continue_creation")
async def continue_to_id(cq: CallbackQuery, state: FSMContext):
    await state.set_state(PostState.waiting_for_id)
    await cq.message.edit_text("Введите уникальный ID поста (латиница, цифры, подчёрки):")
    await cq.answer()

@router.message(PostState.waiting_for_id)
async def got_id(message: Message, state: FSMContext):
    pid = message.text.strip()
    if not pid.replace('_', '').isalnum():
        await message.reply(
            "ID должен содержать только латиницу, цифры и подчёркивания.",
            reply_markup=cancel_button()
        )
        return

    with post_id_lock:
        if not storage.is_post_available(pid):
            await message.reply(
                text="Этот ID уже занят, введите другой:",
                reply_markup=cancel_button()
            )
            return

    await state.update_data(post_id=pid)
    await state.set_state(PostState.waiting_for_image)
    await message.reply(
        text="Отправьте ссылку на изображение или 'нет':\n"
        "Пример: https://img4.teletype.in/files/f2/47/...",
        reply_markup=cancel_button()
    )

@router.message(PostState.waiting_for_image)
async def got_image(message: Message, state: FSMContext):
    img = message.text.strip()
    if img.lower() in ('нет', 'no', 'none'):
        img = ''
    await state.update_data(image=img)
    await state.set_state(PostState.waiting_for_buttons)
    await message.reply(
        textmd2(
            """Отправьте кнопки по шаблону:
Кнопка заглушка | void
Уведомление | notification:Для вас!
Кнопка ссылка | https://google.com
Копирование | copy:Копирование текста!
Для одного | callback_data | allowed_ids=123 | unauthorized_message=Нет доступа

Пустая строка — новый ряд. /done — закончить."""
        ),
        reply_markup=cancel_button(), parse_mode=None
    )

@router.message(PostState.waiting_for_buttons)
async def got_buttons(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    uid = message.from_user.id
    pid = data['post_id']
    try:
        if text.lower() in ('/done', 'none'):
            btns = data.get('buttons', []) if text == '/done' else []
            posts = storage.load_user_posts(uid)
            posts[pid] = {
                'user_id': uid,
                'text': data['text'],
                'image': data['image'],
                'buttons': btns,
                'private': data.get('private', False)
            }
            storage.save_user_posts(uid, posts)
            await message.reply(
                f"✅ Пост создан! ID: {pid}\n"
                f"{'🔒 Приватный' if data.get('private') else '🔓 Публичный'}\n"
                f"Используйте: <code>@{(await message.bot.me()).username} {pid}</code>"
            )
            await state.clear()
            return

        rows = parse_buttons(text)
        existing = data.get('buttons', [])
        await state.update_data(buttons=existing + rows)
        await message.reply(
            text="✅ Кнопки добавлены. Добавьте ещё или /done для окончания.",
            reply_markup=cancel_button()
        )
    except ValueError as err:
        await message.reply(f"❌ {err}")

@router.callback_query(lambda c: c.data == "cancel_creation")
async def cancel(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    await cq.message.reply(textmd2("Процесс создания поста отменён."))
    await cq.answer()
