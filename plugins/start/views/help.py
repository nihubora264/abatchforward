from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from bot.config import Script, Config


@Client.on_message(filters.command("help") & filters.private & filters.incoming)
@Client.on_callback_query(filters.regex("^help$"))
async def help(bot: Client, message: Message | CallbackQuery):

    help_message = Script.HELP_MESSAGE

    buttons = []
    if Config.UPDATE_CHANNEL:
        buttons.append(
            [
                InlineKeyboardButton("Update Channel", url=Config.UPDATE_CHANNEL),
                InlineKeyboardButton("Owner", user_id=bot.owner.id),
            ]
        )
    else:
        buttons.append(
            [
                InlineKeyboardButton("Owner", user_id=bot.owner.id),
            ]
        )

    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="start")])

    await bot.reply(
        message,
        text=help_message,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(buttons),
    )
