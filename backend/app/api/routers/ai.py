from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.core.rate_limit import limiter
from app.api.services.ai_service import AIService, get_ai_service
from app.schemas.general import StandardResponse as resp
from .dependencies import is_tenants, require_active_subscription

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=40)


class ChatReply(BaseModel):
    reply: str


@router.post(
    "/chat",
    response_model=resp[ChatReply],
    summary="Ask the Maison assistant (tenant)",
    description="Stateless chat: send the conversation so far (last message must be from the user). Answers from Maison docs plus this tenant's live data.",
    dependencies=[Depends(is_tenants), Depends(require_active_subscription)],
)
@limiter.limit("20/minute")
async def chat(request: Request, body: ChatRequest, svc: AIService = Depends(get_ai_service)):
    if body.messages[-1].role != "user":
        raise HTTPException(422, "Last message must be from the user.")
    reply = await svc.chat([m.model_dump() for m in body.messages])
    return resp(data=ChatReply(reply=reply))
