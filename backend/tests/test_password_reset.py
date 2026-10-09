import pytest
from fastapi import HTTPException

from app.api.core.oauth2 import create_password_reset_token, verify_password_reset_token, create_access_token
from app.api.services.email_services.password_reset import PasswordResetEmails, _safe_hex
from app.utils.password_utils import hash as hash_password


def test_token_round_trip_and_single_use():
    old = hash_password("OldPassw0rd")
    token = create_password_reset_token("rider", 7, old)
    assert verify_password_reset_token(token, "rider", old)["id"] == "7"
    with pytest.raises(HTTPException):  # password changed since the link was issued
        verify_password_reset_token(token, "rider", hash_password("NewPassw0rd"))


def test_token_is_bound_to_its_role():
    token = create_password_reset_token("rider", 7, "h")
    for other in ("driver", "tenant"):
        with pytest.raises(HTTPException):
            verify_password_reset_token(token, other)


def test_other_token_types_rejected():
    with pytest.raises(HTTPException):
        verify_password_reset_token(create_access_token({"id": 7, "role": "tenant"}), "tenant")
    with pytest.raises(HTTPException):
        verify_password_reset_token("garbage", "tenant")


def test_only_plain_hex_reaches_email_css():
    assert _safe_hex("#7c3aed") == "#7c3aed"
    assert _safe_hex("red;background:url(x)") is None
    assert _safe_hex(None) is None


def test_rider_email_is_branded_and_links_to_operator(monkeypatch):
    sent = {}
    monkeypatch.setattr(PasswordResetEmails, "send_email", lambda self, **kw: sent.update(kw))
    PasswordResetEmails(
        to_email="r@x.com", role="rider", first_name="Hann Jordan", token="T", minutes=30, slug="acme",
        branding={"company_name": "Acme Limo", "enable_branding": True, "primary_color": "#7c3aed",
                  "button_text_color": "#ffffff", "logo_url": "https://cdn.x/logo.png"},
    ).send()
    assert "Acme Limo" in sent["from_email"] and sent["subject"] == "Reset your Acme Limo password"
    assert "#7c3aed" in sent["html"] and "https://cdn.x/logo.png" in sent["html"]
    assert "acme." in sent["html"] and "/riders/reset-password?token=T" in sent["html"]
    assert "Hi Hann," in sent["html"]
