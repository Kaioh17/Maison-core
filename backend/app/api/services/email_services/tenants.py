import resend
from .email_services import EmailServices
from app.models.tenant import Tenants
from . import email_layout as L

class TenantEmailServices(EmailServices):
    """
        Inherits the parentclass EmailServices with the set
        purpose: As the name implies, it will be used to send tenant related emails for all tenants on our service.
        The from email used here should be tailored by the tenants,
        the content of the email can be tailored too if not there will be a default service that handles this.
    Args:
        to_email: Recipient address (dev may redirect to a fixed test inbox).
        from_email: Mailbox local part only (e.g. noreply, notifications).
        display_name: Inbox From display name (e.g. tenant company name or slug).
    """
    def __init__(self, to_email, from_email: str, display_name: str):
        self.to_email = 'mubskill@gmail.com' if self.ENV == 'development' else to_email
        self.from_email = self._format_from(from_email, display_name)

    def _public_domain(self) -> str:
        """Marketing / app host (e.g. usemaison.io) — not API base_url."""
        d = (self.DOMAIN or "usemaison.io").replace("https://", "").replace("http://", "").strip("/").split("/")[0]
        return d or "usemaison.io"

    def _maison_web(self, path: str) -> str:
        """Absolute URL on the public site, e.g. /tenant/login -> https://usemaison.io/tenant/login"""
        p = path if path.startswith("/") else f"/{path}"
        return f"https://{self._public_domain()}{p}"

    def _tenant_host(self, slug: str) -> str:
        return f"{slug}.{self._public_domain()}"

    def onboarding_email(self):

        params:resend.Emails.SendParams = {
        "from": self.from_email,
        "to": [self.to_email],
        "subject": "You have been successfully registered",
        "html": f"<p>Enter this </p>"
        }
        resend.Emails.send(params)

    def welcome_email(self, obj: Tenants, slug: str):
        """Send welcome email to tenant after account creation — B2B operator tone."""
        subject = "You're live on Maison"

        company_name = obj.profile.company_name if hasattr(obj, 'profile') and obj.profile else "Your company"
        host = self._tenant_host(slug)
        live_url = f"https://{host}"
        fn = L.first_name(obj.full_name)

        body = (
            L.p(f"Hi {fn},")
            + L.p(
                f"Your account is set up. <strong>{company_name}</strong> is live at:<br/>"
                f'<a href="{live_url}" style="color: #111827; text-decoration: underline; word-break: break-all;">{host}</a>'
            )
            + L.p(
                "Start by adding your first driver and vehicle — that's all you need before your first booking comes in."
            )
            + L.primary_cta(self._maison_web("/tenant/login"), "Go to your dashboard →")
            + L.muted_p("If you run into anything, reply to this email.")
            + L.signoff_maison_team()
        )
        html = L.build_email(body, footer_brand="Maison")
        self._email(subject, html)

    async def booking_notification_email(
        self,
        booking_obj,
        tenant_obj: Tenants,
        slug: str,
        rider_name: str = None,
        vehicle_info: str = None,
        driver_name: str = None,
    ):
        """Notify tenant of a new booking — factual, route + time + assignment."""
        rider_label = rider_name or "A rider"
        subject = f"New booking from {rider_label}"

        pickup_time = booking_obj.pickup_time.strftime("%B %d, %Y at %I:%M %p") if hasattr(booking_obj.pickup_time, 'strftime') else str(booking_obj.pickup_time)
        dropoff = getattr(booking_obj, 'dropoff_location', None) or ""
        pickup = booking_obj.pickup_location
        route_line = f"{pickup} → {dropoff}" if dropoff else pickup

        if driver_name:
            assign_line = f"Driver assigned: {driver_name}."
        else:
            assign_line = "Needs driver assignment."

        vehicle_line = f"<br/>Vehicle: {vehicle_info}" if vehicle_info else ""

        body = (
            L.p(f"Hi {L.first_name(tenant_obj.full_name)},")
            + L.p(f"<strong>{rider_label}</strong><br/>{route_line}<br/>{pickup_time}{vehicle_line}")
            + L.p(assign_line)
            + L.primary_cta(self._maison_web("/tenant/bookings"), "Open bookings →")
        )
        html = L.build_email(body, footer_brand="Maison")
        self._email(subject, html)

    def settings_change_email(self, tenant_obj: Tenants, slug: str, changed_settings: dict = None):
        """Critical settings changed — direct, no filler."""
        subject = "Settings updated"

        settings_block = ""
        if changed_settings:
            items = "".join(
                f"<li style='margin-bottom: 8px; font-family: {L.FONT}; font-size: 15px; color: {L.TEXT};'><strong>{k.replace('_', ' ').title()}:</strong> {v}</li>"
                for k, v in changed_settings.items()
            )
            settings_block = f"<ul style='margin: 16px 0 0 0; padding-left: 20px;'>{items}</ul>"

        body = (
            L.p(f"Hi {L.first_name(tenant_obj.full_name)},")
            + L.p("Your account settings were updated.")
            + (settings_block if settings_block else "")
            + L.p("If you didn't make this change, reply to this email.")
        )
        html = L.build_email(body, footer_brand="Maison")
        self._email(subject, html)

    def logo_update_confirmation_email(self, tenant_obj: Tenants, slug: str, logo_url: str = None):
        """Logo updated — one fact + optional preview."""
        subject = "Logo updated"

        logo_block = ""
        if logo_url:
            logo_block = f'<div style="margin: 20px 0;"><img src="{logo_url}" alt="" style="max-width: 200px; height: auto; border-radius: 8px;" /></div>'

        body = (
            L.p(f"Hi {L.first_name(tenant_obj.full_name)},")
            + L.p("Your logo is updated. It will show on your dashboard and customer-facing pages.")
            + logo_block
        )
        html = L.build_email(body, footer_brand="Maison")
        self._email(subject, html)

    def _email(self, subject, html):
        self.send_email(to_email=self.to_email, from_email=self.from_email,
                        subject=subject, html=html)
