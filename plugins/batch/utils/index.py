import asyncio
import re
import time
from pyrogram import Client
from database import Batch, Forward, File, User
from plugins.account.utils import get_client_by_user_id
from typing import Dict
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import logging

logger = logging.getLogger(__name__)


async def start_batch_index(bot: Client, batch: Batch, **kwargs):
    """Start the batch indexing process"""

    if not batch.active:
        logger.info(f"Batch {batch.id} is not active, skipping")
        return

    await batch.fetch_all_links()
    user_id = batch.user.id

    forward = await Forward.find_one(Forward.id == batch.forward.id)
    user = await User.find_one(User.id == user_id)

    start_message_id = batch.start_message_id

    client: Client = await get_client_by_user_id(user_id)
    if not client:
        logger.error(f"No client found for user {user_id}")
        await edit_progress_message(
            bot, batch, "\n\n❌ No account found. Please /login again."
        )
        return

    if not await is_valid_chat(client, forward.source_channel_id):
        logger.error(
            f"Invalid source channel {forward.source_channel_id} for user {user_id}"
        )
        await edit_progress_message(
            bot,
            batch,
            "\n\n❌ Source channel has restricted access. Please check your forward settings.",
        )
        return

    if kwargs.get("resend_progress_message", False):
        progress_message = await get_progress_message(bot, batch)
        await progress_message.delete()
        progress_message = await bot.send_message(
            batch.user.id,
            "🔄 **Resuming Batch**\n\nYour batch is now active and will continue processing.",
        )
        batch.progress_message_id = progress_message.id
        await batch.save()

    topics: Dict[str, int] = await get_topics_by_forward_id(
        client, forward.target_group_id
    )

    total_messages = await get_last_message_id(client, forward.source_channel_id)
    start_time = time.time()

    limit = (
        total_messages - start_message_id
        if batch.last_message_id == 0
        else batch.last_message_id - start_message_id
    ) + 1
    count = 0
    logger.info(
        f"Batch ID: {batch.id} Last Message ID: {batch.last_message_id} Start Message ID: {start_message_id}, Total Messages: {total_messages}, Limit: {limit}"
    )

    all_messages = []

    async for message in client.search_messages(
        chat_id=forward.source_channel_id,
        query="",
        offset_id=batch.last_message_id,
        limit=limit,
    ):
        all_messages.append(message)

    all_messages.reverse()

    for message in all_messages:
        # Update progress every 50 messages for better user experience
        # check every 10 message that batch is active or not
        if count != 0 and count % 10 == 0:
            batch = await Batch.find_one(Batch.id == batch.id)

            if not batch:
                logger.info(f"Batch {batch.id} not found, stopping")
                await send_batch_delete_message(bot, batch)
                return
            await batch.fetch_all_links()
            if not batch.active:
                logger.info(f"Batch {batch.id} is not active, stopping")
                await send_batch_pause_message(bot, batch)
                return

        if count != 0 and count % 50 == 0:
            logger.info(f"Updating batch progress for message {message.id}")
            await update_batch_progress(
                bot, batch, forward, message, count, total_messages, start_time
            )

        if not valid_message_to_forward(message):
            count += 1
            continue

        if await check_if_file_copied(
            message.id, forward.source_channel_id, forward.target_group_id, user_id
        ):
            count += 1
            continue

        topic_name = extract_topic_name(message)
        if not topic_name:
            count += 1
            continue

        if topic_name not in topics:
            topic_created = await create_topic(
                client, forward.target_group_id, topic_name
            )
            logger.info(f"Created topic {topic_name} with id {topic_created.id}")
            topics[topic_name] = topic_created.id

        topic_id = topics[topic_name]

        log = await copy_message_to_topic(message, forward.target_group_id, topic_id)
        if log:
            await create_file_entry(message, log, user, forward)
        count += 1
        await asyncio.sleep(1)

    await update_batch_progress(
        bot, batch, forward, message, count, total_messages, start_time
    )

    # Send completion message
    logger.info(f"Sending batch completion message for message {message.id}")
    await send_batch_completion_message(
        bot, batch, forward, count, total_messages, start_time
    )


async def get_progress_message(bot: Client, batch: Batch):
    """Get the progress message for a batch"""
    return await bot.get_messages(batch.user.id, batch.progress_message_id)


async def edit_progress_message(bot: Client, batch: Batch, text: str, **kwargs):
    """Edit the progress message for a batch"""
    progress_message = await get_progress_message(bot, batch)
    await safe_execute(
        progress_message.edit_text, progress_message.text + text, **kwargs
    )


