from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from ..utils.helpers import get_forward_by_id, create_forward_detail_keyboard


@Client.on_callback_query(filters.regex("^view_forward_(\d+)$"))
async def view_forward(bot: Client, query: CallbackQuery):
    """Handle view single forward callback"""
    user_id = query.from_user.id

    # Extract forward ID from callback data
    forward_id = int(query.data.split("_")[-1])

    # Get the forward
    forward = await get_forward_by_id(forward_id, user_id)

    if not forward:
        # Forward not found
        text = "🔍 **Forward not found**\n\nThis forward may have been deleted or doesn't belong to you."

        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📋 My Forwards", callback_data="my_forwards")],
                [InlineKeyboardButton("⬅️ Back", callback_data="start")],
            ]
        )

        await query.edit_message_text(text, reply_markup=keyboard)
        return

    # Create detailed view text
    text = f"⚡ **Forward**\n\n"
    text += f"**{forward.source_channel_title}** → **{forward.target_group_title}**\n"

    # Create keyboard for actions
    keyboard = create_forward_detail_keyboard(forward.id)

    await query.edit_message_text(text, reply_markup=keyboard)


@Client.on_callback_query(filters.regex("^forward_details_(\d+)$"))
async def forward_details_alternative(bot: Client, query: CallbackQuery):
    """Alternative callback for viewing forward details"""
    # Extract forward ID and redirect to main view handler
    forward_id = query.data.split("_")[-1]
    query.data = f"view_forward_{forward_id}"
    await view_forward(bot, query)
