from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import User, ChatAdministratorRights, BotDescription, BotShortDescription
from aiogram.utils.i18n import ConstI18nMiddleware, I18n

from middleware.loggers import loggers
from configs.config import BotSettings, BotEdit, Webhook
from middleware.loggers import log

# Экспортируем объекты модуля
__all__ = ("dp", "bot", "BotInfo", "i18n",)

# Инициализация i18n
i18n: I18n = I18n(path="locales", default_locale="ru", domain="bot")

# Диспетчер бота, языковых настроек и его хранилища
storage: MemoryStorage = MemoryStorage()
dp: Dispatcher = Dispatcher(storage=storage)
dp.message.outer_middleware(ConstI18nMiddleware(locale='ru', i18n=i18n))
dp["is_active"]: bool = True

# Экземпляр бота с настройками по умолчанию
bot: Bot = Bot(token=BotSettings.BOT_TOKEN,
     default=DefaultBotProperties(
        parse_mode=BotSettings.PARSE_MODE,
        disable_notification=BotSettings.DISABLE_NOTIFICATION,
        protect_content=BotSettings.PROTECT_CONTENT,
        allow_sending_without_reply=BotSettings.ALLOW_SENDING_WITHOUT_REPLY,
        link_preview_is_disabled=BotSettings.LINK_PREVIEW_IS_DISABLED,
        link_preview_prefer_small_media=BotSettings.LINK_PREVIEW_PREFER_SMALL_MEDIA,
        link_preview_prefer_large_media=BotSettings.LINK_PREVIEW_PREFER_LARGE_MEDIA,
        link_preview_show_above_text=BotSettings.LINK_PREVIEW_SHOW_ABOVE_TEXT,
        show_caption_above_media=BotSettings.SHOW_CAPTION_ABOVE_MEDIA
    )
)


