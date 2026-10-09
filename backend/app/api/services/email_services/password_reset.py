import html
import re

from .email_services import EmailServices
from . import email_layout as L

_HEX = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def _safe_hex(value):
    """Brand colors go into inline CSS, so anything that is not a plain hex is dropped."""
    return value.strip() if isinstance(value, str) and _HEX.match(value.strip()) else None


class PasswordResetEmails(EmailServices):
    """Reset-link email for any role.

    Riders and drivers get their operator's brand: company name as sender and header, logo, button
    in the brand color (when the operator has branding on), and a link on the operator's own
    subdomain. Tenants (operators) get the Maison look and the operator dashboard link.
    """

    def __init__(self, to_email: str, role: str, first_name: str, token: str, minutes: int,
                 slug: str | None = None, branding: dict | None = None):
        self.role, self.first_name, self.token, self.minutes, self.slug = role, first_name, token, minutes, slug
        self.brand = branding or {}
        self.company = self.brand.get("company_name") or "Maison"
        self.to_email = "mubskill@gmail.com" if self.ENV == "development" else to_email
        # Commas and quotes in a company name would break the From header.
        self.from_email = self._format_from("noreply", re.sub(r'[<>",;]', "", self.company) if branding else "Maison")

    def _link(self) -> str:
        if self.role == "tenant":
            return self._tenant_url("app", f"/reset-password?token={self.token}")
        area = "riders" if self.role == "rider" else "driver"
        return self._tenant_url(self.slug, f"/{area}/reset-password?token={self.token}")

    def send(self):
        branded = bool(self.brand.get("enable_branding"))
        accent = _safe_hex(self.brand.get("primary_color")) if branded else None
        on_accent = (_safe_hex(self.brand.get("button_text_color")) if branded else None) or "#ffffff"
        body = (
            L.p(f"Hi {html.escape(L.first_name(self.first_name))},")
            + L.p(f"We received a request to reset your {html.escape(self.company)} password.")
            + L.primary_cta(self._link(), "Choose a new password &rarr;", bg=accent, fg=on_accent)
            + L.muted_p(f"This link expires in {self.minutes} minutes and works once. If you did not ask for it, ignore this email and your password stays as it is.")
            + (L.signoff_maison_team() if self.role == "tenant" else "")
        )
        html_body = L.build_email(body, footer_brand=html.escape(self.company), logo_url=self.brand.get("logo_url"))
        self.send_email(from_email=self.from_email, to_email=self.to_email, subject=f"Reset your {self.company} password", html=html_body)
