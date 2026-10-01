"""Seed mock riders, drivers, vehicles (one per driver plus unassigned fleet cars), bookings and driver payouts into an EXISTING tenant.

It never creates a tenant: a real tenant needs real Stripe keys, so sign one up (or run ./mock-tenant)
first. It also seeds the demo driver and demo rider logins from DEMO_DRIVER_* / DEMO_RIDER_* in .env,
the same accounts the login pages prefill via /api/v1/demo/credentials. The other seeded drivers use the
demo driver password and the other seeded riders the demo rider password, so every account can log in.

    docker exec maison_backend sh -c "cd /app/backend && python -m app.seed_demo --slug <tenant-slug>"
    ... python -m app.seed_demo --slug <tenant-slug> --reset      # remove the previous seed, then seed again
    ... python -m app.seed_demo --help

Safety:
  - It prints the database and tenant it will write to and asks you to type the slug, unless --yes.
  - Everything it inserts is tagged (emails @demo-seed.example.com or the DEMO_* emails, vehicle plates
    SD<tenant id>-...), and --reset deletes only those rows, in that tenant. It never touches anything else.
  - It reads the database from the app's own settings (DB_NAME / DB_HOST ...), so point those at the
    database you mean, exactly as you would for the API.
  - Runs are deterministic for a given --seed (dates are relative to now).
"""
import argparse
import random
import secrets
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import bindparam, text
from sqlalchemy.orm.attributes import flag_modified

from app.api.services.payout_service import PayoutService
from app.config import Settings
from app.db.database import SessionLocal, engine
from app.models import Bookings, Drivers, Payout, Users, Vehicles
from app.models.tenant import TenantProfile
from app.models.vehicle_category_rate import VehicleCategoryRate
from app.models.tenant_setting import TenantSettings
from app.utils.password_utils import hash as hash_password

MARKER_DOMAIN = "demo-seed.example.com"

FIRST = ["Olivia", "Liam", "Sofia", "Noah", "Amara", "Ethan", "Priya", "Lucas", "Maya", "Daniel", "Zoe", "Omar"]
LAST = ["Hart", "Bell", "Marchetti", "Okafor", "Nguyen", "Reyes", "Patel", "Brooks", "Silva", "Kim", "Duarte", "Lewis"]
CARS = [("Mercedes-Benz", "S580", 2024, 3), ("Cadillac", "Escalade", 2023, 6), ("Lincoln", "Navigator", 2023, 6),
        ("BMW", "740i", 2022, 3), ("Chevrolet", "Suburban", 2024, 6)]
PLACES = ["Airport Terminal 2", "Airport Terminal 4", "Grand Hotel, Main St", "Convention Center", "Riverside Hotel",
          "Union Station", "Stadium Gate B", "Financial District Tower", "Harbor Marina", "Opera House"]
PAYMENT_WEIGHTS = [("card", 55), ("cash", 20), ("zelle", 15), ("card_pickup", 10)]
DISPUTE_NOTES = ["Amount looks too low for this ride", "I was not paid for this one", "Rider tipped cash, not counted"]


def seeded_email(kind: str, n: int) -> str:
    return f"{kind}{n}@{MARKER_DOMAIN}"


def plate(tenant_id: int, tag: str) -> str:
    return f"SD{tenant_id}-{tag}"


def unusable_password() -> str:
    """Only used when DEMO_*_PASSWORD is not configured: nobody could guess it, so nothing is left open."""
    return hash_password(secrets.token_urlsafe(24))


def pick_method(rng: random.Random) -> str:
    return rng.choices([m for m, _ in PAYMENT_WEIGHTS], weights=[w for _, w in PAYMENT_WEIGHTS])[0]


def fare_for(rng: random.Random, service: str, hours: float | None) -> float:
    base = hours * 95 if service == "hourly" else rng.uniform(95, 260) if service == "airport" else rng.uniform(45, 180)
    # odd cents on purpose: they exercise per-ride rounding in the pay math
    return round(base + rng.choice([0, 0, 0.25, 0.5, 0.75, 0.99]), 2)


