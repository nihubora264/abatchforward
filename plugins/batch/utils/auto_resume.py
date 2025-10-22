import asyncio
from .index import start_batch_index
from database import Batch
from pyrogram import Client
import logging

logger = logging.getLogger(__name__)

async def auto_resume_batch(bot: Client):
    batches = await Batch.find(Batch.completed == False).to_list()
    tasks = []
    for batch in batches:
        logger.info(f"Auto resuming batch {batch.id}")
        tasks.append(start_batch_index(bot, batch, resend_progress_message=True))
    await asyncio.gather(*tasks, return_exceptions=True)