class BotInfo:
    """Класс для хранения и инициализации данных бота."""
    id: int = None
    url: str = None
    first_name: str = None
    last_name: str = None
    username: str = None
    description: str = None
    short_description: str = None
    language_code: str = BotSettings.BOT_LANGUAGE
    prefix: str = BotSettings.PREFIX
    bot_owner: str = BotSettings.OWNER
    added_to_attachment_menu: bool = False
    supports_inline_queries: bool = False
    can_connect_to_business: bool = False
    has_main_web_app: bool = False
    can_join_groups: bool = False
    can_read_all_group_messages: bool = False


    @classmethod
    @log(level='INFO', log_type='BOT', text='Настройка вебхука бота')
    async def webhook(cls, bots: Bot = bot, delete_webhook: bool = Webhook.WEBHOOK) -> None:
        """
        Удаление или установка вебхука.

        :param bots: Объект бота для управления.
        :param delete_webhook: Статус удаления, поумолчанию (true).
        """
        if delete_webhook:
            await bots.delete_webhook()


    @classmethod
    @log(level='INFO', log_type='BOT', text='Получение информации о боте')
    async def info(cls, bots: Bot = bot) -> dict:
        """
        Получает и сохраняет информацию о боте.

        :param bots: Объект бота для управления.
        :return: Словарь с персональными данными о боте.
        """
        bot_info: User = await bots.get_me()

        cls.id = bot_info.id
        cls.url = f'tg://user?id={cls.id}'
        cls.first_name = bot_info.first_name
        cls.last_name = bot_info.last_name
        cls.username = bot_info.username
        cls.description = getattr(bot_info, 'description', '')
        cls.short_description = getattr(bot_info, 'short_description', '')
        cls.language_code = bot_info.language_code
        cls.is_premium = bot_info.is_premium
        cls.added_to_attachment_menu = bot_info.added_to_attachment_menu
        cls.supports_inline_queries = bot_info.supports_inline_queries
        cls.can_connect_to_business = bot_info.can_connect_to_business
        cls.has_main_web_app = bot_info.has_main_web_app
        cls.can_join_groups = getattr(bot_info, 'can_join_groups', False)
        cls.can_read_all_group_messages = getattr(bot_info, 'can_read_all_group_messages', False)

        return {
            'id': cls.id,
            'url': cls.url,
            'first_name': cls.first_name,
            'last_name': cls.last_name,
            'username': cls.username,
            'description': cls.description,
            'short_description': cls.short_description,
            'language_code': cls.language_code,
            'prefix': cls.prefix,
            'bot_owner': cls.bot_owner,
            'is_premium': cls.is_premium,
            'added_to_attachment_menu': cls.added_to_attachment_menu,
            'supports_inline_queries': cls.supports_inline_queries,
            'can_connect_to_business': cls.can_connect_to_business,
            'has_main_web_app': cls.has_main_web_app,
            'can_join_groups': cls.can_join_groups,
            'can_read_all_group_messages': cls.can_read_all_group_messages,
        }


    @staticmethod
    @log(level='INFO', log_type='BOT', text='Установка прав администратора')
    async def set_administrator_rights(bots: Bot = bot, rights: ChatAdministratorRights = BotEdit.RIGHTS) -> None:
        """
        Устанавливает права администратора по умолчанию.

        :param bots: Объект бота для управления.
        :param rights: Заданные права администратора бота, по умолчанию словарь из конфигов.
        """
        bot_rights: ChatAdministratorRights = await bots.get_my_default_administrator_rights()

        if bot_rights != rights:
            await bots.set_my_default_administrator_rights(rights)


    @staticmethod
    @log(level='INFO', log_type='BOT', text='Обновление имени бота')
    async def set_name(bots: Bot = bot, new_name: str = BotEdit.NAME) -> None:
        """
        Устанавливает имя бота из конфига.

        :param bots: Объект бота для управления.
        :param new_name: Новое имя бота, по умолчанию из конфигов.
        """
        current_name: str = (await bots.get_me()).first_name

        if not (1 <= len(new_name) <= 32):
            raise ValueError("Имя бота должно быть от 1 до 32 символов.")

        if current_name != new_name:
            await bots.set_my_name(new_name)


    @staticmethod
    @log(level='INFO', log_type='BOT', text='Обновление описания бота')
    async def set_description(bots: Bot = bot, new_description: str = BotEdit.DESCRIPTION) -> None:
        """
        Устанавливает полное описание бота.

        :param bots: Объект бота для управления.
        :param new_description: Новое описание бота, по умолчанию из конфигов.
        """
        current_description: BotDescription = await bots.get_my_description()

        if not (0 < len(new_description) <= 255):
            raise ValueError("Описание должно быть от 1 до 255 символов.")

        if current_description != new_description:
            await bots.set_my_description(description=new_description)


    @staticmethod
    @log(level='INFO', log_type='BOT', text='Обновление короткого описания бота')
    async def set_short_description(bots: Bot = bot, new_short: str = BotEdit.SHORT_DESCRIPTION) -> None:
        """
        Устанавливает короткое описание виджета.

        :param bots: Объект бота для управления.
        :param new_short: Новое короткое описание бота, по умолчанию из конфигов.
        """
        current_short: BotShortDescription = await bots.get_my_short_description()

        if not (0 < len(new_short) <= 512):
            raise ValueError("Короткое описание должно быть от 1 до 512 символов.")

        if current_short != new_short:
            await bots.set_my_short_description(short_description=new_short)


    @classmethod
    @log(level='INFO', log_type='START', text=f'Процесс запуска бота!!!!!')
    async def setup(cls, bots: Bot = bot):
        """
        Выполняет полную настройку бота.

        :param bots: Объект бота для управления.
        """
        await cls.webhook(bots=bots)
        await cls.info(bots=bots)
        await cls.set_administrator_rights(bots=bots)
        await cls.set_description(bots=bots)
        await cls.set_short_description(bots=bots)
        await cls.set_name(bots=bots)
        loggers.info(text=f"Бот @{BotInfo.username} запущен!!!")