def find_tenant(db, slug: str):
    profile = db.query(TenantProfile).filter(TenantProfile.slug == slug).first()
    if not profile:
        sys.exit(
            f"No tenant with slug {slug!r} in database {engine.url.database!r}.\n"
            "This script never creates tenants (they need real Stripe keys). Sign one up, or run ./mock-tenant, "
            "then pass its slug with --slug."
        )
    return profile.tenant_id


def seeded_accounts(db, tenant_id: int, settings: Settings):
    """Drivers and riders this script owns in the tenant: marker domain, or the demo login emails."""
    demo = [e for e in (settings.demo_driver_email, settings.demo_rider_email) if e]
    drivers = db.query(Drivers).filter(
        Drivers.tenant_id == tenant_id,
        Drivers.email.ilike(f"%@{MARKER_DOMAIN}") | Drivers.email.in_(demo),
    ).all()
    riders = db.query(Users).filter(
        Users.tenant_id == tenant_id,
        Users.email.ilike(f"%@{MARKER_DOMAIN}") | Users.email.in_(demo),
    ).all()
    return drivers, riders


def reset(db, tenant_id: int, settings: Settings) -> dict:
    """Delete only rows tied to seeded accounts. Order matters: payouts/ratings/transactions have no cascade."""
    drivers, riders = seeded_accounts(db, tenant_id, settings)
    driver_ids, rider_ids = [d.id for d in drivers], [r.id for r in riders]
    booking_ids = [
        b.id for b in db.query(Bookings.id).filter(
            Bookings.tenant_id == tenant_id,
            Bookings.driver_id.in_(driver_ids) | Bookings.rider_id.in_(rider_ids),
        )
    ] if (driver_ids or rider_ids) else []
    counts = {"bookings": len(booking_ids), "drivers": len(driver_ids), "riders": len(rider_ids)}
    if booking_ids:
        for table in ("payouts", "booking_ratings", "transactions"):
            db.execute(text(f"DELETE FROM {table} WHERE booking_id IN :ids").bindparams(
                bindparam("ids", value=booking_ids, expanding=True)))
        db.query(Bookings).filter(Bookings.id.in_(booking_ids)).delete(synchronize_session=False)
    # tagged vehicles: seeded drivers' cars and the unassigned fleet (plates SD<tenant>-...)
    vehicles = db.query(Vehicles).filter(Vehicles.tenant_id == tenant_id, Vehicles.license_plate.like(f"{plate(tenant_id, '')}%"))
    in_use = db.query(Bookings.id).filter(
        Bookings.vehicle_id.in_([v.id for v in vehicles]), ~Bookings.id.in_(booking_ids or [0])
    ).count()
    if in_use:  # a real ride was booked on a seeded vehicle: do not delete someone's booking behind their back
        sys.exit(f"{in_use} booking(s) that are not seed data use a seeded vehicle. Reassign or delete them, then retry --reset.")
    counts["vehicles"] = vehicles.count()
    vehicles.delete(synchronize_session=False)
    if driver_ids:
        db.query(Drivers).filter(Drivers.id.in_(driver_ids)).delete(synchronize_session=False)
    if rider_ids:
        db.query(Users).filter(Users.id.in_(rider_ids)).delete(synchronize_session=False)
    db.flush()
    return counts


def ensure_pay_rule(db, tenant_id: int) -> str | None:
    """Payouts only exist once a pay rule is set. Add a demo one only if the tenant has none."""
    cfg = db.query(TenantSettings).filter(TenantSettings.tenant_id == tenant_id).first()
    if cfg is None:
        sys.exit("The tenant has no settings row, so it was never fully set up. Seed a complete tenant first.")
    config = dict(cfg.config or {})
    if config.get("driver_pay"):
        return None
    config["driver_pay"] = {
        "default": {"type": "percent", "value": 70},
        "in_house": None,
        "outsourced": {"type": "percent", "value": 75},
    }
    cfg.config = config
    flag_modified(cfg, "config")
    db.flush()
    return "No driver pay rule was set, so a demo one was added: 70% default, 75% outsourced."


