import pytest
from pydantic import ValidationError

from app.schemas.tenant_setting import TenantBrandingUpdate


def test_known_font_and_blank_reset_accepted():
    p = TenantBrandingUpdate(font_heading="Playfair Display", font_body="")
    assert p.font_heading == "Playfair Display" and p.font_body == ""


@pytest.mark.parametrize("bad", ["Comic Sans", 'x"; background:url(//evil)', "dm sans"])
def test_unknown_font_rejected(bad):
    with pytest.raises(ValidationError):
        TenantBrandingUpdate(font_accent=bad)


def test_font_scope():
    assert TenantBrandingUpdate(font_scope="all").font_scope == "all"
    with pytest.raises(ValidationError):
        TenantBrandingUpdate(font_scope="everywhere")
