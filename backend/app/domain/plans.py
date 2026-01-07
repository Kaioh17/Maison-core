from dataclasses import dataclass

@dataclass(frozen=True)
class Plan:
    name: str
    max_vehicle: int 
    max_driver_count: int
    maison_fee: float
    allow_property_support: bool
    
STARTER_PLAN = Plan(
    name="starter",
    max_vehicle=1,
    max_driver_count=1,
    maison_fee = 0.02,
    allow_property_support=False
)

GROWTH_PLAN = Plan(
    name="growth",
    max_vehicle=7,
    max_driver_count=5,
    maison_fee = 0.02,    
    allow_property_support=False
)

FLEET_PLAN = Plan(
    name="fleet",
    max_vehicle= 50,
    max_driver_count=50,
    maison_fee = 0.02,
    allow_property_support=False
)

PLAN_REGISTRY = {
    "starter": STARTER_PLAN,
    "growth": GROWTH_PLAN,
    "fleet": FLEET_PLAN,
}
