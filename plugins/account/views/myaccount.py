from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    Message,
)
from database import Session


@Client.on_message(filters.command("login") & filters.private & filters.incoming)
@Client.on_callback_query(filters.regex("^my_account$"))
@Client.on_callback_query(filters.regex("^connected_account$"))
async def connected_account(bot: Client, message: CallbackQuery | Message):

    session = await Session.find_one(Session.user.id == message.from_user.id)

    if session and session.session_string:
        text = "✅ **Account Connected**\n\n"
        text += f"👤 **User:** {'@' + session.username if session.username else 'Anonymous'}\n"
        text += f"**Session:** `{session.id}`"
    else:
        text = "⚠️ **Account Not Connected**\n\nConnect your account to use the bot features."

    buttons = []

    if session and session.session_string:
        buttons.append(
            [InlineKeyboardButton("🔓 Logout", callback_data="disconnect_account")]
        )
    else:
        buttons.extend(
            [
                [InlineKeyboardButton("🔐 Login", callback_data="connect_account")],
            ]
        )

    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="start")])

    await bot.reply(message, text, reply_markup=InlineKeyboardMarkup(buttons))