async def copy_message_to_topic(message: Message, target_group_id: int, topic_id: int):
    """Copy a message to a topic"""
    try:
        log = await message._client.floodwait_handler(
            message.copy, chat_id=target_group_id, message_thread_id=topic_id
        )
        return log
    except Exception as e:
        logger.error(f"Error copying message to topic: {e}")
        return None


async def create_file_entry(source_message, target_message, user, forward):
    """Create a file entry"""

    file = File(
        source_message_id=source_message.id,
        source_channel_id=source_message.chat.id,
        target_message_id=target_message.id,
        target_group_id=target_message.chat.id,
        user=user,
        forward=forward,
    )
    await file.save()


async def create_topic(client: Client, target_group_id: int, topic_name: str):
    """Create a topic"""
    return await client.floodwait_handler(
        client.create_forum_topic, chat_id=target_group_id, title=topic_name
    )


def extract_topic_name(message: Message):
    """Extract the topic name from a message"""
    text = message.caption or message.text
    topic_pattern = r"Topic:\s*(.+?)(?:\n|$)"

    topic_match = re.search(topic_pattern, text, re.IGNORECASE | re.MULTILINE)

    if not topic_match:
        return

    extracted_topic = topic_match.group(1).strip()
    # replace more than one whitespace with a single whitespace
    extracted_topic = re.sub(r"\s+", " ", extracted_topic)
    return extracted_topic


def valid_message_to_forward(message: Message):
    """Check if a message is valid to forward"""
    return bool(message.caption)


async def get_topics_by_forward_id(bot: Client, forward_id: int):
    """Get topics by forward id"""
    topics: Dict[str, int] = {}
    async for topic in bot.get_forum_topics(forward_id):
        topics[topic.title] = topic.id
    return topics


async def update_batch_progress(
    bot: Client,
    batch: Batch,
    forward: Forward,
    message: Message,
    done_till_now: int,
    total_messages: int,
    start_time: float,
):
    """Update the batch progress with a beautiful progress bar"""
    # Calculate progress metrics
    current_time = time.time()
    elapsed_time = current_time - start_time
    progress_percentage = (
        (done_till_now / total_messages) * 100 if total_messages > 0 else 0
    )

    # Calculate ETA
    if done_till_now > 0:
        avg_time_per_message = elapsed_time / done_till_now
        remaining_messages = total_messages - done_till_now
        eta_seconds = avg_time_per_message * remaining_messages

        # Format ETA
        if eta_seconds < 60:
            eta_str = f"{int(eta_seconds)}s"
        elif eta_seconds < 3600:
            eta_str = f"{int(eta_seconds / 60)}m {int(eta_seconds % 60)}s"
        else:
            hours = int(eta_seconds / 3600)
            minutes = int((eta_seconds % 3600) / 60)
            eta_str = f"{hours}h {minutes}m"
    else:
        eta_str = "Calculating..."

    # Format elapsed time
    if elapsed_time < 60:
        elapsed_str = f"{int(elapsed_time)}s"
    elif elapsed_time < 3600:
        elapsed_str = f"{int(elapsed_time / 60)}m {int(elapsed_time % 60)}s"
    else:
        hours = int(elapsed_time / 3600)
        minutes = int((elapsed_time % 3600) / 60)
        elapsed_str = f"{hours}h {minutes}m"

    # Create visual progress bar
    bar_length = 20
    filled_length = int(bar_length * progress_percentage / 100)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)

    # Calculate messages per second
    messages_per_sec = done_till_now / elapsed_time if elapsed_time > 0 else 0

    # Create compact progress message
    progress_text = (
        f"🔄 **Processing Messages for {forward.source_channel_title}**\n\n"
        f"\n{bar} {progress_percentage:.1f}%\n"
        f"📊 {done_till_now:,}/{total_messages:,} • {messages_per_sec:.1f} msg/s\n"
        f"⏱️ {elapsed_str} • ETA: {eta_str}"
    )

    # Update the progress message
    await safe_execute(
        bot.floodwait_handler,
        bot.edit_message_text,
        chat_id=batch.user.id,
        message_id=batch.progress_message_id,
        text=progress_text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⏸️ Pause Batch", callback_data=f"batch_pause_{batch.id}_noreply"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🗑️ Delete Batch", callback_data=f"batch_delete_{batch.id}"
                    )
                ],
            ]
        ),
    )

    # Update batch in database
    batch.last_message_id = message.id
    await batch.save()


