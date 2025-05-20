from aiogram import Router
from .create_posts import router as posts_router
from .post_list import router as post_list_router

router = Router(name="post_router")

router.include_routers(
posts_router,
        post_list_router,
)
