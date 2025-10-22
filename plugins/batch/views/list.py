from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
)
from ..utils.helpers import (
    get_user_forwards_for_batch,
    create_batch_forwards_keyboard,
    create_batch_selection_keyboard,
    get_forward_by_id,
    prompt_start_message,
    prompt_end_message,
    create_confirmation_message,
    handle_batch_search,
)
from pyrogram.types import Chat
from database import Batch


@Client.on_message(filters.command("batchlist") & filters.private & filters.incoming)
@Client.on_callback_query(filters.regex("^batch_list$"))
@Client.on_callback_query(filters.regex("^batch_page_(\d+)$"))
async def list_batch_forwards(bot: Client, query: CallbackQuery):
    """Handle batch forwards list callback"""
    user_id = query.from_user.id

    # Extract page number from callback data
    page = 0

    if isinstance(query, CallbackQuery):
        if "batch_page_" in query.data:
            page = int(query.data.split("_")[-1])

    # Get user's forwards
    forwards = await get_user_forwards_for_batch(user_id)

    if not forwards:
        # No forwards found
        text = (
            "📭 **No Forwards Found**\n\n"
            "You haven't created any forwards yet.\n"
            "Create forwards first to use batch operations!"
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "➕ Create Forward", callback_data="create_forward"
                    )
                ],
                [InlineKeyboardButton("⬅️ Back", callback_data="start")],
            ]
        )

        await query.edit_message_text(text, reply_markup=keyboard)
        return

    # Create pagination info
    per_page = 10
    total_forwards = len(forwards)
    total_pages = (total_forwards + per_page - 1) // per_page
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, total_forwards)

    text = f"🔄 **Batch Operations ({total_forwards})**\n\n"
    text += f"Select a channel below to index the whole channel 👇\n\n"
    text += f"📄 **Page {page + 1} of {total_pages}**"

    # Create keyboard with pagination
    keyboard = create_batch_forwards_keyboard(forwards, page, per_page)

    # await query.edit_message_text(text, reply_markup=keyboard)
    await bot.reply(query, text, reply_markup=keyboard)


@Client.on_callback_query(filters.regex("^batch_select_(\d+)$"))
async def select_batch_forward(bot: Client, query: CallbackQuery):
    """Handle batch forward selection"""
    user_id = query.from_user.id
    forward_id = int(query.data.split("_")[-1])

    # Get the forward details
    forward = await get_forward_by_id(forward_id, user_id)

    if not forward:
        await query.answer("❌ Forward not found!", show_alert=True)
        return

    text = (
        f"📡 **Selected Channel**\n\n"
        f"**Source:** {forward.source_channel_title}\n"
        f"**Target:** {forward.target_group_title}\n\n"
        f"Choose an action below:"
    )

    keyboard = create_batch_selection_keyboard(forward_id)

    await query.edit_message_text(text, reply_markup=keyboard)


@Client.on_callback_query(filters.regex("^batch_confirm_(\d+)$"))
async def confirm_batch_index(bot: Client, query: CallbackQuery):
    """Handle batch indexing confirmation with interactive prompts"""
    user_id = query.from_user.id
    forward_id = int(query.data.split("_")[-1])

    # Get the forward details
    forward = await get_forward_by_id(forward_id, user_id)
    if not forward:
        await query.answer("❌ Forward not found!", show_alert=True)
        return

    # Check if user already has an active batch
    batch = await Batch.find_one(
        Batch.user.id == user_id, Batch.completed == False, fetch_links=True
    )
    if batch:
        # batch.forward may be a Link, so ensure we fetch the actual Forward object if needed
        forward = await batch.forward.fetch()
        name = f"{forward.source_channel_title} -> {forward.target_group_title}"
        await query.answer(
            f"❌ You can only have one batch at a time to avoid flooding the channel \n{name}",
            show_alert=True,
        )
        return

    await query.answer()


    # Get start message from user
    start_message_id = await prompt_start_message(query, forward, forward.source_channel_id)
    if start_message_id is False:  # User cancelled or error occurred
        return

    # Get end message from user
    end_message_id = await prompt_end_message(query, start_message_id, forward.source_channel_id)
    if end_message_id is False:  # User cancelled or error occurred
        return

    # Ensure start <= end if both are provided
    if start_message_id and end_message_id and start_message_id > end_message_id:
        start_message_id, end_message_id = end_message_id, start_message_id

    # Show confirmation
    confirmation_text, keyboard = create_confirmation_message(
        forward, start_message_id, end_message_id, forward_id
    )

    await query.message.reply_text(confirmation_text, reply_markup=keyboard)


@Client.on_callback_query(filters.regex("^batch_search$"))
async def on_batch_search(bot: Client, query: CallbackQuery):
    """Handle search button for batch forwards list."""
    await handle_batch_search(query)