async def send_batch_completion_message(
    bot: Client,
    batch: Batch,
    forward: Forward,
    total_processed: int,
    total_messages: int,
    start_time: float,
):
    """Send a completion message showing how many messages were done in a minute"""
    end_time = time.time()
    total_elapsed = end_time - start_time

    # Format total elapsed time
    if total_elapsed < 60:
        elapsed_str = f"{int(total_elapsed)}s"
    elif total_elapsed < 3600:
        elapsed_str = f"{int(total_elapsed / 60)}m {int(total_elapsed % 60)}s"
    else:
        hours = int(total_elapsed / 3600)
        minutes = int((total_elapsed % 3600) / 60)
        elapsed_str = f"{hours}h {minutes}m"

    # Calculate messages done in a minute
    if total_elapsed > 0:
        messages_per_minute = total_processed / (total_elapsed / 60)
    else:
        messages_per_minute = 0

    # Create completion message showing messages done in a minute
    completion_text = (
        f"✅ **Indexing Complete for {forward.source_channel_title} → {forward.target_group_title}**\n\n"
        f"📊 Processed **{total_processed:,}** messages in {elapsed_str}\n"
        f"⚡ **{messages_per_minute:.1f} messages/minute**\n\n"
        f"🎯 Messages organized into topics successfully!"
    )

    await safe_execute(
        bot.floodwait_handler,
        bot.edit_message_text,
        chat_id=batch.user.id,
        message_id=batch.progress_message_id,
        text=completion_text,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📋 My Forwards", callback_data="my_forwards")],
            ]
        ),
    )

    # Mark batch as inactive
    batch.active = False
    batch.completed = True
    await batch.save()


async def is_valid_chat(client: Client, chat_id: int):
    """Check if a chat is valid"""
    try:
        chat = await client.get_chat(chat_id)
        return not chat.has_protected_content
    except Exception as e:
        logger.error(f"Invalid chat {chat_id}: {e}")
        return False


async def send_batch_status_message(
    bot: Client, batch: Batch, title: str, message: str, buttons: list
):
    """Send a status message with buttons (DRY helper function)"""
    status_text = f"{title}\n\n{message}"

    reply_markup = InlineKeyboardMarkup(buttons)

    await edit_progress_message(bot, batch, status_text, reply_markup=reply_markup)


async def send_batch_pause_message(bot: Client, batch: Batch):
    """Send a message indicating the batch has been paused"""
    title = "⏸️ **Batch Paused!**"
    message = f"Your batch processing has been paused and will continue from where it left off."

    buttons = [
        [
            InlineKeyboardButton(
                "▶️ Resume Batch", callback_data=f"batch_resume_{batch.id}_noreply"
            )
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data="start")],
    ]

    await send_batch_status_message(bot, batch, title, message, buttons)


async def send_batch_resume_message(bot: Client, batch: Batch):
    """Send a message indicating the batch has been resumed"""
    title = "🔄 **Batch Resumed!**"
    message = f"Your batch processing has been resumed and will continue from where it left off."

    buttons = [
        [
            InlineKeyboardButton(
                "⏸️ Pause Batch", callback_data=f"batch_pause_{batch.id}_noreply"
            )
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data="start")],
    ]

    await send_batch_status_message(bot, batch, title, message, buttons)


async def send_batch_delete_message(bot: Client, batch: Batch):
    """Send a message indicating the batch has been deleted"""
    title = "🗑️ **Batch Deleted!**"
    message = f"Your batch processing has been deleted and stopped."

    buttons = [
        [InlineKeyboardButton("➕ Create New Batch", callback_data="create_batch")],
        [InlineKeyboardButton("⬅️ Back", callback_data="start")],
    ]

    await send_batch_status_message(bot, batch, title, message, buttons)


async def safe_execute(func, *args, **kwargs):
    """Safe execute a function"""
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error executing {func.__name__}: {e}")
        return None


async def check_if_file_copied(
    source_message_id: int, source_channel_id: int, target_group_id: int, user_id: int
):
    """Check if a file is copied"""
    file = await File.find_one(
        File.source_message_id == source_message_id,
        File.source_channel_id == source_channel_id,
        File.user.id == user_id,
        File.target_group_id == target_group_id,
    )
    return file is not None


async def get_last_message_id(client: Client, chat_id: int):
    """Get the last message id of a channel"""
    async for message in client.search_messages(chat_id, query="", limit=1):
        return message.id
    return 0
