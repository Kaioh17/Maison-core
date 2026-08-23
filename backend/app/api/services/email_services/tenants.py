import html

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

    def _maison_web(self, path: str) -> str:
        """Absolute URL on the public site, e.g. /tenant/login -> https://usemaison.io/tenant/login
        in production, or http://localhost:3000/tenant/login in local dev -- follows DOMAIN/ENV
        from config rather than hardcoding the prod host, so local emails are actually clickable."""
        return self._public_url(path)

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
        subject = "One step left to go live"

        fn = L.first_name(obj.full_name)
        host = self._tenant_host(slug)

        verification_content = (
            L.p(
                "<strong>Complete identity and payment verification</strong>",
                margin_bottom="10px",
            )
            + L.p(
                "Maison uses Stripe to verify operator identities and process payments. "
                "This step activates your booking page and enables you to accept payments from customers. "
                "It typically takes a few minutes — Stripe may request additional documents in some cases.",
                margin_bottom="20px",
            )
            + L.primary_cta(self._maison_web("/tenant/settings/account"), "Complete verification →")
        )

        body = (
            L.p(f"Hi {fn},")
            + L.p(
                "Your Maison account has been created. Before your platform goes live, "
                "you need to complete one required step: identity and payment verification through Stripe."
            )
            + L.section_block(verification_content)
            + L.p(
                "Once verification is approved, you'll be able to:",
                margin_bottom="8px",
            )
            + L.p(
                "Add your first driver&nbsp;&nbsp;·&nbsp;&nbsp;"
                "Add a vehicle to your fleet&nbsp;&nbsp;·&nbsp;&nbsp;"
                "Share your booking page with customers",
                margin_bottom="24px",
            )
            + L.p(
                f'Your booking page will be live at '
                f'<span style="font-family: {L.FONT_MONO}; font-size: 0.92em; color: {L.MUTED}; word-break: break-all;">{host}</span> '
                f"once verification is complete. It is not active yet.",
                margin_bottom="0",
            )
            + L.muted_p("If you run into anything, reply to this email.")
            + L.signoff_maison_team()
        )
        html_body = L.build_email(body, footer_brand="Maison")
        self._email(subject, html_body)

    def stripe_completion_reminder_email(self, obj: Tenants, onboarding_link: str):
        """Remind a tenant to finish their Stripe payout/account setup — sent by admin."""
        subject = "Action needed: complete your identity verification and Stripe setup"

        company_name = obj.profile.company_name if hasattr(obj, 'profile') and obj.profile else "Your company"
        fn = L.first_name(obj.full_name)

        body = (
            L.p(f"Hi {fn},")
            + L.p(
                f"<strong>{company_name}</strong> has a required step outstanding: your identity "
                "verification and Stripe account setup are not yet complete."
            )
            + L.p(
                "This verification step serves two purposes — it confirms your identity as a legitimate "
                "operator, and it enables your account to accept payments and receive payouts through Stripe."
            )
            + L.p(
                "Until both are complete, you won't have access to your white-label features — your "
                "branded subdomain, custom branding, and the rest of your operator dashboard stay locked."
            )
            + L.p(
                "It only takes a couple of minutes — tap below to pick up where you left off and complete "
                "your identity verification and Stripe details to unlock full access."
            )
            + L.primary_cta(onboarding_link, "Complete verification →")
            + L.muted_p("This secure link is provided by Stripe and may expire — request a new one if it stops working.")
            + L.signoff_maison_team()
        )
        html_body = L.build_email(body, footer_brand="Maison")
        self._email(subject, html_body)

    def booking_cancellation_email(
        self,
        booking_obj,
        tenant_obj: Tenants,
        slug: str,
        rider_name: str = None,
        rider_phone: str = None,
        vehicle_info: str = None,
        driver_name: str = None,
        driver_phone: str = None,
    ):
        """Notify tenant when a trip is cancelled."""
        passenger = (rider_name or "").strip() or "Passenger"
        pickup = getattr(booking_obj, "pickup_location", None) or "TBD"
        dropoff = getattr(booking_obj, "dropoff_location", None) or ""
        pickup_time = (
            booking_obj.pickup_time.strftime("%B %d, %Y at %I:%M %p")
            if hasattr(booking_obj, "pickup_time") and hasattr(booking_obj.pickup_time, "strftime")
            else str(getattr(booking_obj, "pickup_time", "TBD"))
        )
        vehicle_line = vehicle_info if (vehicle_info and str(vehicle_info).strip()) else "TBD"
        driver_line = driver_name if (driver_name and str(driver_name).strip()) else "Unassigned"

        subject = f"Trip cancelled — {passenger}"
        route = (
            f"{L.highlight(pickup)} → {L.highlight(dropoff)}"
            if dropoff
            else L.highlight(pickup)
        )
        details = (
            L.detail_kv("Passenger", html.escape(passenger, quote=False))
            + "<br/>"
            + (
                L.detail_kv("Passenger phone", html.escape(str(rider_phone), quote=False)) + "<br/>"
                if rider_phone and str(rider_phone).strip()
                else ""
            )
            + L.detail_kv("Route", route)
            + "<br/>"
            + L.detail_kv("Pickup time", html.escape(pickup_time, quote=False))
            + "<br/>"
            + L.detail_kv("Vehicle", html.escape(str(vehicle_line), quote=False))
            + "<br/>"
            + L.detail_kv("Driver", html.escape(str(driver_line), quote=False))
            + (
                "<br/>" + L.detail_kv("Driver phone", html.escape(str(driver_phone), quote=False))
                if driver_phone and str(driver_phone).strip()
                else ""
            )
        )
        body = (
            L.p(f"Hi {L.first_name(tenant_obj.full_name)},")
            + L.p("A booked trip has been cancelled.")
            + L.p(details)
            + L.p(
                f"Review your schedule in the dashboard to reassign availability if needed for {slug}."
            )
        )
        html_body = L.build_email(body, footer_brand="Maison")
        self._email(subject, html_body)
    async def booking_notification_email(
        self,
        booking_obj,
        tenant_obj: Tenants,
        slug: str,
        rider_name: str = None,
        rider_phone: str = None,
        vehicle_info: str = None,
        driver_name: str = None,
        driver_phone: str = None,
    ):
        """Notify tenant when a trip is confirmed — dashboard-oriented summary."""
        passenger = (rider_name or "").strip() or "Passenger"

        pt = booking_obj.pickup_time
        if hasattr(pt, "strftime"):
            month_day = pt.strftime("%B ") + str(pt.day)
            pickup_time_full = pt.strftime("%B %d, %Y at %I:%M %p")
        else:
            month_day = str(pt)
            pickup_time_full = str(pt)

        subject = f"New trip confirmed — {passenger} ({month_day})"

        dropoff = getattr(booking_obj, "dropoff_location", None) or ""
        pickup = booking_obj.pickup_location
        route_display = (
            f"{L.highlight(pickup)} → {L.highlight(dropoff)}" if dropoff else L.highlight(pickup)
        )

        vehicle_line = vehicle_info if (vehicle_info and str(vehicle_info).strip()) else "TBD"
        driver_line = (
            driver_name.strip()
            if (driver_name and str(driver_name).strip())
            else "To be assigned"
        )

        details = (
            L.detail_kv("Passenger", html.escape(passenger, quote=False))
            + "<br/>"
            + (
                L.detail_kv("Passenger phone", html.escape(str(rider_phone), quote=False)) + "<br/>"
                if rider_phone and str(rider_phone).strip()
                else ""
            )
            + L.detail_kv("Route", route_display)
            + "<br/>"
            + L.detail_kv("Pickup time", html.escape(pickup_time_full, quote=False))
            + "<br/>"
            + L.detail_kv("Vehicle", html.escape(str(vehicle_line), quote=False))
            + "<br/>"
            + L.detail_kv("Driver", html.escape(str(driver_line), quote=False))
            + (
                "<br/>" + L.detail_kv("Driver phone", html.escape(str(driver_phone), quote=False))
                if driver_phone and str(driver_phone).strip()
                else ""
            )
        )

        body = (
            L.p(f"Hi {L.first_name(tenant_obj.full_name)},")
            + L.p("A new trip has been confirmed and added to your dashboard.")
            + L.p(details)
            + L.p(
                "Every confirmed booking is a moment of trust — both from your passenger "
                "and the chauffeur behind the wheel. Maison helps ensure that connection "
                "runs smoothly."
            )
            + L.p("Thanks for continuing to build your service on Maison.")
            + L.p("— Maison Operations", margin_bottom="0")
        )
        html_body = L.build_email(body, footer_brand="Maison")
        self._email(subject, html_body)

    def founding_operator_email(self, tenant_obj: Tenants, promo_code: str):
        """Sent once, right after signup, to one of the first 10 tenants — the
        code is never shown in the UI, only here, so it's redeemable at
        Stripe Checkout (`allow_promotion_codes`) for 100% off."""
        subject = "You're a Maison founding operator — your code is free"

        body = (
            L.p(f"Hi {L.first_name(tenant_obj.full_name)},")
            + L.p(
                "You're one of our first 10 operators, so your subscription is on us. "
                "When you get to checkout, enter this promo code for 100% off:"
            )
            + L.p(
                "This covers the plan you pick today. If you upgrade to a higher "
                "tier later, that tier is billed at full price.",
                margin_bottom="0",
            )
            + L.section_block(
                L.p(
                    f'<span style="font-family: {L.FONT_MONO}; font-size: 1.1em; font-weight: 600;">{html.escape(promo_code)}</span>',
                    margin_bottom="0",
                )
            )
            + L.p(
                "A card is still required to activate the subscription — the coupon covers the charge.",
                margin_bottom="0",
            )
            + L.signoff_maison_team()
        )
        html_body = L.build_email(body, footer_brand="Maison")
        self._email(subject, html_body)

    def subscription_confirmation_email(self, tenant_obj: Tenants, plan: str):
        """Confirm to the tenant that their subscription is now active."""
        subject = "Your Maison subscription is active"

        plan_display = (plan or "Free").replace("_", " ").title()
        fn = L.first_name(tenant_obj.full_name)

        body = (
            L.p(f"Hi {fn},")
            + L.p(
                f"You're now on the <strong>{plan_display}</strong> plan. "
                "Your subscription is active and your account is ready to use."
            )
            + L.p(
                "You can manage or upgrade your plan at any time from your account settings."
            )
            + L.primary_cta(self._maison_web("/tenant/overview"), "Go to your dashboard →")
            + L.signoff_maison_team()
        )
        html_body = L.build_email(body, footer_brand="Maison")
        self._email(subject, html_body)

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
        html_body = L.build_email(body, footer_brand="Maison")
        self._email(subject, html_body)

    def driver_application_email(self, tenant_obj: Tenants, driver_obj, slug: str):
        """Notify the tenant a driver applied through the public site and needs review/approval."""
        applicant_name = f"{driver_obj.first_name} {driver_obj.last_name}".strip()
        subject = f"New driver application — {applicant_name}"

        driver_type_label = (getattr(driver_obj, "driver_type", "") or "").replace("_", " ").title()

        details = (
            L.detail_kv("Name", html.escape(applicant_name, quote=False))
            + "<br/>"
            + L.detail_kv("Email", html.escape(driver_obj.email, quote=False))
            + (
                "<br/>" + L.detail_kv("Driver type", html.escape(driver_type_label, quote=False))
                if driver_type_label
                else ""
            )
        )

        body = (
            L.p(f"Hi {L.first_name(tenant_obj.full_name)},")
            + L.p(f"<strong>{applicant_name}</strong> applied to drive for you. Review the request and approve it to send them their registration link.")
            + L.p(details)
            + L.primary_cta(self._maison_web("/tenant/drivers"), "Review application →")
        )
        html_body = L.build_email(body, footer_brand="Maison")
        self._email(subject, html_body)

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
        html_body = L.build_email(body, footer_brand="Maison")
        self._email(subject, html_body)

    def _email(self, subject, html):
        self.send_email(to_email=self.to_email, from_email=self.from_email,
                        subject=subject, html=html)
