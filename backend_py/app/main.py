import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response

# Relative imports within the backend_py package
from .api.router import api_router
from .core.logging import setup_logging
from .core.config import settings
from .db.init_db import init_db

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    import sys
    # Ensure stdout can handle UTF-8 on Windows (avoids UnicodeEncodeError with emoji)
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    # 1. Initialize Database (Create tables & seed keywords if empty)
    logger.info("Initializing Neon PostgreSQL Database...")
    try:
        init_db()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # 2. Start Telegram Bot
    bot_task = None
    bot_instance = None

    if settings.TELEGRAM_BOT_TOKEN:
        try:
            from app.bot.bot import dp, Bot
            from aiogram.client.session.aiohttp import AiohttpSession

            if settings.TELEGRAM_PROXY_URL:
                session = AiohttpSession(proxy=settings.TELEGRAM_PROXY_URL)
                bot_instance = Bot(token=settings.TELEGRAM_BOT_TOKEN, session=session)
            else:
                bot_instance = Bot(token=settings.TELEGRAM_BOT_TOKEN)

            # Store bot & dispatcher in app state so the webhook route can access them
            app.state.bot = bot_instance
            app.state.dp = dp

            if settings.WEBHOOK_URL:
                # ── WEBHOOK MODE (Render / production) ──────────────────────────────
                # Delete any existing webhook first, then register the new one.
                # FastAPI handles updates via POST /webhook/telegram
                webhook_url = f"{settings.WEBHOOK_URL.rstrip('/')}/webhook/telegram"
                logger.info(f"Setting Telegram webhook to: {webhook_url}")
                await bot_instance.delete_webhook(drop_pending_updates=True)
                await bot_instance.set_webhook(
                    url=webhook_url,
                    secret_token=settings.WEBHOOK_SECRET,
                    allowed_updates=dp.resolve_used_update_types(),
                )
                logger.info("Telegram webhook registered successfully.")
            else:
                # ── POLLING MODE (local development) ────────────────────────────────
                if settings.TELEGRAM_BOT_POLLING:
                    logger.info("WEBHOOK_URL not set — starting Long Polling (local dev mode).")

                    async def run_bot():
                        retry_delay = 5
                        while True:
                            try:
                                await bot_instance.delete_webhook(drop_pending_updates=True)
                                await dp.start_polling(
                                    bot_instance,
                                    close_bot_session=True,
                                    allowed_updates=dp.resolve_used_update_types(),
                                )
                                break
                            except asyncio.CancelledError:
                                logger.info("Bot polling task cancelled (shutdown).")
                                raise
                            except Exception as e:
                                logger.warning(f"Bot polling failed: {e}. Retrying in {retry_delay}s...")
                                await asyncio.sleep(retry_delay)
                                retry_delay = min(retry_delay * 2, 60)

                    bot_task = asyncio.create_task(run_bot())
                else:
                    logger.info("WEBHOOK_URL not set and TELEGRAM_BOT_POLLING is disabled. Bot polling will NOT start in API process.")

        except Exception as e:
            logger.error(f"Failed to start Telegram Bot: {e}")
    else:
        logger.warning("TELEGRAM_BOT_TOKEN is not set. Telegram Bot will NOT start.")

    yield

    # 3. Shutdown
    if settings.WEBHOOK_URL and bot_instance:
        logger.info("Deleting Telegram webhook on shutdown...")
        try:
            await bot_instance.delete_webhook()
        except Exception as e:
            logger.warning(f"Failed to delete webhook on shutdown: {e}")
        await bot_instance.session.close()

    if bot_task:
        logger.info("Stopping Telegram Bot polling...")
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass
        logger.info("Telegram Bot stopped.")


app = FastAPI(title="Tender Intelligence Platform", lifespan=lifespan)
app.include_router(api_router)


# ── Telegram Webhook endpoint ────────────────────────────────────────────────
@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """Receive Telegram updates via webhook (used in production on Render)."""
    # Validate the secret token Telegram sends in the header
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if secret != settings.WEBHOOK_SECRET:
        logger.warning("Webhook request with invalid secret token rejected.")
        return Response(status_code=403)

    try:
        from aiogram.types import Update
        bot = app.state.bot
        dp = app.state.dp

        data = await request.json()
        update = Update.model_validate(data)
        await dp.feed_update(bot=bot, update=update)
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}")

    return Response(status_code=200)
