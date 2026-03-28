import resend
from .email_services import EmailServices
from app.models.tenant import Tenants
from . import email_layout as L


class AdminEmailServices(EmailServices):
    """
    Platform admin notifications — brief, factual.
    """
    def __init__(self, to_email, from_email: str = 'noreply', display_name: str = 'Maison'):
        self.to_email = 'mubskill@gmail.com' if self.ENV == 'development' else to_email
        self.from_email = self._format_from(from_email, display_name)

    def onboarding_email(self):

        params:resend.Emails.SendParams = {
        "from": self.from_email,
        "to": [self.to_email],
        "subject": "You have been successfully registered",
        "html": f"<p>Enter this </p>"
        }
        resend.Emails.send(params)

    def notify_new_tenant(self, tenant_obj: Tenants):
        """Notify admin when a new tenant is registered"""
        self.new_tenant_notification_email(tenant_obj)

    def new_tenant_notification_email(self, tenant_obj: Tenants):
        subject = "New tenant registered"

        company_name = tenant_obj.profile.company_name if hasattr(tenant_obj, 'profile') and tenant_obj.profile else "N/A"
        slug = tenant_obj.slug if hasattr(tenant_obj, 'slug') else "N/A"
        created_date = tenant_obj.created_on.strftime("%B %d, %Y at %I:%M %p") if hasattr(tenant_obj.created_on, 'strftime') else str(tenant_obj.created_on)

        phone_row = ""
        if hasattr(tenant_obj, 'phone_no') and tenant_obj.phone_no:
            phone_row = L.p(f"Phone: {tenant_obj.phone_no}")

        body = (
            L.p("New operator signup:")
            + L.p(
                f"ID #{tenant_obj.id} · {company_name}<br/>"
                f"Contact: {tenant_obj.full_name} ({tenant_obj.email})<br/>"
                f"Host: {slug}<br/>"
                f"Registered: {created_date}"
            )
            + phone_row
        )
        html = L.build_email(body, footer_brand="Maison")
        self._email(subject, html)

    def tenant_deletion_confirmation_email(self, tenant_id: int, company_name: str = None, deleted_by: str = None):
        subject = "Tenant account removed"

        body = (
            L.p(f"Tenant ID #{tenant_id} was deleted from the platform.")
            + (L.p(f"Company: {company_name}") if company_name else "")
            + (L.p(f"Deleted by: {deleted_by}") if deleted_by else "")
            + L.p("Associated drivers, vehicles, and bookings are removed.")
        )
        html = L.build_email(body, footer_brand="Maison")
        self._email(subject, html)

    def _email(self, subject, html):
        self.send_email(to_email=self.to_email, from_email=self.from_email,
                        subject=subject, html=html)