def make_drivers(db, tenant_id: int, count: int, rng: random.Random, settings: Settings):
    out = []
    specs = [("in_house", settings.demo_driver_email, settings.demo_driver_password)]
    # the other drivers log in with the same demo driver password, so every seeded driver is usable in the app
    specs += [(("in_house" if i == 0 else "outsourced"), seeded_email("driver", i + 1), settings.demo_driver_password or None) for i in range(count - 1)]
    for i, (dtype, email, password) in enumerate(specs[:count]):
        if not email:  # demo driver login not configured: seed a plain one instead
            email, password = seeded_email("driver", 0), None
        first, last = (("Demo", "Driver") if i == 0 and password else (FIRST[(i * 3) % len(FIRST)], LAST[(i * 5 + 1) % len(LAST)]))
        d = Drivers(
            tenant_id=tenant_id, email=email, first_name=first, last_name=last, phone_no=f"+1555010{i:04d}",
            password=hash_password(password) if password else unusable_password(), state="CA", postal_code="90001",
            role="driver", driver_type=dtype, completed_rides=0, license_number=f"SEED{tenant_id}{i:03d}",
            driver_token=f"seed-token-{tenant_id}-{i}", is_registered="registered", is_active=True, is_token=True,
            status="available", background_check_status="approved",
        )
        db.add(d)
        out.append(d)
    db.flush()
    categories = [c.id for c in db.query(VehicleCategoryRate).filter(VehicleCategoryRate.tenant_id == tenant_id).order_by(VehicleCategoryRate.id)]
    for i, d in enumerate(out):
        add_vehicle(db, tenant_id, i, f"{i:02d}", categories, driver_id=d.id)
    db.flush()
    return out


def add_vehicle(db, tenant_id: int, i: int, tag: str, categories: list[int], driver_id: int | None = None):
    make, model, year, seats = CARS[i % len(CARS)]
    color = ["Black", "Black", "White", "Silver"][i % 4]
    v = Vehicles(tenant_id=tenant_id, driver_id=driver_id, make=make, model=model, year=year, seating_capacity=seats,
                 license_plate=plate(tenant_id, tag), color=color, status="available",
                 vehicle_category_id=categories[i % len(categories)] if categories else None)
    db.add(v)
    return v


def make_fleet_vehicles(db, tenant_id: int, count: int, first_index: int):
    """Extra vehicles with no driver, ready to assign from the dashboard."""
    categories = [c.id for c in db.query(VehicleCategoryRate).filter(VehicleCategoryRate.tenant_id == tenant_id).order_by(VehicleCategoryRate.id)]
    out = [add_vehicle(db, tenant_id, first_index + j, f"X{j + 1}", categories) for j in range(count)]
    db.flush()
    return out


def make_riders(db, tenant_id: int, count: int, settings: Settings):
    out = []
    emails = [settings.demo_rider_email or seeded_email("rider", 0)] + [seeded_email("rider", i + 1) for i in range(count - 1)]
    for i, email in enumerate(emails[:count]):
        demo = i == 0 and email == settings.demo_rider_email and bool(settings.demo_rider_password)
        clash = db.query(Users).filter(Users.email == email).first()
        if clash:
            sys.exit(f"{email} already exists (tenant {clash.tenant_id}); rider emails are unique across tenants.")
        first, last = ("Demo", "Rider") if demo else (FIRST[(i * 2 + 1) % len(FIRST)], LAST[(i * 7 + 2) % len(LAST)])
        u = Users(tenant_id=tenant_id, email=email, first_name=first, last_name=last, phone_no=f"+1555020{i:04d}",
                  password=hash_password(settings.demo_rider_password) if settings.demo_rider_password else unusable_password(),
                  city="Los Angeles", state="CA", country="US", postal_code="90001", role="rider", tier="vip" if demo else "free")
        db.add(u)
        out.append(u)
    db.flush()
    return out


