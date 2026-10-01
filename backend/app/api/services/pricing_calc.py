"""Single source of truth for ride fare math. Used by real quotes (BookingService._price_quote)
and by the tenant pricing scenario calculator, so the two can never disagree."""


def quote_total(
    service_type: str,
    base_fare: float,
    vehicle_rate: float,
    *,
    per_mile_rate: float = 0.0,
    per_minute_rate: float = 0.0,
    per_hour_rate: float = 0.0,
    distance: float = 0.0,  # miles
    speed: float = 1.0,  # average mph, used to derive ride minutes
    hours: float = 0.0,
    stc_rate: float | None = 0.0,  # fractions: 0.1 == 10%
    gratuity_rate: float | None = 0.0,
    airport_gate_fee: float | None = 0.0,
    meet_and_greet_fee: float | None = 0.0,
) -> float:
    if service_type == "hourly":
        return base_fare + vehicle_rate + per_hour_rate * hours

    minutes = distance / speed * 60
    total = base_fare + per_mile_rate * distance + per_minute_rate * minutes + vehicle_rate
    if service_type == "airport":
        total = (
            total * (1 + (stc_rate or 0.0)) * (1 + (gratuity_rate or 0.0))
            + (airport_gate_fee or 0.0)
            + (meet_and_greet_fee or 0.0)
        )
    return total


def deposit_amount(total: float, deposit_type: str | None, deposit_fee: float | None) -> float:
    fee = deposit_fee or 0.0
    return total * fee if deposit_type == "percentage" else fee
