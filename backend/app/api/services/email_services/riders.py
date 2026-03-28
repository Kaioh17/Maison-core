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
        html = L.build_email(body, footer_brand=self.operator_name)
        self._email(subject, html)

    async def booking_confirmation_email(self, booking_obj, rider_obj: Users, slug: str, vehicle_info: str = None, driver_name: str = None):
        """Booking confirmed — facts + one reassurance line."""
        subject = "Your ride is confirmed"

        pickup_time = booking_obj.pickup_time.strftime("%B %d, %Y at %I:%M %p") if hasattr(booking_obj.pickup_time, 'strftime') else str(booking_obj.pickup_time)
        estimated_price = f"${booking_obj.estimated_price:.2f}" if hasattr(booking_obj, 'estimated_price') and booking_obj.estimated_price else "TBD"
        dropoff = getattr(booking_obj, 'dropoff_location', None) or ""

        details = (
            f"Pickup: {booking_obj.pickup_location}<br/>"
            + (f"Drop-off: {dropoff}<br/>" if dropoff else "")
            + f"Time: {pickup_time}<br/>"
        )
        if driver_name:
            details += f"Driver: {driver_name}<br/>"
        if vehicle_info:
            details += f"Vehicle: {vehicle_info}<br/>"
        details += f"Estimate: {estimated_price}"

        body = (
            L.p(f"Hi {L.first_name(rider_obj.full_name)},")
            + L.p("Your ride is confirmed.")
            + L.p(details)
            + L.p("We'll send you a reminder one hour before pickup.")
        )
        html = L.build_email(body, footer_brand=self.operator_name)
        self._email(subject, html)

    def booking_status_update_email(self, booking_obj, rider_obj: Users, slug: str, old_status: str = None):
        """Status change — factual."""
        status_text = booking_obj.booking_status.title() if hasattr(booking_obj, 'booking_status') else "Updated"
        subject = f"Booking {status_text}"

        body = (
            L.p(f"Hi {L.first_name(rider_obj.full_name)},")
            + L.p(f"Booking #{booking_obj.id} is now <strong>{status_text}</strong>.")
            + L.p(self._get_status_message_plain(booking_obj.booking_status.lower() if hasattr(booking_obj, 'booking_status') else 'pending'))
        )
        html = L.build_email(body, footer_brand=self.operator_name)
        self._email(subject, html)

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
        html = L.build_email(body, footer_brand=self.operator_name)
        self._email(subject, html)

    def _email(self, subject, html):
        self.send_email(to_email=self.to_email, from_email=self.from_email,
                        subject=subject, html=html)
