import uuid

from pydantic import BaseModel, Field


class ChatIn(BaseModel):
    conversation_id: uuid.UUID | None = None
    content: str = Field(min_length=1, max_length=2000)
    # True = l'utilisateur veut une réponse rédigée par le LLM même si une fiche
    # de la base correspond quasi exactement (bouton « développer » du widget).
    force_llm: bool = False
