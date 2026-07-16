import uuid

from pydantic import BaseModel, Field


class ChatIn(BaseModel):
    conversation_id: uuid.UUID | None = None
    content: str = Field(min_length=1, max_length=2000)