def make_bookings(db, tenant_id, drivers, riders, days, rng, now):
    """Non-overlapping rides per driver (uq_driver_booking / uq_vehicle_booking). Past: mostly completed; next 3 days: upcoming."""
    vehicles = {v.driver_id: v for v in db.query(Vehicles).filter(Vehicles.driver_id.in_([d.id for d in drivers]))}
    bookings = []
    for d in drivers:
        for offset in range(-days, 4):
            day = (now + timedelta(days=offset)).replace(hour=0, minute=0, second=0, microsecond=0)
            for slot in sorted(rng.sample([7, 9, 12, 15, 18, 21], rng.choice([0, 1, 1, 2]) if day.weekday() < 5 else rng.choice([0, 1]))):
                service = rng.choices(["airport", "dropoff", "hourly"], weights=[35, 45, 20])[0]
                hours = float(rng.choice([2, 3, 4, 6])) if service == "hourly" else None
                pickup = day + timedelta(hours=slot, minutes=rng.choice([0, 15, 30, 45]))
                dropoff = pickup + (timedelta(hours=hours) if hours else timedelta(minutes=rng.choice([35, 50, 70])))
                if offset < 0 or dropoff < now:
                    status = "cancelled" if rng.random() < 0.08 else "completed"
                else:
                    status = rng.choice(["confirmed", "confirmed", "pending"])
                method = pick_method(rng)
                a, b = rng.sample(PLACES, 2)
                bookings.append(Bookings(
                    tenant_id=tenant_id, driver_id=d.id, vehicle_id=vehicles[d.id].id, rider_id=rng.choice(riders).id,
                    service_type=service, airport_service=(rng.choice(["from_airport", "to_airport"]) if service == "airport" else None),
                    pickup_location=a, dropoff_location=None if service == "hourly" else b, pickup_time=pickup, dropoff_time=dropoff,
                    hours=hours, country="US", booking_status=status, estimated_price=fare_for(rng, service, hours),
                    payment_method=method, is_approved=status != "pending",
                    payment_status="full_paid" if method == "card" and status == "completed" else "pending",
                    cancellation_reason="Rider cancelled" if status == "cancelled" else None,
                    reminder_24h_sent=pickup < now, reminder_1h_sent=pickup < now, confirm_reminder_sent=status != "pending",
                ))
    db.add_all(bookings)
    db.flush()
    return bookings


def make_payouts(db, bookings, drivers, tenant_id, rng, now):
    """Reuse the real completion hook (so earnings use the tenant's rule), then age the statuses realistically."""
    by_id = {d.id: d for d in drivers}
    completed = [b for b in bookings if b.booking_status == "completed"]
    for b in completed:
        by_id[b.driver_id].completed_rides += 1
        PayoutService.record_completion(db, b, by_id[b.driver_id])
    db.flush()
    payouts = {p.booking_id: p for p in db.query(Payout).filter(Payout.booking_id.in_([b.id for b in completed]))}
    rows = [(b, payouts[b.id]) for b in completed if b.id in payouts]
    for b, p in rows:
        age = (now - b.pickup_time).days
        if age > 14:
            p.status, p.status_by_role = ("verified", "driver") if rng.random() < 0.8 else ("paid", "tenant")
        elif age > 7:
            p.status, p.status_by_role = "paid", "tenant"
        else:
            continue  # recent rides stay pending
        p.status_by_id = b.driver_id if p.status_by_role == "driver" else tenant_id
        p.status_on = min(now, b.pickup_time + timedelta(days=rng.randint(1, 4), hours=rng.randint(0, 6)))
    older = [(b, p) for b, p in rows if 7 < (now - b.pickup_time).days <= 21 and p.status == "paid"]
    for b, p in rng.sample(older, min(2, len(older))):
        p.status, p.status_by_role, p.status_by_id = "disputed", "driver", b.driver_id
        p.status_on, p.note = now - timedelta(days=rng.randint(1, 3)), rng.choice(DISPUTE_NOTES)
    pending = [p for _, p in rows if p.status == "pending"]
    if pending:  # one bonus on an open ride, so adjustments show up in Balances
        p = rng.choice(pending)
        p.adjustment, p.note = 15.0, "Waiting-time bonus"
        p.status_by_role, p.status_by_id, p.status_on = "tenant", tenant_id, now
    db.flush()
    return len(rows)


