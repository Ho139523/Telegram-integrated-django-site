from .start import router as user_router

def register_all_handlers(dp):
    dp.include_router(user_router)
