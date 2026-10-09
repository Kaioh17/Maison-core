from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.core import deps
from app.api.services import legal_service
from app.db.database import get_base_db
from app.domain.legal import LEGAL_VERSION
from app.models.tenant import Tenants

router = APIRouter(prefix="/api/v1/legal", tags=["Legal"])


def _tenant(user=Depends(deps.get_current_user)) -> Tenants:
    if not isinstance(user, Tenants):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operators only")
    return user


class AcceptBody(BaseModel):
    version: str


@router.get("/status", summary="Pilot and legal acceptance status for the signed-in operator")
def legal_status(tenant: Tenants = Depends(_tenant), db: Session = Depends(get_base_db)):
    return legal_service.status_for(db, tenant)


@router.post("/accept", summary="Accept the current legal documents (in-session re-consent)")
def accept_legal(body: AcceptBody, request: Request, tenant: Tenants = Depends(_tenant), db: Session = Depends(get_base_db)):
    if body.version != LEGAL_VERSION:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Legal documents changed. Reload and try again.")
    if legal_service.pilot_expired(tenant):
        raise legal_service.pilot_ended_error(tenant)
    legal_service.accept(db, tenant, request, "gate")
    return legal_service.status_for(db, tenant)
