from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query, status
from fastapi.params import Depends

from app.schemas import general, payout as schemas
from ..services.payout_service import PayoutService, get_payout_service
from ..core import deps
from .dependencies import is_tenants

# Ledger access is deliberately not billing-gated: a lapsed plan must not lock operator and driver
# out of the record of what is owed.


def driver_only(user=Depends(deps.get_current_user)):
    # dependencies.is_driver also admits tenants, which would hand them the driver endpoints.
    if user.role != "driver":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Drivers only")
    return user

router = APIRouter(prefix="/api/v1", tags=["Payouts"])


@router.get(
    "/tenant/payouts",
    response_model=general.StandardResponse[schemas.PayoutsResponse],
    summary="Driver pay ledger",
    description="One row per completed ride with its frozen driver earning, net money movement and payout status. Requires **tenant** JWT.",
)
def tenant_payouts(
    driver_id: Optional[int] = Query(None),
    _=Depends(is_tenants),
    service: PayoutService = Depends(get_payout_service),
):
    return service.list(driver_id=driver_id)


@router.post(
    "/tenant/payouts/bulk",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=general.StandardResponse[dict],
    summary="Set the status of several payouts",
    description="Used for 'mark settled' on a driver's balance. Requires **tenant** JWT.",
)
def tenant_payouts_bulk(
    payload: schemas.PayoutBulkUpdate,
    _=Depends(is_tenants),
    service: PayoutService = Depends(get_payout_service),
):
    return service.bulk_update(payload)


@router.patch(
    "/tenant/payouts/{payout_id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=general.StandardResponse[dict],
    summary="Update one payout (status, adjustment, note)",
    description="Records who changed it and when. Adjustments are only allowed while pending or disputed. Requires **tenant** JWT.",
)
def tenant_payout_update(
    payload: schemas.PayoutUpdate,
    payout_id: int = Path(...),
    _=Depends(is_tenants),
    service: PayoutService = Depends(get_payout_service),
):
    return service.update(payout_id, payload)


@router.get(
    "/driver/payouts",
    response_model=general.StandardResponse[schemas.PayoutsResponse],
    summary="My earnings ledger",
    description="The authenticated driver's own completed rides and payout statuses. Requires **driver** JWT.",
)
def driver_payouts(
    _=Depends(driver_only),
    service: PayoutService = Depends(get_payout_service),
):
    return service.list()


@router.patch(
    "/driver/payouts/{payout_id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=general.StandardResponse[dict],
    summary="Verify or dispute my payout",
    description="A driver may mark a paid payout verified, or dispute any payout with a note. Requires **driver** JWT.",
)
def driver_payout_update(
    payload: schemas.PayoutUpdate,
    payout_id: int = Path(...),
    _=Depends(driver_only),
    service: PayoutService = Depends(get_payout_service),
):
    return service.update(payout_id, payload)
