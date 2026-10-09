import re

_KEEP_UPPER = {"LLC", "INC", "LTD", "LLP", "USA"}


def normalize_slug(value: str) -> str:
    return re.sub(r"[\s_]+", "-", value.strip().lower())


def normalize_company_name(value: str) -> str:
    """'ACME LIMO SERVICE' -> 'Acme Limo Service'. Names that already have lowercase letters are left alone,
    so 'BLS Transportation' keeps its acronym."""
    name = " ".join(value.split())
    if not any(c.isalpha() for c in name) or name != name.upper():
        return name
    return " ".join(w if w in _KEEP_UPPER else w[:1] + w[1:].lower() for w in name.split(" "))
