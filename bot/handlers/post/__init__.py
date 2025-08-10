from aiogram import Router
from .create_posts import router as posts_router
from .post_list import router as post_list_router

# Настройки экспорта и роутера
__all__ = ("router", )
router: Router = Router(name="post_router")

# Подключение роутеров
router.include_routers(
    post_list_router,
    posts_router,
)
