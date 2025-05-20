# Создание поста
new_post = {
    "id": "cat_post",
    "author_id": 123,
    "mod": "HTML",
    "type": "photo",
    "text": "Мой котик!",
    "media": "cat.jpg",
    "private": True,
    "allowed_users": [456, 789],
    "buttons": [[{
        "type": "share",
        "name": "Поделиться",
        "params": {"message": "Посмотрите этого котика!"}
    }]]
}

post_id = storage.create_post(new_post)

# Получение поста
post = storage.get_post(post_id, user_id=456)  # Доступ разрешен
post = storage.get_post(post_id, user_id=000)  # Доступ запрещен

# Поиск постов
results = storage.search_posts("котик", user_id=456)

# Обновление поста
storage.update_post(post_id, updater_id=123, updates={"text": "Новый текст"})

# Удаление поста
storage.delete_post(post_id, deleter_id=123)