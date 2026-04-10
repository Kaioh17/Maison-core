import html

from .email_services import EmailServices
from app.models.driver import Drivers
from . import email_layout as L


class DriverEmailServices(EmailServices):
    """
    Driver emails: practical, mobile-first, minimal copy.
    Args:
        from_email: Mailbox local part only (e.g. notifications).
        display_name: From display name (e.g. company or slug).
    """
    def __init__(self, to_email, from_email: str, display_name: str):
        self.to_email = 'mubskill@gmail.com' if self.ENV == 'development' else to_email
        self.from_email = self._format_from(from_email, display_name)

    def _tenant_host(self, slug: str) -> str:
        domain = (self.DOMAIN or "").replace("https://", "").replace("http://", "").strip("/").split("/")[0]
        return f"{slug}.{domain}" if domain else slug

    def _company_label(self, obj: Drivers) -> str:
        if getattr(obj, "tenants", None) and getattr(obj.tenants, "profile", None):
            return obj.tenants.profile.company_name or obj.slug
        return obj.slug.replace("-", " ").title() if obj.slug else "your operator"

    def onboarding_email(self, token, slug):
        subject = "Complete your driver registration"
        host = self._tenant_host(slug)
        verify_url = f"https://{host}/driver/verify"

        body = (
            L.p("Use this code to finish registration (valid 24 hours):")
            + f"""
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: 20px 0; background-color: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px;">
                <tr>
                    <td style="padding: 20px; text-align: center;">
                        <p style="margin: 0 0 8px 0; font-family: {L.FONT}; font-size: 12px; font-weight: 500; color: {L.MUTED}; text-transform: uppercase; letter-spacing: 0.06em;">Verification code</p>
                        <p style="margin: 0; font-family: {L.FONT}; font-size: 22px; font-weight: 600; color: {L.TEXT}; letter-spacing: 0.12em; word-break: break-all;">{token}</p>
                    </td>
                </tr>
            </table>
            """
            + L.primary_cta(verify_url, "Complete registration →")
            + L.muted_p(f'Or open: <a href="{verify_url}" style="color:{L.MUTED};">{verify_url}</a>')
            + L.p("If you didn’t expect this, ignore this email.", margin_bottom="0")
        )
        html_body = L.build_email(body, footer_brand=self._company_label_from_slug(slug))
        self._email(subject, html_body)

    def _company_label_from_slug(self, slug: str) -> str:
        return slug.replace("-", " ").title() if slug else "Maison"

    def welcome_(self, obj: Drivers):
        subject = "You're on Maison"
        company = self._company_label(obj)
        host = self._tenant_host(obj.slug)
        sign_in = f"https://{host}/driver/login"

        body = (
            L.p(f"Hi {L.first_name(obj.full_name)},")
            + L.p(
                f"You've been added to <strong>{company}</strong> on Maison. "
                f"Download the app or sign in at <a href=\"{sign_in}\" style=\"color: #111827;\">{host}</a>."
            )
            + L.primary_cta(sign_in, "Sign in →")
        )
        html_body = L.build_email(body, footer_brand=company)
        self._email(subject, html_body)

    def new_ride(self, booking_obj: object, assigned: bool = False, slug: str = None, rider_name: str = None):
        """New ride — pickup, passenger, time; optional assignment flag."""
        passenger = rider_name
        if passenger is None and getattr(booking_obj, "rider", None) is not None:
            passenger = getattr(booking_obj.rider, "full_name", None) or getattr(booking_obj.rider, "email", "Passenger")
        if not passenger:
            passenger = "Passenger"

        pickup_time = booking_obj.pickup_time.strftime("%B %d, %Y at %I:%M %p") if hasattr(booking_obj.pickup_time, 'strftime') else str(booking_obj.pickup_time)
        pickup = booking_obj.pickup_location

        subject = "New ride assigned" if assigned else "New ride available"

        suffix = "/driver/bookings"
        cta_url = f"{self.BASE_URL}/{slug or 'default'}{suffix}"

        body = (
            L.p(L.detail_kv("Pickup", L.highlight(pickup)))
            + L.p(L.detail_kv("Passenger", html.escape(str(passenger), quote=False)))
            + L.p(L.detail_kv("Time", html.escape(pickup_time, quote=False)))
            + L.primary_cta(cta_url, "Open in app →")
        )
        html_body = L.build_email(body, footer_brand=self._company_label_from_slug(slug or ""))
        self._email(subject, html_body)

    def status_change_email(self, obj: Drivers, is_active: bool):
        status_text = "active" if is_active else "inactive"
        subject = f"Your driver account is {status_text}"

        msg = (
            "You can accept rides again from the driver app."
            if is_active
            else "You won’t receive new rides until your account is reactivated. Reply to this email if this looks wrong."
        )

        body = (
            L.p(f"Hi {L.first_name(obj.full_name)},")
            + L.p(f"Your account is now <strong>{status_text}</strong>.")
            + L.p(msg)
            + L.primary_cta(f"{self.BASE_URL}/{obj.slug}/driver/login", "Sign in →")
        )
        html_body = L.build_email(body, footer_brand=self._company_label(obj))
        self._email(subject, html_body)

    def vehicle_assignment_email(self, obj: Drivers, vehicle_obj):
        subject = "Vehicle assigned to you"
        vehicle_name = f"{vehicle_obj.make} {vehicle_obj.model} {vehicle_obj.year}" if getattr(vehicle_obj, "year", None) else f"{vehicle_obj.make} {vehicle_obj.model}"
        plate = getattr(vehicle_obj, "license_plate", None) or ""

        body = (
            L.p(f"Hi {L.first_name(obj.full_name)},")
            + L.p(f"Vehicle: {vehicle_name}")
            + (L.p(f"Plate: {plate}") if plate else "")
            + L.primary_cta(f"https://{self._tenant_host(obj.slug)}/driver/login", "View in app →")
        )
        html_body = L.build_email(body, footer_brand=self._company_label(obj))
        self._email(subject, html_body)

    def vehicle_unassignment_email(self, obj: Drivers, vehicle_obj):
        subject = "Vehicle unassigned"
        if getattr(vehicle_obj, "vehicle_name", None):
            vehicle_name = vehicle_obj.vehicle_name
        else:
            vehicle_name = f"{vehicle_obj.make} {vehicle_obj.model}"
        plate = getattr(vehicle_obj, "license_plate", None) or ""

        body = (
            L.p(f"Hi {L.first_name(obj.full_name)},")
            + L.p(f"You’re no longer assigned to: {vehicle_name}")
            + (L.p(f"Plate was: {plate}") if plate else "")
            + L.p("Questions? Reply to this email.")
        )
        html_body = L.build_email(body, footer_brand=self._company_label(obj))
        self._email(subject, html_body)

    def _email(self, subject, html):
        self.send_email(to_email=self.to_email, from_email=self.from_email,
                        subject=subject, html=html)
