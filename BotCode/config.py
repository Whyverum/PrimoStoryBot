# BotCode/config.py
from os import getenv
from ast import literal_eval
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()

BOT_TOKEN: str|None = getenv('BOT_TOKEN', None)
BOT_DEBUG_TOKEN: str|None = getenv('BOT_DEBUG_TOKEN', None)

ADMIN_ID: tuple[int] = literal_eval(getenv('ADMIN_ID', '[6751720805]'))

PARSE_MODE: str = getenv('PARSE_MODE', "HTML")

LOGGING_TO_CONSOLE: bool = getenv('LOGGING_TO_CONSOLE', "False").lower() == 'true'
DEBUG_MODE: bool = getenv('DEBUG_MODE', "False").lower() == 'true'

POSTS_DIR: str = getenv('POSTS_DIR', "posts")
