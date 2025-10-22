from contextlib import suppress
import traceback
from bot.config import Config
from database import Session
from pyrogram import Client

async def delete_and_notify_session(bot: Client, session_string: str):
    session = await Session.find_one(Session.session_string == session_string)
    if session:
        session_username = session.username
        await session.delete()
        user_id = session.user.id
        with suppress(Exception):
            await bot.send_message(
                int(user_id),
                f"Failed to start your account: @{session_username}\nPlease Re-Login",
            )
    return

async def stop_client_by_session(session: Session): 

    await session.delete()

    try:
        app: Client = Config.CLIENTS[session.id]
        await app.log_out()
    except Exception as e:
        traceback.print_exc()

    Config.CLIENTS.pop(session.id, None)
    return True

async def get_client_by_user_id(user_id: int):
    session = await Session.find_one(Session.user.id == user_id)
    if session:
        return Config.CLIENTS[session.id]
    return None

async def is_user_logged_in(user_id: int):
    session = await Session.find_one(Session.user.id == user_id)
    if session:
        return session
    return False