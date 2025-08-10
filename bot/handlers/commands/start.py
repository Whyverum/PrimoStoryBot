from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.i18n import gettext as _

from bot.templates import msg_photo
from bot.utils.interesting_facts import interesting_fact
from middleware.loggers import log
from bot.bots import BotInfo
from configs import COMMANDS, BotEdit

# Настройки экспорта и роутера
__all__ = ("router",)
CMD: str = "start".lower()
router: Router = Router(name=f"{CMD}_cmd_router")


@router.callback_query(F.data == CMD)
@router.message(Command(*COMMANDS[CMD], prefix=BotInfo.prefix, ignore_case=True))
@log(level='INFO', log_type=CMD.upper(), text=f"использовал команду /{CMD}")
async def start_cmd(message: Message | CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик команды /start

    Args:
        message (Message | CallbackQuery): Сообщение или callback-запрос от пользователя.
        state (FSMContext): Состояние пользователя бота.
    """
    await state.clear()

    # Создаем клавиатуру с кнопками
    rkb: ReplyKeyboardBuilder = ReplyKeyboardBuilder()
    rkb.row(KeyboardButton(text=_("Создать пост📔")))
    rkb.row(KeyboardButton(text=_("Посмотреть список📋")))

    # Формируем приветственное сообщение
    text: str = _(
        """Добро пожаловать, <a href="{url}">{name}</a>!

Мое имя - <b>{bot_name}</b>! Я искусственный интеллект и сказитель ваших историй! 
Моя цель — помочь вам сориентироваться и сделать ваши истории куда интереснее! 
Надеюсь, я смогу вам помочь! Пожалуйста, выберите нужную функцию на клавиатуре!

Интересный факт:
<blockquote>{fact}</blockquote>
"""
    ).format(
        url=message.from_user.url if message.from_user else "",
        name=message.from_user.first_name if message.from_user else "пользователь",
        bot_name=BotEdit.PROJECT_NAME,
        fact=interesting_fact(),
    )

    # Отправляем сообщение
    await msg_photo(message=message, text=text, file='assets/start.jpg', markup=rkb)
