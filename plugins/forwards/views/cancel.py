from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardRemove

from plugins.start.views.start import start


@Client.on_message(filters.regex("^Cancel$"))
async def cancel(bot: Client, message: Message):
    """Cancel the current operation"""
    await message.reply_text("Operation cancelled.", reply_markup=ReplyKeyboardRemove())
    await start(bot, message)