"""Plan and subscription gating.

Rejections are HTTP 402 Payment Required with the message in `detail` -- the
frontend reads `err.response?.data?.detail`. 401 would trigger a token-refresh
loop in the client interceptor and 403 renders as a generic "access denied",
so neither is usable for a billing signal.
"""
from typing import Optional

from fastapi import HTTPException, status

from app.domain.plans import Plan, is_entitled, resolve_status


class PlanPolicyError(HTTPException):
    """Quota or subscription-state rejection."""

    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=detail)


def _exceeds(current: int, limit: Optional[int]) -> bool:
    """The only place `None means unlimited` is interpreted.

    The `>=` also gives us the downgrade policy for free: a tenant who drops
    from fleet (30 vehicles) to free (cap 1) is immediately over limit, so
    new creates are blocked while existing records are left untouched. They
    can delete down to fit -- deletes are deliberately never billing-gated.
    """
    return limit is not None and current >= limit


def _fmt(limit: Optional[int]) -> str:
    return "unlimited" if limit is None else str(limit)


class PlanPolicy:
    @staticmethod
    def assert_subscription_active(sub_status) -> None:
        if not is_entitled(sub_status):
            raise PlanPolicyError(
                f"Your subscription is {resolve_status(sub_status)}. "
                "Reactivate your plan to continue."
            )

    @staticmethod
    def can_create_vehicle(plan: Plan, current_vehicle_count: int) -> None:
        if _exceeds(current_vehicle_count, plan.max_vehicle):
            raise PlanPolicyError(
                f"Your {plan.name} plan allows {_fmt(plan.max_vehicle)} vehicle(s); "
                f"you already have {current_vehicle_count}. Upgrade to add more."
            )

    @staticmethod
    def can_add_driver(plan: Plan, current_driver_count: int) -> None:
        if _exceeds(current_driver_count, plan.max_driver_count):
            raise PlanPolicyError(
                f"Your {plan.name} plan allows {_fmt(plan.max_driver_count)} driver(s); "
                f"you already have {current_driver_count}. Upgrade to add more."
            )

    @staticmethod
    def assert_property_support(plan: Plan) -> None:
        if not plan.allow_property_support:
            raise PlanPolicyError(
                f"Property support is not included in the {plan.name} plan."
            )

    @staticmethod
    def can_view_analytics(plan: Plan, sub_status) -> bool:
        """Returns a bool rather than raising, unlike the rest of this class.

        Analytics is degraded, not rejected: the /analysis response also carries
        the KPI tiles every tenant sees, so a 402 would blank the whole Overview
        page. Callers withhold the series and set analytics_locked instead.
        """
        return plan.allow_analytics and is_entitled(sub_status)

    # --- convenience wrappers used by the service layer: status, then quota ---

    @staticmethod
    def assert_can_add_vehicle(plan: Plan, sub_status, current_count: int) -> None:
        PlanPolicy.assert_subscription_active(sub_status)
        PlanPolicy.can_create_vehicle(plan, current_count)

    @staticmethod
    def assert_can_onboard_driver(plan: Plan, sub_status, current_count: int) -> None:
        PlanPolicy.assert_subscription_active(sub_status)
        PlanPolicy.can_add_driver(plan, current_count)
