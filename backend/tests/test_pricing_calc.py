from app.api.services.pricing_calc import quote_total, deposit_amount


def test_dropoff_uses_real_minutes():
    # 30 mi at 30 mph = 60 min: 5 + 2*30 + 0.5*60 + 10 flat
    assert quote_total("dropoff", 5, 10, per_mile_rate=2, per_minute_rate=0.5, distance=30, speed=30) == 105


def test_airport_adds_percentages_then_fees():
    # (100) * 1.1 * 1.1 + 4 + 6
    assert round(quote_total("airport", 100, 0, stc_rate=0.1, gratuity_rate=0.1, airport_gate_fee=4, meet_and_greet_fee=6), 2) == 131.0


def test_airport_without_config_is_plain_fare():
    assert quote_total("airport", 100, 0, stc_rate=None, gratuity_rate=None) == 100


def test_hourly():
    assert quote_total("hourly", 10, 20, per_hour_rate=50, hours=4) == 230


def test_deposit():
    assert deposit_amount(200, "percentage", 0.25) == 50
    assert deposit_amount(200, "flat", 75) == 75
