from database import Session
from plugins.account.utils.helpers import stop_client_by_session


from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup


@Client.on_message(filters.command("logout") & filters.private & filters.incoming)
@Client.on_callback_query(filters.regex("^disconnect_account$"))
async def disconnect_account(bot: Client, message: CallbackQuery):
    session = await Session.find_one(Session.user.id == message.from_user.id)

    if not session:
        return await bot.reply(
            message,
            "⚠️ No account connected.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🔐 Login", callback_data="connect_account")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="start")],
                ]
            ),
        )

    await stop_client_by_session(session)
    await session.delete()

    await bot.reply(
        message,
        "✅ **Account successfully logged out**.",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🔐 Login", callback_data="connect_account")],
                [InlineKeyboardButton("⬅️ Back", callback_data="start")],
            ]
        ),
        disable_web_page_preview=True,
    )
