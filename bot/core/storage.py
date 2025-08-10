import json
from os import path, makedirs, listdir
from typing import Any, Dict, List, Optional
from configs.config import Project
from bot.loggers import logs

# Настройки экспорта
__all__ = ("storage", )

class PostStorage:
    """Класс для управления хранением постов и связанных уведомлений."""

    def __init__(self, posts_dir: str = Project.POSTS_DIR):
        self.posts_dir = posts_dir
        self.global_posts: Dict[str, Dict[str, Any]] = {}
        self.notifications: Dict[str, Dict[str, Any]] = {}
        self.alert_texts: Dict[str, Dict[str, Any]] = {}

        self._ensure_posts_dir()
        self.load_all_posts()

    def _ensure_posts_dir(self, directory: Optional[str] = None) -> None:
        """Создаёт директорию для хранения постов, если она не существует."""
        dir_path = directory or self.posts_dir
        if not path.isdir(dir_path):
            makedirs(dir_path, exist_ok=True)
            logs.info(
                f"Created posts directory: {dir_path}",
                log_type="STORAGE",
            )

    def _get_user_posts_file(self, user_id: int) -> str:
        """Возвращает путь к файлу с постами пользователя."""
        return path.join(self.posts_dir, f"posts_{user_id}.json")

    def _update_button_notifications(self, callback_data: str, notification_data: Dict[str, Any]) -> None:
        """Регистрирует данные уведомления кнопки во внутренних хранилищах."""
        if not callback_data:
            return
        self.alert_texts[callback_data] = notification_data
        self.notifications[callback_data] = notification_data

    def _process_buttons(self, post_id: str, buttons: List[Any]) -> None:
        """
        Обрабатывает кнопки поста, нормализует callback_data и регистрирует уведомления.
        Поддерживает различные типы кнопок: callback, url, copy, inline.
        """
        if not buttons:
            return

        for row_idx, row in enumerate(buttons):
            btns = row if isinstance(row, list) else [row]
            for col_idx, button in enumerate(btns):
                if not isinstance(button, dict):
                    continue

                if 'callback_data' in button:
                    cb_data = button['callback_data']
                    if not cb_data or not (cb_data.startswith('bt_') or cb_data.startswith('show_alert_')):
                        prefix = 'show_alert_' if button.get('show_alert') else 'bt_'
                        button['callback_data'] = f"{prefix}{post_id}_{row_idx}_{col_idx}"
                        cb_data = button['callback_data']

                    if 'notification' in button:
                        notification = {
                            'text': button['notification'],
                            'show_alert': button.get('show_alert', False),
                            'allowed_ids': button.get('allowed_ids'),
                            'unauthorized_message': button.get('unauthorized_message')
                        }
                        self._update_button_notifications(cb_data, notification)
                        logs.debug(
                            f"Registered notification for {cb_data}",
                            log_type="STORAGE",
                        )

    def load_user_posts(self, user_id: int) -> Dict[str, Any]:
        """Загружает посты пользователя из файла."""
        file_path = self._get_user_posts_file(user_id)
        try:
            if path.isfile(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    posts = json.load(f)
                    if isinstance(posts, dict):
                        return posts
                    logs.warning(
                        f"Invalid posts format in {file_path}",
                        log_type="STORAGE",
                    )
        except json.JSONDecodeError as e:
            logs.error(
                f"JSON decode error in {file_path}: {str(e)}",
                log_type="STORAGE",
            )
        except Exception as e:
            logs.error(
                f"Error loading posts from {file_path}: {str(e)}",
                log_type="STORAGE",
            )
        return {}

    def save_user_posts(self, user_id: int, posts: Dict[str, Any]) -> None:
        """
        Сохраняет посты пользователя в файл и обновляет внутренние хранилища.
        Обрабатывает кнопки и уведомления перед сохранением.
        """
        if not isinstance(posts, dict):
            logs.error(
                "Invalid posts format, expected dict",
                log_type="STORAGE",
            )
            return

        for post_id, post in posts.items():
            if isinstance(post, dict) and 'buttons' in post:
                self._process_buttons(post_id, post['buttons'])

        file_path = self._get_user_posts_file(user_id)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(posts, f, ensure_ascii=False, indent=4)
            logs.info(
                f"Saved posts for user {user_id}",
                log_type="STORAGE",
            )
        except Exception as e:
            logs.error(
                f"Error saving posts to {file_path}: {str(e)}",
                log_type="STORAGE",
            )
            return

        # Обновление кэша: перезагружаем записи этого пользователя
        # Удаляем старые записи
        for pid in list(self.global_posts):
            if pid in posts:
                self.global_posts.pop(pid, None)
        # Загружаем свежие
        fresh = self.load_user_posts(user_id)
        for pid, post in fresh.items():
            if isinstance(post, dict) and 'buttons' in post:
                self._process_buttons(pid, post['buttons'])
            self.global_posts[pid] = post

    def delete_user_post(self, user_id: int, post_id: str) -> bool:
        """Удаляет пост пользователя и связанные уведомления. Возвращает статус операции."""
        user_posts = self.load_user_posts(user_id)
        if post_id not in user_posts:
            logs.warning(
                f"Post {post_id} not found for user {user_id}",
                log_type="STORAGE",
            )
            return False

        post = user_posts.pop(post_id)
        notification_count = 0
        if isinstance(post.get('buttons'), list):
            for row in post['buttons']:
                btns = row if isinstance(row, list) else [row]
                for button in btns:
                    if isinstance(button, dict):
                        cb = button.get('callback_data')
                        if cb and cb in self.alert_texts:
                            self.alert_texts.pop(cb)
                            self.notifications.pop(cb, None)
                            notification_count += 1
        logs.debug(
            f"Removed {notification_count} notifications for post {post_id}",
            log_type="STORAGE",
        )

        # Сохраняем и обновляем кэш
        self.save_user_posts(user_id, user_posts)
        self.global_posts.pop(post_id, None)
        logs.info(
            f"Deleted post {post_id} for user {user_id}",
            log_type="STORAGE",
        )
        return True

    def is_post_available(self, post_id: str) -> bool:
        """Проверяет доступность идентификатора поста."""
        return post_id not in self.global_posts

    def load_all_posts(self) -> None:
        """Загружает все посты из файлов в рабочей директории."""
        self.global_posts.clear()
        self.alert_texts.clear()
        self.notifications.clear()

        self._ensure_posts_dir()
        loaded_files = 0
        loaded_posts = 0

        try:
            for filename in listdir(self.posts_dir):
                if filename.endswith('.json'):
                    user_id_str = filename[len('posts_'):-len('.json')]
                    try:
                        user_id = int(user_id_str)
                    except ValueError:
                        logs.warning(
                            f"Invalid filename format: {filename}",
                            log_type="STORAGE",
                        )
                        continue

                    posts = self.load_user_posts(user_id)
                    for pid, post in posts.items():
                        if isinstance(post, dict) and 'buttons' in post:
                            self._process_buttons(pid, post['buttons'])
                        self.global_posts[pid] = post
                        loaded_posts += 1
                    loaded_files += 1
        except Exception as e:
            logs.error(
                f"Error loading all posts: {str(e)}",
                log_type="STORAGE",
            )

        logs.info(
            f"Loaded {loaded_posts} posts from {loaded_files} files",
            log_type="STORAGE",
        )

    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Возвращает пост по идентификатору или None если не найден."""
        return self.global_posts.get(post_id)

    def get_notification(self, callback_data: str) -> Optional[Dict[str, Any]]:
        """Возвращает данные уведомления для указанного callback."""
        return self.notifications.get(callback_data)


# Инициализация хранилища при импорте модуля
storage: PostStorage = PostStorage()
