from database.batch import Batch
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bson import ObjectId

from plugins.batch.views.list import list_batch_forwards
from plugins.batch.utils.index import start_batch_index


@Client.on_callback_query(filters.regex("^batch_current$"))
@Client.on_message(filters.command("batch") & filters.private & filters.incoming)
async def batch_current_batch(bot: Client, query: CallbackQuery):
    """Handle current batch view"""
    user_id = query.from_user.id
    batch = await Batch.find_one(Batch.user.id == user_id, Batch.completed == False)

    if not batch:
        if isinstance(query, CallbackQuery):
            await query.answer("❌ No active batch found!", show_alert=True)
        else:
            await bot.reply(
                query,
                "❌ No active batch found!",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "➕ Add a Batch", callback_data="batch_list"
                            )
                        ]
                    ]
                ),
            )
        return

    # Fetch linked data
    await batch.fetch_all_links()
    forward = batch.forward

    # Create batch details message
    status_emoji = "🟢" if batch.active else "⏸️"
    status_text = "Active" if batch.active else "Paused"

    details_text = f"""🔄 **Current Batch** {status_emoji} {status_text}

📡 {forward.source_channel_title} → {forward.target_group_title}"""

    # Create action buttons
    keyboard = []

    # Resume/Pause button
    if batch.active:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "⏸️ Pause Batch", callback_data=f"batch_pause_{batch.id}"
                )
            ]
        )
    else:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "▶️ Resume Batch", callback_data=f"batch_resume_{batch.id}"
                )
            ]
        )

    # Delete batch button
    keyboard.append(
        [
            InlineKeyboardButton(
                "🗑️ Delete Batch", callback_data=f"batch_delete_{batch.id}"
            )
        ]
    )

    # Back button
    keyboard.append(
        [InlineKeyboardButton("⬅️ Back to Batch Menu", callback_data="batch_list")]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

    # await query.edit_message_text(details_text, reply_markup=reply_markup)
    await bot.reply(query, details_text, reply_markup=reply_markup)


# Resume batch handler
@Client.on_callback_query(filters.regex(r"^batch_resume_([a-f0-9]{24})(?:_noreply)?$"))
async def batch_resume_handler(bot: Client, query: CallbackQuery):
    """Resume a paused batch"""
    batch_id = query.matches[0].group(1)
    user_id = query.from_user.id

    batch = await Batch.find_one(
        Batch.id == ObjectId(batch_id), Batch.user.id == user_id
    )
    if not batch:
        await query.answer("❌ Batch not found!", show_alert=True)
        return

    # Resume batch by setting active to True
    batch.active = True
    await batch.save()
    await query.answer("✅ Batch will be resumed soon!", show_alert=True)
    # Refresh the current batch view

    # Check if _noreply is present in the callback data
    if not query.data.endswith("_noreply"):
        await batch_current_batch(bot, query)

    await start_batch_index(bot, batch, resend_progress_message=True)


# Pause batch handler
@Client.on_callback_query(filters.regex(r"^batch_pause_([a-f0-9]{24})(?:_noreply)?$"))
async def batch_pause_handler(bot: Client, query: CallbackQuery):
    """Pause an active batch"""
    batch_id = query.matches[0].group(1)
    user_id = query.from_user.id

    batch = await Batch.find_one(
        Batch.id == ObjectId(batch_id), Batch.user.id == user_id
    )
    if not batch:
        await query.answer("❌ Batch not found!", show_alert=True)
        return

    # Pause batch by setting active to False
    batch.active = False
    await batch.save()

    await query.answer("⏸️ Batch will be paused soon!", show_alert=True)
    # Refresh the current batch view
    # Check if _noreply is present in the callback data
    if query.data.endswith("_noreply"):
        # Don't send an answer or refresh the view
        return
    await batch_current_batch(bot, query)


# Delete batch confirmation handler
@Client.on_callback_query(filters.regex(r"^batch_delete_([a-f0-9]{24})$"))
async def batch_delete_confirm_handler(bot: Client, query: CallbackQuery):
    """Show delete confirmation for batch"""
    batch_id = query.matches[0].group(1)
    user_id = query.from_user.id

    batch = await Batch.find_one(
        Batch.id == ObjectId(batch_id), Batch.user.id == user_id
    )
    if not batch:
        await query.answer("❌ Batch not found!", show_alert=True)
        return

    await batch.fetch_all_links()
    forward = batch.forward

    confirm_text = f"""⚠️ **Delete Batch Confirmation**

Are you sure you want to delete this batch?

📡 {forward.source_channel_title}
🎯 {forward.target_group_title}

**This action cannot be undone!**"""

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Yes, Delete", callback_data=f"batch_delete_confirm_{batch_id}"
            ),
            InlineKeyboardButton("❌ Cancel", callback_data="batch_current"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply(confirm_text, reply_markup=reply_markup)


# Final delete batch handler
@Client.on_callback_query(filters.regex(r"^batch_delete_confirm_([a-f0-9]{24})$"))
async def batch_delete_final_handler(bot: Client, query: CallbackQuery):
    """Actually delete the batch after confirmation"""
    batch_id = query.matches[0].group(1)
    user_id = query.from_user.id

    batch = await Batch.find_one(
        Batch.id == ObjectId(batch_id), Batch.user.id == user_id
    )
    if not batch:
        await query.answer("❌ Batch not found!", show_alert=True)
        return

    # Delete the batch
    await batch.delete()

    await query.answer("🗑️ Batch deleted successfully!", show_alert=True)

    await list_batch_forwards(bot, query)
