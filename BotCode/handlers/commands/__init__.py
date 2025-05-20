from aiogram import Router
from .start_cmd import router as start_cmd_router

__all__ = ('router',)
router = Router(name="post_router")

router.include_routers(start_cmd_router,)
