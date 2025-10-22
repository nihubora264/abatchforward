from beanie import Document, Link
from pydantic import Field
from datetime import datetime
from database.user import User
from database.forwards import Forward


class Batch(Document):
    user: Link[User]  # Link to the user who created this batch
    forward: Link[Forward]  # Link to the forward
    active: bool = Field(default=True)
    completed: bool = Field(default=False)
    progress_message_id: int = Field(default=0)  # progress message id in user chat
    last_message_id: int = Field(default=0)  # last message id of the source channel
    start_message_id: int = Field(default=0)  # start message id of the source channel
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "batch"
