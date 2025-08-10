from aiogram import Router
from .start import router as start_cmd_router
from .help import router as help_cmd_router

# Настройка экспорта и роутера
__all__ = ('router',)
router: Router = Router(name="cmd_router")

# Подготовка роутера команд
router.include_routers(start_cmd_router,
                       help_cmd_router,
)
