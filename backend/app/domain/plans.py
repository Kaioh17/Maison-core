from dataclasses import dataclass

@dataclass(frozen=True)
class Plan:
    name: str
    max_vehicle: int 
    max_driver_count: int
    allow_property_support: bool
    
STARTER_PLAN = Plan(
    name="starter",
    max_vehicle=1,
    max_driver_count=1,
    allow_property_support=False
)

PREMIUM_PLAN = Plan(
    name="premium",
    max_vehicle=7,
    max_driver_count=5,
    allow_property_support=False
)

DIAMOND_PLAN = Plan(
    name="diamond",
    max_vehicle= 100000000,
    max_driver_count=10000000,
    allow_property_support=False
)

PLAN_REGISTRY = {
    "starter": STARTER_PLAN,
    "premium": PREMIUM_PLAN,
    "diamond": DIAMOND_PLAN,
}
