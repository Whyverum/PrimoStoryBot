from aiogram import Router
from .post import router as post_routers
from .commands import router as cmd_routers

from .callback import router as callback_router
from .inline import router as inline_router

router = Router(name=__name__)

# Include routers with different priorities
router.include_routers(
cmd_routers,
    callback_router,
    post_routers,
    inline_router
)
