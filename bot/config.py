import os
from dotenv import load_dotenv

if os.path.exists("config.env"):
    load_dotenv("config.env")
else:
    load_dotenv()


def is_enabled(value, default):
    if value.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif value.lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        return default


class Config(object):
    API_ID = int(os.environ.get("API_ID"))
    API_HASH = os.environ.get("API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "tg_bot")
    DATABASE_URL = os.environ.get("DATABASE_URL", None)
    OWNER_ID = int(os.environ.get("OWNER_ID"))
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", OWNER_ID))

    CLIENTS = {}

    # Update Channel
    UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL") # link

    # Button ID Constant
    BUTTON_ID_CACHE = {}
    FORWARD_CREATE_QUEUE = []

class Script(object):
    START_MESSAGE = (
        "**Batch Forward Bot**\n\n"
        ">Automate message forwarding from channels to topic.\n\n"
        "{account_info}"
    )
    HELP_MESSAGE = (
        "🤖 **Batch Forward Bot**\n\n"
        "**What you can do with this bot:**\n"
        "You can automatically organize your educational content from channels into proper study groups. When you share notes, PDFs, videos or any study material in your channel, this bot will put them in the right subject folders in your group.\n\n"
        "**How it helps you:**\n"
        "• You can share Physics notes and they go to Physics topic automatically\n"
        "• You can share Maths PDFs and they go to Maths topic automatically\n"
        "• You can organize thousands of old study materials in minutes\n"
        "• You can keep your study group clean and organized\n"
        "• You can save time - no manual forwarding needed\n\n"
        "**How to use:**\n"
        "1. Use `/login` to connect your account\n"
        "2. Use `/addforward` to connect your channel to study group\n"
        "3. When posting content, add `Topic: Physics` or `Topic: Chemistry` in your message\n"
        "4. Use `/batch` to organize all old messages at once\n\n"
        "**Example:**\n"
        "In your channel, post: `NCERT Physics Chapter 5 Notes\\nTopic: Physics`\n"
        "The bot will automatically put it in Physics topic in your study group.\n\n"
        "💡 **Tip:** You can organize years of study materials in just a few minutes using the batch feature!\n\n"
    )
