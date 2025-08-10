from re import sub, escape
from configs.config import BotSettings

# Настройка экспорта в модули
__all__ = ("textmd2",)

def textmd2(msg: str,
            parse_mode: str = BotSettings.PARSE_MODE,
            special_chars: str = r"_*[]()~`>#+-=|{}.!") -> str:
    """
    Экранирует специальные символы MarkdownV2 в переданном тексте.

    :param msg: Входной текст в виде строки.
    :param parse_mode: Формат форматирования ('MarkdownV2' или 'HTML').
    :param special_chars: Символы, которые необходимо экранировать.

    :return: Экранированный текст или исходный текст, если формат HTML.
    :raises TypeError: Если передан не строковый тип данных.
    :raises ValueError: Если parse_mode задан некорректно.
    """

    if not isinstance(msg, str):
        raise TypeError(f"Ожидается строка, но получено {type(msg).__name__}")

    if not isinstance(parse_mode, str):
        raise TypeError(f"parse_mode должен быть строкой, но получено {type(parse_mode).__name__}")

    if parse_mode.strip().lower() == "html":
        return msg

    elif parse_mode in {"markdownv2", "markdown"}:
        return sub(rf"([{escape(special_chars)}])", r"\\\1", msg)

    else:
        raise ValueError(f"Недопустимое значение parse_mode: '{parse_mode}'. Ожидалось 'HTML' или 'MarkdownV2'")
