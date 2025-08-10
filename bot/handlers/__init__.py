from aiogram import Router
from .post import router as post_routers
from .commands import router as cmd_routers
from .callback import router as callback_router
from .inline import router as inline_router

# Настройка экспорта и роутера
__all__ = ("router",)
router: Router = Router(name="handlers_router")

# Подключение роутеров
router.include_routers(
cmd_routers,
    callback_router,
    post_routers,
    inline_router
)
