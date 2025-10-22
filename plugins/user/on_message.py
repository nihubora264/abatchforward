import logging
from pyrogram import Client, filters, errors
from bot.config import Config
from database import Forward
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import RPCError
from plugins.batch.utils.index import (
    extract_topic_name,
    get_topics_by_forward_id,
    create_topic,
)
import re

logger = logging.getLogger(__name__)


@Client.on_message(filters.channel)
async def handle_on_message(bot: Client, message: Message):
    Config.FORWARD_CREATE_QUEUE.append(message)
    logger.info(f"Added message to forward queue: {message.chat.id}")
    return

async def handle_single_forward(message: Message):
    bot = message._client
    try:
        # Get any forward with source_channel_id = message.chat.id
        forwards = await Forward.find(
            Forward.source_channel_id == message.chat.id,
            Forward.active == True,
            fetch_links=True,
        ).to_list()

        if not forwards:
            logger.info(f"No forwards configured for channel {message.chat.id}")
            return  # No forwards configured for this channel

        # Extract topic name using utility function
        extracted_topic = extract_topic_name(message)
        if not extracted_topic:
            logger.warning(f"No topic found in message from {message.chat.id}")
            return
        
        # replace more than one whitespace with a single whitespace
        extracted_topic = re.sub(r"\s+", " ", extracted_topic)

        # Process each forward
        for forward in forwards:
            user_id = forward.user.id
            try:
                # Get all forum topics using utility function
                topics = await get_topics_by_forward_id(bot, forward.target_group_id)

                # Check if topic exists
                if extracted_topic in topics:
                    topic_id = topics[extracted_topic]
                    # Forward message to the existing topic
                    await message.copy(
                        chat_id=forward.target_group_id,
                        message_thread_id=topic_id,
                    )
                    logger.info(
                        f"Forwarded message to existing topic '{extracted_topic}' in group {forward.target_group_id}"
                    )
                else:
                    # Create new topic using utility function
                    topic_created = await create_topic(
                        bot, forward.target_group_id, extracted_topic
                    )
                    logger.info(
                        f"Created topic '{topic_created.title}' in group {forward.target_group_id}"
                    )
                    await message.copy(
                        chat_id=forward.target_group_id,
                        message_thread_id=topic_created.id,
                    )
                    logger.info(
                        f"Forwarded message to new topic '{topic_created.title}' in group {forward.target_group_id}"
                    )
            except errors.ChannelForumMissing:
                # Send a message to the user that the forum is missing, including group id, forward id, and topic name
                await suppress_exception(
                    bot.send_message,
                    chat_id=user_id,
                    text=f"The forum is missing for this channel.\n"
                    f"Group ID: {forward.target_group_id}\n"
                    f"Topic name: {extracted_topic}\n"
                    "Please enable/create a forum and try again.",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "View Forward Details",
                                    callback_data=f"view_forward_{forward.id}",
                                )
                            ]
                        ]
                    ),
                )
                logger.error(
                    f"Error forwarding message to {forward.target_group_id}: {e}"
                )
                continue
            except RPCError as e:
                logger.error(
                    f"Error forwarding message to {forward.target_group_id}: {e}"
                )
                continue
            except Exception as e:
                logger.error(f"Unexpected error processing forward {forward.id}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error in handle_on_message: {e}")
        return


async def suppress_exception(func, *args, **kwargs):
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error in {func.__name__}: {e}")
        return None
