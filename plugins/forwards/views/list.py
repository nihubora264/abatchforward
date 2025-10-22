from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from ..utils.helpers import get_user_forwards, create_forwards_keyboard, handle_forwards_search


@Client.on_message(filters.command("forwards") & filters.private & filters.incoming)
@Client.on_callback_query(filters.regex("^my_forwards$"))
@Client.on_callback_query(filters.regex("^forwards_page_(\d+)$"))
async def list_forwards(bot: Client, query: CallbackQuery):
    """Handle forwards list callback"""
    user_id = query.from_user.id

    # Extract page number from callback data
    page = 0

    if isinstance(query, CallbackQuery):
        if "forwards_page_" in query.data:
            page = int(query.data.split("_")[-1])

    # Get user's forwards
    forwards = await get_user_forwards(user_id)

    if not forwards:
        # No forwards found
        text = (
            "📭 **No Forwards Found**\n\n"
            "You haven't created any forwards yet.\n"
            "Click the button below to create your first forward!"
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
    per_page = 5
    total_forwards = len(forwards)
    total_pages = (total_forwards + per_page - 1) // per_page
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, total_forwards)

    text = f"📋 **My Forwards ({total_forwards})**\n\n"
    text += f"Select option below to manage your forwards 👇"


    # Create keyboard with pagination
    keyboard = create_forwards_keyboard(forwards, page, per_page)

    await bot.reply(query, text, reply_markup=keyboard)


@Client.on_callback_query(filters.regex("^list_forwards$"))
async def list_forwards_command(bot: Client, query: CallbackQuery):
    """Alternative callback for listing forwards"""
    # Redirect to main forwards handler
    query.data = "my_forwards"
    await list_forwards(bot, query)


@Client.on_callback_query(filters.regex("^forwards_search$"))
async def on_forwards_search(bot: Client, query: CallbackQuery):
    """Handle search button for forwards list."""
    await handle_forwards_search(query)
