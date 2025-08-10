PROJECT/
├── config/
│   ├── __init__.py
│   ├── settings.py       # Основные настройки
│   └── roles_config.py   # Конфиг ролей и прав
├── data/
│   ├── database.db       # SQLite база (или папка для миграций если PostgreSQL)
│   ├── lists/            # JSON/CSV файлы списков (игроков, персонажей и т.д.)
│   └── templates/        # Шаблоны сообщений
├── handlers/
│   ├── __init__.py
│   ├── private/          # Обработчики ЛС
│   │   ├── commands.py
│   │   ├── faq.py
│   │   ├── reports.py
│   │   └── notifications.py
│   ├── groups/           # Обработчики групповых чатов
│   │   ├── flood.py
│   │   ├── roleplay.py
│   │   └── moderation.py
│   └── channels/         # Обработчики каналов
│       ├── info_updater.py
│       └── life_news.py
├── middlewares/
│   ├── __init__.py
│   ├── throttling.py     # Анти-спам
│   ├── database.py       # Интеграция БД
│   └── mode_switcher.py  # Переключение режимов
├── services/
│   ├── __init__.py
│   ├── database.py       # CRUD операции
│   ├── stats.py          # Статистика сообщений
│   ├── list_manager.py   # Управление списками
│   ├── notifier.py       # Уведомления
│   └── antispam.py       # Система спам-фильтрации
├── utils/
│   ├── __init__.py
│   ├── parsers.py        # Парсинг сообщений
│   ├── keyboards.py      # Генерация клавиатур
│   └── helpers.py        # Вспомогательные функции
├── states/               # FSM состояния
│   ├── __init__.py
│   ├── user_registration.py
│   └── report_states.py
├── .env                  # Переменные окружения
├── requirements.txt      # Зависимости
└── main.py               # Точка входа