def main() -> None:
    settings = Settings()
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slug", default=settings.demo_tenant_slug, help="Existing tenant slug (default: DEMO_TENANT_SLUG).")
    ap.add_argument("--drivers", type=int, default=4, help="Drivers to create, including the demo driver.")
    ap.add_argument("--vehicles", type=int, default=2, help="Extra unassigned fleet vehicles (drivers get one each already).")
    ap.add_argument("--riders", type=int, default=8, help="Riders to create, including the demo rider.")
    ap.add_argument("--days", type=int, default=28, help="Days of ride history.")
    ap.add_argument("--seed", type=int, default=42, help="Random seed.")
    ap.add_argument("--reset", action="store_true", help="Delete this script's previous seed in the tenant first.")
    ap.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")
    args = ap.parse_args()
    if not args.slug:
        sys.exit("Pass --slug (DEMO_TENANT_SLUG is empty).")
    if args.drivers < 1 or args.riders < 1:
        sys.exit("--drivers and --riders must be at least 1.")

    db = SessionLocal()
    try:
        tenant_id = find_tenant(db, args.slug)
        print(f"Database: {engine.url.host}/{engine.url.database}   Tenant: {args.slug} (id {tenant_id})")
        if not args.yes and input(f"Type the tenant slug to seed it ({args.slug}): ").strip() != args.slug:
            sys.exit("Cancelled.")

        if args.reset:
            print("Removed previous seed:", reset(db, tenant_id, settings))
        elif any(seeded_accounts(db, tenant_id, settings)):
            sys.exit("This tenant already has seeded accounts. Run again with --reset to replace them.")

        rng, now = random.Random(args.seed), datetime.now(timezone.utc).replace(microsecond=0)
        note = ensure_pay_rule(db, tenant_id)
        drivers = make_drivers(db, tenant_id, args.drivers, rng, settings)
        fleet = make_fleet_vehicles(db, tenant_id, args.vehicles, first_index=len(drivers))
        riders = make_riders(db, tenant_id, args.riders, settings)
        bookings = make_bookings(db, tenant_id, drivers, riders, args.days, rng, now)
        n_payouts = make_payouts(db, bookings, drivers, tenant_id, rng, now)
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()

    if note:
        print(note)
    print(f"Seeded {len(drivers)} drivers, {len(drivers) + len(fleet)} vehicles ({len(fleet)} unassigned), "
          f"{len(riders)} riders, {len(bookings)} bookings, {n_payouts} payouts.")
    for label, email, pw in (("Demo driver", settings.demo_driver_email, settings.demo_driver_password),
                             ("Demo rider", settings.demo_rider_email, settings.demo_rider_password)):
        if email and pw:
            print(f"{label} login: {email} (password from .env)")
    if settings.demo_driver_password and settings.demo_rider_password:
        print(f"Other seeded drivers (driver1@{MARKER_DOMAIN} ...) and riders (rider1@{MARKER_DOMAIN} ...) use those same passwords.")


if __name__ == "__main__":
    main()
