from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import Script
from ..utils.helpers import add_user
from plugins.account.utils.helpers import is_user_logged_in


@Client.on_message(filters.command("start") & filters.private & filters.incoming)
@Client.on_callback_query(filters.regex("^start$"))
async def start(bot: Client, message: Message):
    # get or create user
    await add_user(message.from_user.id)
    # iuf not logged in then show logged in button and help button
    buttons = []
    session = await is_user_logged_in(message.from_user.id)
    if not session:
        buttons.append(
            [InlineKeyboardButton("🔐 Login", callback_data="connect_account")]
        )
    else:
        buttons.append(
            [InlineKeyboardButton("👤 My Account", callback_data="my_account")]
        )
        buttons.append(
            [InlineKeyboardButton("📤 My Forwards", callback_data="my_forwards")]
        )
        buttons.append(
            [InlineKeyboardButton("🔄 Batch Save", callback_data="batch_list")]
        )
    buttons.append([InlineKeyboardButton("❓ Information", callback_data="help")])

    account_status = "__Login to your account to get started__"
    if session:
        account_status = f"✅ Connected as @{session.username}"

    text = Script.START_MESSAGE.format(account_info=account_status)
    keyboard = InlineKeyboardMarkup(buttons)
    await bot.reply(message, text, reply_markup=keyboard)
