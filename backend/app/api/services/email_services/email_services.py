import resend
from app.config import Settings
# from app.config import Settings
settings = Settings()
class EmailServices:
    settings = Settings()
    resend.api_key =settings.resend_key
    
    BASE_URL = settings.base_url
    DOMAIN=settings.domain
    ENV=settings.environment


    # Verified Resend sending domain. Used in every env: Resend disables the
    # onboarding@resend.dev sandbox once an account has a verified domain.
    MAIL_DOMAIN = "usemaison.io"

    def _format_from(self, local_part: str, display_name: str, service: str = "bookings") -> str:
        """Build Resend From header: display name + local@MAIL_DOMAIN."""
        if "@" in local_part:
            local_part = f"{display_name.lower()}.{service}"
        local_part = local_part.strip().replace(" ", "-")
        return f"{display_name} <{local_part}@{self.MAIL_DOMAIN}>"

    # ── Link building ──────────────────────────────────────────────────────
    # One place for this so every email service (driver/rider/tenant) links
    # to the environment it's actually running in -- DOMAIN/scheme come from
    # config, never hardcoded, so local dev emails point at localhost instead
    # of quietly falling back to https://usemaison.io.
    def _scheme(self) -> str:
        return "https" if self.ENV == "production" else "http"

    def _bare_domain(self) -> str:
        """DOMAIN with any scheme/path stripped, e.g. 'localhost:3000' or 'usemaison.io'."""
        return (self.DOMAIN or "").replace("https://", "").replace("http://", "").strip("/").split("/")[0]

    def _tenant_host(self, slug: str) -> str:
        """Tenant subdomain host, e.g. 'acme.localhost:3000'. No scheme."""
        domain = self._bare_domain()
        return f"{slug}.{domain}" if domain else slug

    def _tenant_url(self, slug: str, path: str) -> str:
        """Full tenant-subdomain URL, scheme matched to the running environment."""
        p = path if path.startswith("/") else f"/{path}"
        return f"{self._scheme()}://{self._tenant_host(slug)}{p}"

    def _public_domain(self) -> str:
        """Apex/marketing host, e.g. 'localhost:3000' or 'usemaison.io'. No scheme.
        Only falls back to the prod domain when DOMAIN is genuinely unset -- never
        because it happens to say 'localhost' (that's the environment working)."""
        return self._bare_domain() or "usemaison.io"

    def _public_url(self, path: str) -> str:
        """Full apex-domain URL (no tenant subdomain), scheme matched to environment."""
        p = path if path.startswith("/") else f"/{path}"
        return f"{self._scheme()}://{self._public_domain()}{p}"

    def send_email(self,from_email,to_email, subject, html):
        
        params:resend.Emails.SendParams = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": html
        }
        resend.Emails.send(params)
# 
# params: resend.Emails.SendParams = {
#   "from": "Acme <onboarding@resend.dev>",
#   "to": ["delivered@resend.dev"],
#   "subject": "hello world",
#   "html": "<p>it works!</p>"
# }

# email = resend.Emails.send(params)
# print(email)


# class 
# tenants, drivers, admin, riders