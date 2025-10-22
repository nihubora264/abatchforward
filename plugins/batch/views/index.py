from plugins.batch.utils.helpers import get_forward_by_id

from database.batch import Batch
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from plugins.batch.utils.index import start_batch_index


@Client.on_callback_query(filters.regex("^batch_index_(\d+)_(\d+)_(\d+)$"))
async def batch_index_channel(bot: Client, query: CallbackQuery):
    """Handle batch indexing of a channel"""
    user_id = query.from_user.id
    forward_id = int(query.data.split("_")[2])
    start_message_id = int(query.data.split("_")[3])
    end_message_id = int(query.data.split("_")[4])

    # Get the forward details
    forward = await get_forward_by_id(forward_id, user_id)

    if not forward:
        await query.answer("❌ Forward not found!", show_alert=True)
        return

    text = (
        f"🔄 **Starting Batch Index**\n\n"
        f"**Channel:** {forward.source_channel_title}\n"
        f"**Target:** {forward.target_group_title}\n\n"
        f"⏳ Indexing all messages from this channel...\n"
        f"📊 Analyzing channel content and creating progress tracker..."
    )

    batch = Batch(
        user=user_id,
        forward=forward,
        active=True,
        progress_message_id=query.message.id,
        last_message_id=end_message_id,
        start_message_id=start_message_id,
    )

    await batch.save()
    await query.edit_message_text(text)

    batch = await Batch.find_one(Batch.id == batch.id, fetch_links=True)
    await start_batch_index(bot, batch)