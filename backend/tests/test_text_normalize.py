import pytest

from app.schemas.tenant import TenantUpdate
from app.utils.text_normalize import normalize_company_name, normalize_slug


@pytest.mark.parametrize("raw,want", [
    ("ACME LIMO SERVICE", "Acme Limo Service"),
    ("  ACME   LLC ", "Acme LLC"),
    ("BLS Transportation", "BLS Transportation"),
    ("o'brien cars", "o'brien cars"),
    ("O'BRIEN CARS", "O'brien Cars"),
    ("123", "123"),
])
def test_company_name(raw, want):
    assert normalize_company_name(raw) == want


def test_slug():
    assert normalize_slug(" My_Company Name ") == "my-company-name"


def test_update_schema_normalizes():
    p = TenantUpdate(company_name="ACME LIMO", slug="ACME-Limo")
    assert (p.company_name, p.slug) == ("Acme Limo", "acme-limo")
