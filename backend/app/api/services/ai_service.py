"""Maison AI assistant: a tiny RAG (keyword-retrieved docs + live tenant data) in front of OpenAI or Gemini.

Read-only by design: the model only sees a tenant-scoped, PII-free snapshot and cannot take actions.
"""
import asyncio
import re
from functools import lru_cache
from pathlib import Path

import httpx
from fastapi import Depends, HTTPException
from sqlalchemy import func

from app.api.core import deps
from app.config import Settings
from app.db.database import get_db
from app.models.booking import Bookings
from app.models.driver import Drivers
from app.models.vehicle import Vehicles
from app.utils.logging import logger
from .service_context import ServiceContext

settings = Settings()
KB_DIR = Path(__file__).resolve().parents[2] / "data" / "ai_kb"
MAX_HISTORY = 10
STOP = frozenset("the a an is are to of and or in on for my how do i can what where with it me this that".split())

SYSTEM_PROMPT = """You are Maison Assistant, the built-in helper for operators of Maison, a white-label platform for luxury ground transportation.
You are talking to the operator (tenant) of "{company}". They manage drivers, vehicles, riders and bookings from the Maison dashboard.

Rules:
- Answer only about Maison and this operator's business. Politely decline anything else in one sentence.
- Ground every fact in the DOCS and LIVE DATA sections below. If the answer is not there, say you do not know and point to Settings > Help (/tenant/settings/help) or support. Never invent numbers, prices, policies or features.
- You are read-only. You cannot change data or take actions; tell the operator which page to use instead.
- When pointing to a page, use a markdown link with the in-app path, for example [Bookings](/tenant/bookings).
- Never reveal or ask for passwords, API keys, card numbers or rider contact details.
- Be concise: short paragraphs or a short bullet list. Use plain "-" not em dashes.

DOCS:
{docs}

LIVE DATA (today is {today}, this operator only):
{data}"""


def _tokens(text: str) -> set[str]:
    # crude plural stripping so "drivers" matches "driver"
    return {w.rstrip("s") for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP and len(w) > 1}


@lru_cache(maxsize=1)
def _chunks() -> list[tuple[str, set[str]]]:
    out = []
    for f in sorted(KB_DIR.glob("*.md")):
        for part in re.split(r"(?m)^(?=## )", f.read_text()):
            if part.strip():
                out.append((part.strip(), _tokens(part)))
    return out


def retrieve_docs(question: str, k: int = 3) -> str:
    q = _tokens(question)
    scored = sorted(((len(q & t), c) for c, t in _chunks()), key=lambda x: -x[0])
    # always return something: navigation basics beat an empty context
    return "\n\n".join(c for s, c in scored[:k] if s > 0) or _chunks()[0][0]


class AIService(ServiceContext):
    def live_data(self, question: str) -> str:
        db, tid = self.db, self.tenant_id
        q = _tokens(question)
        b = db.query(Bookings).filter(Bookings.tenant_id == tid)
        by_status = dict(
            db.query(Bookings.booking_status, func.count()).filter(Bookings.tenant_id == tid).group_by(Bookings.booking_status).all()
        )
        # same "billable" rule as the Overview page: everything but cancelled
        revenue = (
            db.query(func.coalesce(func.sum(Bookings.estimated_price), 0))
            .filter(Bookings.tenant_id == tid, Bookings.booking_status != "cancelled")
            .scalar()
        )
        drivers = db.query(Drivers).filter(Drivers.tenant_id == tid)
        vehicles = db.query(Vehicles).filter(Vehicles.tenant_id == tid)
        lines = [
            f"Plan: {self.sub_plan} (subscription {self.sub_status})",
            f"Bookings by status: {by_status or 'none'}; billable revenue to date: ${float(revenue):,.2f}",
            f"Drivers: {drivers.count()} total, {drivers.filter(Drivers.is_active.is_(True)).count()} active",
            f"Vehicles: {vehicles.count()}",
        ]
        # detail sections only when the question touches them, to keep the prompt small
        if q & {"driver", "chauffeur", "assign", "available"}:
            rows = drivers.order_by(Drivers.id).limit(25).all()
            lines.append("Drivers: " + "; ".join(
                f"{d.first_name} {d.last_name} ({d.driver_type}, {'active' if d.is_active else 'inactive'}, {d.status}, rides {d.completed_rides})" for d in rows) or "none")
        if q & {"vehicle", "car", "fleet", "suv", "sedan"}:
            rows = vehicles.order_by(Vehicles.id).limit(25).all()
            lines.append("Vehicles: " + "; ".join(f"{v.year or ''} {v.make} {v.model} ({v.status})" for v in rows) or "none")
        if q & {"booking", "ride", "trip", "pickup", "upcoming", "today", "pending", "revenue", "cancel", "complete"}:
            rows = b.order_by(Bookings.pickup_time.desc()).limit(12).all()
            lines.append("Latest bookings (newest pickup first): " + "; ".join(
                f"#{r.id} {r.booking_status} {r.service_type} {r.pickup_time:%Y-%m-%d %H:%M} {r.pickup_location} -> {r.dropoff_location or 'n/a'} ${r.estimated_price or 0:.0f}" for r in rows) or "none")
        return "\n".join(lines)

    def system_prompt(self, question: str) -> str:
        company = getattr(self.current_user.profile, "company_name", None) or "your company"
        return SYSTEM_PROMPT.format(
            company=company, docs=retrieve_docs(question), data=self.live_data(question), today=self.time_now.date()
        )

    async def chat(self, messages: list[dict]) -> str:
        messages = messages[-MAX_HISTORY:]
        system = self.system_prompt(next((m["content"] for m in reversed(messages) if m["role"] == "user"), ""))
        return await complete(system, messages)


async def _post(client: httpx.AsyncClient, url: str, **kw) -> httpx.Response:
    # providers shed load with 429/503 during demand spikes; a short backoff usually clears it
    for attempt in range(3):
        r = await client.post(url, **kw)
        if r.status_code not in (429, 500, 502, 503) or attempt == 2:
            return r
        await asyncio.sleep(1.5 * (attempt + 1))


async def complete(system: str, messages: list[dict]) -> str:
    provider = settings.ai_provider.lower()
    async with httpx.AsyncClient(timeout=45) as client:
        try:
            if provider == "openai" and settings.openai_api_key:
                r = await _post(
                    client,
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    json={"model": settings.openai_model, "messages": [{"role": "system", "content": system}, *messages]},
                )
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"].strip()
            if provider == "gemini" and settings.gemini_api_key:
                r = await _post(
                    client,
                    f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent",
                    headers={"x-goog-api-key": settings.gemini_api_key},
                    json={
                        "systemInstruction": {"parts": [{"text": system}]},
                        # lookup Q&A over supplied context: dynamic thinking cost 15-20s/reply, minimal is ~2s (Gemini 3.x only)
                        "generationConfig": {"thinkingConfig": {"thinkingLevel": "minimal"}},
                        "contents": [
                            {"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]} for m in messages
                        ],
                    },
                )
                r.raise_for_status()
                parts = r.json()["candidates"][0]["content"]["parts"]
                return "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
        except (httpx.HTTPError, KeyError, IndexError) as e:
            logger.error(f"AI provider {provider} failed: {e!r}")
            raise HTTPException(502, "The assistant is unavailable right now. Please try again.")
    raise HTTPException(503, "The assistant is not configured.")


def get_ai_service(db=Depends(get_db), current_user=Depends(deps.get_current_user)):
    return AIService(db=db, current_user=current_user)
