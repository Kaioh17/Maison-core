import html

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
    def __init__(self, to_email, from_email, operator_name: str = "Maison"):
        self.to_email = 'mubskill@gmail.com' if self.ENV == 'development' else to_email
        self.from_email = (
            'Acme <onboarding@resend.dev>'
            if self.ENV == 'development'
            else from_email
        )
        self.operator_name = operator_name

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
            + L.primary_cta(f"{self.BASE_URL}/{slug}/rider/login", "Sign in →")
            + L.muted_p(f"Thank you for riding with {self.operator_name}.")
        )
        html_body = L.build_email(body, footer_brand=self.operator_name)
        self._email(subject, html_body)

    async def booking_confirmation_email(self, booking_obj, rider_obj: Users, slug: str, vehicle_info: str = None, driver_name: str = None):
        """Booking confirmed — facts + one reassurance line."""
        subject = "Your ride is confirmed"

        pickup_time = booking_obj.pickup_time.strftime("%B %d, %Y at %I:%M %p") if hasattr(booking_obj.pickup_time, 'strftime') else str(booking_obj.pickup_time)
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
        tenant_contact_email: str = None,
        tenant_contact_phone: str = None,
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
                booking_obj.pickup_time.strftime("%B %d, %Y at %I:%M %p")
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
            if dropoff:
                journey = (
                    f"We hope your journey from {L.highlight(pickup)} to {L.highlight(dropoff)} "
                    "was seamless and comfortable."
                )
            else:
                journey = (
                    f"We hope your journey from {L.highlight(pickup)} was seamless and comfortable."
                )
            body = (
                L.p(f"Hi {first},")
                + L.p(
                    f"{journey} Your trip (Booking #{booking_obj.id}) is now complete."
                )
                + L.p(
                    "It was truly a pleasure having you ride with us. We take every trip personally "
                    "and always want to ensure your experience feels effortless and exceptional."
                )
            )
            body += L.p(
                "If you have a moment, we'd love to hear how everything went—"
                "your thoughts help us refine every detail for next time."
            )
            if feedback_href:
                body += L.primary_cta(feedback_href, "Share your feedback →")
            else:
                body += L.muted_p(
                    "You can reply directly to this email if you'd like to share anything with our team."
                )
            body += L.completed_ride_dispute_notice(
                tenant_contact_email,
                tenant_contact_phone,
                operator_name=self.operator_name,
            )
            body += (
                L.p(
                    f"Thank you for choosing {self.operator_name}. "
                    "We look forward to driving you again soon."
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

    def booking_cancellation_email(self, booking_obj, rider_obj: Users, slug: str, cancellation_reason: str = None):
        """Cancellation — brief, empathetic, not overwrought."""
        subject = "Booking cancelled"

        reason_block = L.p(f"Reason: {cancellation_reason}") if cancellation_reason else ""

        body = (
            L.p(f"Hi {L.first_name(rider_obj.full_name)},")
            + L.p(f"Booking #{booking_obj.id} has been cancelled.")
            + reason_block
            + L.p("You can book again anytime from your account.")
            + L.primary_cta(f"{self.BASE_URL}/{slug}/rider/book", "Book a ride →")
        )
        html_body = L.build_email(body, footer_brand=self.operator_name)
        self._email(subject, html_body)

    def _email(self, subject, html):
        self.send_email(to_email=self.to_email, from_email=self.from_email,
                        subject=subject, html=html)
