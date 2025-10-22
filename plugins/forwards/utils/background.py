import asyncio
import logging
from bot.config import Config
from plugins.user.on_message import handle_single_forward

logger = logging.getLogger(__name__)


async def handle_forward_queue():
    logger.info(f"Handling forward queue: {Config.FORWARD_CREATE_QUEUE}")
    while True:
        if Config.FORWARD_CREATE_QUEUE:
            message = Config.FORWARD_CREATE_QUEUE.pop(0)
            await handle_single_forward(message)
            logger.info(f"Processed message from queue: {message.chat.id}")
        await asyncio.sleep(1)


async def suppress_exception(func, *args, **kwargs):
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error in {func.__name__}: {e}")
        return None
