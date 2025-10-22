from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from ..utils.helpers import (
    get_forward_by_id,
    delete_forward,
    create_delete_confirmation_keyboard,
)
from ..views.list import list_forwards
# Import and call the view function
from .view import view_forward

@Client.on_callback_query(filters.regex("^delete_forward_(\d+)$"))
async def delete_forward_confirmation(bot: Client, query: CallbackQuery):
    """Handle delete forward confirmation"""
    user_id = query.from_user.id

    # Extract forward ID from callback data
    forward_id = int(query.data.split("_")[-1])

    # Get the forward to show details in confirmation
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

    # Create confirmation text
    text = f"🗑️ **Delete Forward?**\n\n"
    text += f"**{forward.source_channel_title or forward.source_channel_id}** → **{forward.target_group_title or forward.target_group_id}**\n\n"
    text += f"⚠️ This action cannot be undone."

    # Create confirmation keyboard
    keyboard = create_delete_confirmation_keyboard(forward.id)

    await query.edit_message_text(text, reply_markup=keyboard)


@Client.on_callback_query(filters.regex("^confirm_delete_(\d+)$"))
async def confirm_delete_forward(bot: Client, query: CallbackQuery):
    """Handle confirmed delete forward action"""
    user_id = query.from_user.id

    # Extract forward ID from callback data
    forward_id = int(query.data.split("_")[-1])

    # Get forward details before deletion for the success message
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

    # Attempt to delete the forward
    success = await delete_forward(forward_id, user_id)

    if success:
        # Success message
        text = f"✅ **Forward deleted**\n\n"
        text += f"**{forward.source_channel_title or forward.source_channel_id}** → **{forward.target_group_title or forward.target_group_id}**"

        # keyboard = InlineKeyboardMarkup(
        #     [
        #         # add new forward button
        #         [InlineKeyboardButton("➕ Add Forward", callback_data="create_forward")],
        #         [InlineKeyboardButton("📋 My Forwards", callback_data="my_forwards")],
        #         [InlineKeyboardButton("⬅️ Back", callback_data="start")],
        #     ]
        # )

        # await query.edit_message_text(text, reply_markup=keyboard)
        await list_forwards(bot, query)
    else:
        # Error message
        text = f"❌ **Delete failed**\n\nSomething went wrong. Please try again."

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔄 Try Again", callback_data=f"delete_forward_{forward_id}"
                    )
                ],
                [InlineKeyboardButton("📋 My Forwards", callback_data="my_forwards")],
                [InlineKeyboardButton("⬅️ Back", callback_data="start")],
            ]
        )

        await query.edit_message_text(text, reply_markup=keyboard)


@Client.on_callback_query(filters.regex("^cancel_delete_(\d+)$"))
async def cancel_delete_forward(bot: Client, query: CallbackQuery):
    """Handle cancel delete action"""
    # Extract forward ID and redirect to view forward
    forward_id = query.data.split("_")[-1]
    query.data = f"view_forward_{forward_id}"


    await view_forward(bot, query)
