from pyrogram import types
from database.user import User


async def set_commands(app):
    COMMANDS = [
        types.BotCommand("start", "Start the bot."),
        types.BotCommand("help", "Need help?"),
    ]
    await app.set_bot_commands(COMMANDS)


async def add_user(user_id):
    user = await User.find_one(User.id == user_id)
    if user:
        return
    user = User(id=user_id)
    await user.save()
    return True
