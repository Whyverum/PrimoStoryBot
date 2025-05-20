# BotCode/handlers/commands/start_cmd.py
from aiogram import Router, types
from aiogram.filters import CommandStart

router = Router(name=__name__)
__all__ = ("router",)


@router.message(CommandStart())
async def start_cmd(message: types.Message) -> None:
    """
    Обработчик команды /start.

    :param message: Объект сообщения и информации о нем.
    :return: Вывод сообщения для администратора, о выборе режимов работы.
    """
    from BotCode.loggers import logs
    from BotCode.utils import textmd2
    logs.info(text="использовал(а) команду /start", log_type="Start", message=message)
    
    if message.from_user.id:
        # Создаем клавиатурный билдер
        from aiogram.utils.keyboard import ReplyKeyboardBuilder
        rkb: ReplyKeyboardBuilder = ReplyKeyboardBuilder()
        rkb.row(types.KeyboardButton(text="Создать пост📔"))
        rkb.row(types.KeyboardButton(text="Посмотреть список📋"))
            
        # Отправка фотографии с текстом и клавиатурой
        from aiogram.types.input_file import FSInputFile
        await message.reply_photo(
            photo=FSInputFile('assets/start.jpg'),
            caption=textmd2("Добро пожаловать в систему, Босс!"),
            reply_markup=rkb.as_markup(resize_keyboard=True)
        )
    else:
        await message.reply(text=textmd2("Простите, вы не мой Босс!❌\nОбратитесь к @verdise!"))
