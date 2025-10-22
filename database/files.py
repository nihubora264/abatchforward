from beanie import Document, Link
from database.user import User
from database.forwards import Forward


class File(Document):
    source_channel_id: int
    target_group_id: int
    source_message_id: int
    target_message_id: int
    forward: Link[Forward]
    user: Link[User]

    class Settings:
        name = "files"