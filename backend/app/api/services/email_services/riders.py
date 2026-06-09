import html
from datetime import timezone
from urllib.parse import quote
from zoneinfo import ZoneInfo

import resend
from .email_services import EmailServices
from app.models.user import Users
from . import email_layout as L


class RiderEmailServices(EmailServices):
    """
        Rider (customer) emails: warm but clean, premium service tone.
    Args:
        operator_name: Shown in footer as the operating company (e.g. tenant brand).
    """
    def __init__(
        self,
        to_email,
        from_email,
        operator_name: str = "Maison",
        display_name: str | None = None,
    ):
        brand = (
            display_name.replace("-", " ").title()
            if display_name
            else operator_name
        )
        self.to_email = 'mubskill@gmail.com' if self.ENV == 'development' else to_email
        if self.ENV == 'development':
            self.from_email = 'Acme <onboarding@resend.dev>'
        elif display_name and "@" not in str(from_email):
            self.from_email = self._format_from(from_email, display_name)
        else:
            self.from_email = from_email
        self.operator_name = brand
        self.default_tz = "America/Chicago"

    def _tenant_host(self, slug: str) -> str:
        domain = (
            (self.DOMAIN or "")
            .replace("https://", "")
            .replace("http://", "")
            .strip("/")
            .split("/")[0]
        )
        return f"{slug}.{domain}" if domain else slug

    def _confirm_booking_url(self, slug: str, confirm_token: str) -> str:
        host = self._tenant_host(slug)
        scheme = "https" if self.ENV == "production" else "http"
        return f"{scheme}://{host}/riders/confirm-booking?token={quote(confirm_token, safe='')}"

    def _format_local_datetime(self, dt, fmt: str = "%B %d, %Y at %I:%M %p") -> str:
        """Render datetimes in local rider timezone for email copy."""
        if dt is None:
            return "TBD"
        if hasattr(dt, 'tzinfo') and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(ZoneInfo(self.default_tz)).strftime(fmt)

    def onboarding_email(self):

        params:resend.Emails.SendParams = {
        "from": self.from_email,
        "to": [self.to_email],
        "subject": "You have been successfully registered",
        "html": f"<p>Enter this </p>"
        }
        resend.Emails.send(params)

    def welcome_email(self, obj: Users, slug: str):
        """Rider welcome — short, no banner hype."""
        subject = "Your account is ready"

        body = (
            L.p(f"Hi {L.first_name(obj.full_name)},")
            + L.p("You can book rides and manage trips from your account.")
            + L.primary_cta(f"{slug}.{self.BASE_URL}/riders/login", "Sign in →")
            + L.muted_p(f"Thank you for riding with {self.operator_name}.")
        )
        html_body = L.build_email(body, footer_brand=self.operator_name)
        self._email(subject, html_body)
    
    async def booking_cancellation_email(self):
        ...

    def new_ride(
        self,
        booking_obj,
        rider_info: Users,
        slug: str,
        confirm_token: str,
        vehicle_info: str | None = None,
    ):
        """Tenant-scheduled ride — prompt rider to confirm via signed link (no login)."""
        subject = f"{self.operator_name} scheduled a ride for you"

        pickup_time = self._format_local_datetime(booking_obj.pickup_time)
        dropoff = getattr(booking_obj, "dropoff_location", None) or ""
        estimated_price = (
            f"${booking_obj.estimated_price:.2f}"
            if hasattr(booking_obj, "estimated_price") and booking_obj.estimated_price is not None
            else "TBD"
        )

        details = (
            L.detail_kv("Pickup", L.highlight(booking_obj.pickup_location))
            + "<br/>"
            + (L.detail_kv("Drop-off", L.highlight(dropoff)) + "<br/>" if dropoff else "")
            + L.detail_kv("Time", html.escape(pickup_time, quote=False))
            + "<br/>"
        )
        if vehicle_info:
            details += L.detail_kv("Vehicle", html.escape(str(vehicle_info), quote=False)) + "<br/>"
        details += L.detail_kv("Estimate", html.escape(estimated_price, quote=False))

        confirm_url = self._confirm_booking_url(slug, confirm_token)
        first = L.first_name(getattr(rider_info, "full_name", None))

        body = (
            L.p(f"Hi {first},")
            + L.p(
                f"<strong>{html.escape(self.operator_name, quote=False)}</strong> has set up a ride "
                "for you. Please review the details below and confirm when you're ready."
            )
            + L.p(details)
            + L.primary_cta(confirm_url, "Review & confirm ride →")
            + L.muted_p(
                "This link works without signing in. If you did not expect this ride, "
                f"you can ignore this email or reply to reach {html.escape(self.operator_name, quote=False)}."
            )
        )
        html_body = L.build_email(body, footer_brand=self.operator_name)
        self._email(subject, html_body)

    async def booking_confirmation_email(
        self,
        booking_obj,
        rider_obj: Users,
        slug: str,
        vehicle_info: str = None,
        driver_name: str = None,
        driver_phone: str = None,
    ):
        """Booking confirmed — facts + one reassurance line."""
        subject = "Your ride is confirmed"

        pickup_time = (
            self._format_local_datetime(booking_obj.pickup_time)
            if hasattr(booking_obj.pickup_time, 'strftime')
            else str(booking_obj.pickup_time)
        )
        estimated_price = f"${booking_obj.estimated_price:.2f}" if hasattr(booking_obj, 'estimated_price') and booking_obj.estimated_price else "TBD"
        dropoff = getattr(booking_obj, 'dropoff_location', None) or ""

        details = (
            L.detail_kv("Pickup", L.highlight(booking_obj.pickup_location))
            + "<br/>"
            + (
                L.detail_kv("Drop-off", L.highlight(dropoff)) + "<br/>"
                if dropoff
                else ""
            )
            + L.detail_kv("Time", html.escape(pickup_time, quote=False))
            + "<br/>"
        )
        if driver_name:
            details += L.detail_kv("Driver", html.escape(str(driver_name), quote=False)) + "<br/>"
        if driver_phone and str(driver_phone).strip():
            details += L.detail_kv("Driver phone", html.escape(str(driver_phone), quote=False)) + "<br/>"
        if vehicle_info:
            details += L.detail_kv("Vehicle", html.escape(str(vehicle_info), quote=False)) + "<br/>"
        details += L.detail_kv("Estimate", html.escape(str(estimated_price), quote=False))

        body = (
            L.p(f"Hi {L.first_name(rider_obj.full_name)},")
            + L.p("Your ride is confirmed.")
            + L.p(details)
            + L.p("We'll send you a reminder one hour before pickup.")
        )
        html_body = L.build_email(body, footer_brand=self.operator_name)
        self._email(subject, html_body)

    def booking_status_update_email(
        self,
        booking_obj,
        rider_obj: Users,
        slug: str,
        old_status: str = None,
        feedback_url: str = None,
        driver_name: str = None,
        driver_phone: str = None,
        tenant_contact_email: str = None,
        tenant_contact_phone: str = None,
        review_comment: str = None,
    ):
        """Status change — factual; confirmed/completed get richer copy; optional feedback CTA on complete."""
        raw_status = (
            booking_obj.booking_status.lower()
            if hasattr(booking_obj, 'booking_status') and booking_obj.booking_status
            else 'pending'
        )
        status_text = booking_obj.booking_status.title() if hasattr(booking_obj, 'booking_status') else "Updated"
        first = L.first_name(rider_obj.full_name)
        feedback_href = (feedback_url or "").strip() or None

        if raw_status == 'confirmed':
            subject = f"Your {self.operator_name} ride is confirmed ✳︎"
            pickup_time = (
                self._format_local_datetime(booking_obj.pickup_time)
                if hasattr(booking_obj.pickup_time, 'strftime')
                else str(booking_obj.pickup_time)
            )
            dropoff = getattr(booking_obj, 'dropoff_location', None) or ""
            pickup = booking_obj.pickup_location
            estimate = (
                f"${booking_obj.estimated_price:.2f}"
                if hasattr(booking_obj, 'estimated_price') and booking_obj.estimated_price is not None
                else "TBD"
            )
            details_lines = (
                L.detail_kv("From", L.highlight(pickup))
                + "<br/>"
                + (L.detail_kv("To", L.highlight(dropoff)) + "<br/>" if dropoff else "")
                + L.detail_kv("Pickup time", html.escape(pickup_time, quote=False))
                + "<br/>"
                + (
                    L.detail_kv("Driver phone", html.escape(str(driver_phone), quote=False)) + "<br/>"
                    if driver_phone and str(driver_phone).strip()
                    else ""
                )
                + L.detail_kv("Estimate", html.escape(estimate, quote=False))
            )
            driver_line = (
                f"Your driver {driver_name} will arrive promptly at the scheduled time "
                "and ensure your journey is smooth from start to finish."
                if (driver_name and str(driver_name).strip())
                else (
                    "Your driver will arrive promptly at the scheduled time "
                    "and ensure your journey is smooth from start to finish."
                )
            )
            body = (
                L.p(f"Hi {first},")
                + L.p(
                    "We're all set for your upcoming trip. Here are the details so you can "
                    "travel with complete peace of mind:"
                )
                + L.p(details_lines)
                + L.p(driver_line)
                + L.p(
                    f"Thank you for riding with {self.operator_name} — we're looking forward to "
                    "getting you there comfortably and right on time."
                )
                + L.p(f"— The {self.operator_name} Team", margin_bottom="0")
            )
            html_body = L.build_email(body, footer_brand=self.operator_name)
            self._email(subject, html_body)
            return

        if raw_status == 'completed':
            subject = f"Thank you for riding with {self.operator_name}"
            pickup = booking_obj.pickup_location
            dropoff = getattr(booking_obj, 'dropoff_location', None) or ""
            body = (
                L.p(f"Hi {first},")
                + L.p(
                    f"Thanks for riding with {self.operator_name}. "
                    f"Your trip from {L.highlight(pickup)}"
                    + (f" to {L.highlight(dropoff)}" if dropoff else "")
                    + f" (Booking #{booking_obj.id}) is now complete."
                )
            )
            if review_comment and str(review_comment).strip():
                safe_comment = html.escape(str(review_comment).strip(), quote=False)
                body += L.p(
                    "We saw your review come through:"
                    f"<br/><span style=\"font-style: italic;\">\"{safe_comment}\"</span>"
                )
            body += L.p(
                "Really glad it went well, and thank you for taking the time to let us know. "
                "Feedback like this tells us what to keep doing."
            )
            if feedback_href:
                body += L.p(
                    f"If there's ever anything you'd like to pass along, "
                    f"<a href=\"{html.escape(feedback_href, quote=True)}\" "
                    "style=\"color:#0f172a;text-decoration:underline;\">share it here</a>."
                )
            body += L.p(
                "If there's ever anything you'd like to pass along, just reply to this email "
                "and it'll reach our team directly."
            )
            body += (
                L.p(
                    "We hope to drive you again soon."
                )
                + L.p(f"— The {self.operator_name} Team", margin_bottom="0")
            )
            html_body = L.build_email(body, footer_brand=self.operator_name)
            self._email(subject, html_body)
            return

        subject = f"Booking {status_text}"
        body = (
            L.p(f"Hi {first},")
            + L.p(f"Booking #{booking_obj.id} is now <strong>{status_text}</strong>.")
            + L.p(self._get_status_message_plain(raw_status))
        )
        html_body = L.build_email(body, footer_brand=self.operator_name)
        self._email(subject, html_body)

    def _get_status_message_plain(self, status: str) -> str:
        messages = {
            'confirmed': "Your driver will arrive at the scheduled pickup time.",
            'completed': f"Thank you for riding with {self.operator_name}.",
            'delayed': "Your pickup is running late. We'll update you if anything changes.",
            'cancelled': "This booking is cancelled. Contact us if you need a new ride.",
        }
        return messages.get(status, "If you have questions, reply to this email.")

    def booking_cancellation_email(
        self,
        booking_obj,
        rider_obj: Users,
        slug: str,
        cancellation_reason: str = None,
        driver_name: str = None,
        driver_phone: str = None,
    ):
        """Cancellation — brief, empathetic, not overwrought."""
        subject = "Booking cancelled"

        reason_block = L.p(f"Reason: {cancellation_reason}") if cancellation_reason else ""

        body = (
            L.p(f"Hi {L.first_name(rider_obj.full_name)},")
            + L.p(f"Booking #{booking_obj.id} has been cancelled.")
            + (
                L.p(
                    L.detail_kv(
                        "Driver",
                        html.escape(str(driver_name), quote=False),
                    )
                )
                if driver_name and str(driver_name).strip()
                else ""
            )
            + (
                L.p(
                    L.detail_kv(
                        "Driver phone",
                        html.escape(str(driver_phone), quote=False),
                    )
                )
                if driver_phone and str(driver_phone).strip()
                else ""
            )
            + reason_block
            + L.p("You can book again anytime from your account.")
            + L.primary_cta(f"{slug}.{self.BASE_URL}/riders/login", "Book a ride →")
        )
        html_body = L.build_email(body, footer_brand=self.operator_name)
        self._email(subject, html_body)

    def _email(self, subject, html):
        self.send_email(to_email=self.to_email, from_email=self.from_email,
                        subject=subject, html=html)
