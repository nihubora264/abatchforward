from contextlib import suppress
from pyrogram import Client, filters, errors, types
import datetime
import time
from bot.config import Config
import asyncio
import logging
from database.user import User


@Client.on_message(
    filters.command("broadcast") & filters.user(Config.OWNER_ID) & filters.incoming
)
async def b_handler(bot, message: types.Message):

    users = await User.find_all().to_list()
    b_msg = await message.chat.ask("Send the message to broadcast:\n\n/cancel to cancel")

    if b_msg.text and b_msg.text.lower() == "/cancel":
        return await b_msg.reply_text("Broadcast Cancelled!")
    
    sts = await message.reply_text(text="Broadcasting your messages...")

    start_time = time.time()
    total_users = len(users)
    done = 0
    blocked = 0
    deleted = 0
    failed = 0

    success = 0

    sem = asyncio.Semaphore(25)  # limit the number of concurrent tasks to 100

    async def run_task(user):
        async with sem:
            res = await broadcast_func(user, b_msg)
            return res

    tasks = []

    for user in users:
        task = asyncio.ensure_future(run_task(user))
        tasks.append(task)

    for res in await asyncio.gather(*tasks):
        success1, blocked1, deleted1, failed1, done1 = res
        done += done1
        blocked += blocked1
        deleted += deleted1
        failed += failed1
        success += success1

        if not done % 50:
            with suppress(Exception):
                await sts.edit(
                    f"Broadcast in progress:\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}"
                )

    time_taken = datetime.timedelta(seconds=int(time.time() - start_time))
    with suppress(Exception):
        await sts.edit(
            f"Broadcast Completed:\nCompleted in {time_taken} seconds.\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}"
        )


async def broadcast_func(user: User, b_msg: types.Message):
    success, blocked, deleted, failed, done = 0, 0, 0, 0, 0
    pti, sh = await broadcast_messages(int(user.id), b_msg)
    if pti:
        success = 1
    elif pti == False:
        if sh == "Blocked":
            blocked = 1
        elif sh == "Deleted":
            deleted = 1
        elif sh == "Error":
            failed = 1
    done = 1
    return success, blocked, deleted, failed, done


async def broadcast_messages(user_id: int, message: types.Message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except errors.FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_messages(user_id, message)
    except errors.InputUserDeactivated:
        logging.info(f"{user_id} - Removed from Database, since deleted account.")
        return False, "Deleted"
    except errors.UserIsBlocked:
        logging.info(f"{user_id} -Blocked the bot.")
        return False, "Blocked"
    except errors.PeerIdInvalid:
        logging.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception as e:
        return False, "Error"
