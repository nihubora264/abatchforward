from beanie import Document, Link
from pydantic import Field
from datetime import datetime


class User(Document):
    id: int = Field(alias="_id")
    banned: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "users"


class Session(Document):
    id: int = Field(alias="_id")
    user: Link[User]
    session_string: str
    username: str
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "sessions"
