# Используем официальный облегчённый образ Python 3.11
FROM python:3.11-slim

# Задаём рабочую директорию внутри контейнера
WORKDIR /app

# Обновляем pip для актуальной версии (необязательно, но рекомендуется)
RUN pip install --upgrade pip

# Копируем файл зависимостей в контейнер
COPY requirements.txt .

# Устанавливаем зависимости из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта в рабочую директорию контейнера
COPY . .

# Опционально: задаём переменную окружения для оптимизации работы Python
ENV PYTHONUNBUFFERED=1

# Указываем команду запуска бота (можно изменить под ваш файл)
CMD ["python", "main.py"]
