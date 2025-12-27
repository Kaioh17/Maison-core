import resend
from app.config import Settings
from .email_services import EmailServices
from app.models.user import Users

class RiderEmailServices(EmailServices):
    """
        Inherits the parentclass EmailServices with the set
        purpose: As the name implies, it will be used to send rider related emails for all tenants on our service.
        The from email used here should be tailored by the tenants, 
        the content of the email can be tailored too if not there will be a default service that handles this.
    Args:
        EmailServices (_type_): _description_
    """
    def __init__(self, to_email, from_email):
        self.to_email = 'mubskill@gmail.com'
        self.from_email = 'Acme <onboarding@resend.dev>'
    # from_email = "Acme <onboarding@resend.dev>"
    def onboarding_email(self):
        
        params:resend.Emails.SendParams = {
        "from": self.from_email,
        "to": [self.to_email],
        "subject": "You have been successfully registered",
        "html": f"<p>Enter this </p>"
        }
        resend.Emails.send(params)
    
    def welcome_email(self, obj: Users, slug: str):
        """Send welcome email to rider after account creation"""
        subject = "Welcome to Our Service!"
        
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f5f5f5;">
                <tr>
                    <td align="center" style="padding: 48px 16px;">
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
                            <tr>
                                <td style="padding: 40px 40px 32px 40px; text-align: center; background: linear-gradient(135deg, #9B61D1 0%, #8750BD 100%); border-radius: 8px 8px 0 0;">
                                    <h1 style="margin: 0; font-family: 'DM Sans', sans-serif; font-size: 32px; font-weight: 600; color: #ffffff; line-height: 1.2;">
                                        Welcome Aboard!
                                    </h1>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 40px 40px 32px 40px;">
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 18px; line-height: 1.6; color: #1f2937; font-weight: 500;">
                                        Hello {full_name}!
                                    </p>
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        Thank you for creating an account with us! We're excited to have you as part of our community.
                                    </p>
                                    <p style="margin: 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        You can now book rides, track your trips, and manage your account all in one place.
                                    </p>
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                        <tr>
                                            <td align="center" style="padding: 24px 0 8px 0;">
                                                <a href="{base_url}/{slug}/rider/login" style="display: inline-block; padding: 14px 32px; background-color: #9B61D1; color: #ffffff; text-decoration: none; font-family: 'Work Sans', sans-serif; font-size: 16px; font-weight: 500; border-radius: 8px; text-align: center;">
                                                    Get Started
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 32px 40px; background-color: #f9fafb; border-top: 1px solid #e5e7eb; border-radius: 0 0 8px 8px;">
                                    <p style="margin: 0; font-family: 'Work Sans', sans-serif; font-size: 13px; line-height: 1.5; color: #6b7280; text-align: center;">
                                        © 2024 All rights reserved.
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """.format(
            full_name=obj.full_name,
            base_url=self.BASE_URL,
            slug=slug
        )
        self._email(subject, html)
    
    def booking_confirmation_email(self, booking_obj, rider_obj: Users, slug: str, vehicle_info: str = None, driver_name: str = None):
        """Send booking confirmation email to rider"""
        subject = "Booking Confirmed - Your Ride is Scheduled"
        
        pickup_time = booking_obj.pickup_time.strftime("%B %d, %Y at %I:%M %p") if hasattr(booking_obj.pickup_time, 'strftime') else str(booking_obj.pickup_time)
        estimated_price = f"${booking_obj.estimated_price:.2f}" if hasattr(booking_obj, 'estimated_price') and booking_obj.estimated_price else "TBD"
        
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Booking Confirmed</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f5f5f5;">
                <tr>
                    <td align="center" style="padding: 48px 16px;">
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
                            <tr>
                                <td style="padding: 40px 40px 32px 40px; text-align: center; background: linear-gradient(135deg, #1E7F4A 0%, #1A6B3A 100%); border-radius: 8px 8px 0 0;">
                                    <h1 style="margin: 0; font-family: 'DM Sans', sans-serif; font-size: 32px; font-weight: 600; color: #ffffff; line-height: 1.2;">
                                        Booking Confirmed!
                                    </h1>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 40px 40px 32px 40px;">
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 18px; line-height: 1.6; color: #1f2937; font-weight: 500;">
                                        Hello {full_name},
                                    </p>
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        Your ride has been successfully booked. Here are the details:
                                    </p>
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: 32px 0; background-color: #f9fafb; border-left: 4px solid #1E7F4A; border-radius: 4px;">
                                        <tr>
                                            <td style="padding: 20px 24px;">
                                                <p style="margin: 0 0 12px 0; font-family: 'Work Sans', sans-serif; font-size: 13px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">
                                                    Booking Details
                                                </p>
                                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                                    <tr>
                                                        <td style="padding: 4px 0;">
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Booking ID:</span>
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">#{booking_id}</span>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding: 4px 0;">
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Pickup Location:</span>
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{pickup_location}</span>
                                                        </td>
                                                    </tr>
                                                    {dropoff_row}
                                                    <tr>
                                                        <td style="padding: 4px 0;">
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Pickup Time:</span>
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{pickup_time}</span>
                                                        </td>
                                                    </tr>
                                                    {vehicle_row}
                                                    {driver_row}
                                                    <tr>
                                                        <td style="padding: 4px 0;">
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Estimated Price:</span>
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px; font-weight: 600;">{estimated_price}</span>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                    <p style="margin: 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        We'll send you updates as your ride approaches. If you need to make any changes, please contact us.
                                    </p>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 32px 40px; background-color: #f9fafb; border-top: 1px solid #e5e7eb; border-radius: 0 0 8px 8px;">
                                    <p style="margin: 0; font-family: 'Work Sans', sans-serif; font-size: 13px; line-height: 1.5; color: #6b7280; text-align: center;">
                                        © 2024 All rights reserved.
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """.format(
            full_name=rider_obj.full_name,
            booking_id=booking_obj.id,
            pickup_location=booking_obj.pickup_location,
            dropoff_row='<tr><td style="padding: 4px 0;"><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Dropoff Location:</span><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{}</span></td></tr>'.format(booking_obj.dropoff_location) if hasattr(booking_obj, 'dropoff_location') and booking_obj.dropoff_location else '',
            pickup_time=pickup_time,
            vehicle_row='<tr><td style="padding: 4px 0;"><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Vehicle:</span><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{}</span></td></tr>'.format(vehicle_info) if vehicle_info else '',
            driver_row='<tr><td style="padding: 4px 0;"><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Driver:</span><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{}</span></td></tr>'.format(driver_name) if driver_name else '',
            estimated_price=estimated_price
        )
        self._email(subject, html)
    
    def booking_status_update_email(self, booking_obj, rider_obj: Users, slug: str, old_status: str = None):
        """Send email notification when booking status changes"""
        status_text = booking_obj.booking_status.title() if hasattr(booking_obj, 'booking_status') else "Updated"
        status_colors = {
            'pending': '#F59E0B',
            'confirmed': '#1E7F4A',
            'completed': '#1E7F4A',
            'cancelled': '#DC2626',
            'delayed': '#F59E0B'
        }
        status_color = status_colors.get(booking_obj.booking_status.lower() if hasattr(booking_obj, 'booking_status') else 'pending', '#9B61D1')
        
        subject = f"Booking Status Update - {status_text}"
        
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Booking Status Update</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f5f5f5;">
                <tr>
                    <td align="center" style="padding: 48px 16px;">
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
                            <tr>
                                <td style="padding: 40px 40px 32px 40px; text-align: center; background: linear-gradient(135deg, {status_color} 0%, {status_color_dark} 100%); border-radius: 8px 8px 0 0;">
                                    <h1 style="margin: 0; font-family: 'DM Sans', sans-serif; font-size: 32px; font-weight: 600; color: #ffffff; line-height: 1.2;">
                                        Status: {status_text}
                                    </h1>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 40px 40px 32px 40px;">
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 18px; line-height: 1.6; color: #1f2937; font-weight: 500;">
                                        Hello {full_name},
                                    </p>
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        Your booking #{booking_id} status has been updated to <strong style="color: {status_color};">{status_text}</strong>.
                                    </p>
                                    {status_message}
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 32px 40px; background-color: #f9fafb; border-top: 1px solid #e5e7eb; border-radius: 0 0 8px 8px;">
                                    <p style="margin: 0; font-family: 'Work Sans', sans-serif; font-size: 13px; line-height: 1.5; color: #6b7280; text-align: center;">
                                        © 2024 All rights reserved.
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """.format(
            full_name=rider_obj.full_name,
            booking_id=booking_obj.id,
            status_text=status_text,
            status_color=status_color,
            status_color_dark="#1A6B3A" if status_color == '#1E7F4A' else "#B91C1C" if status_color == '#DC2626' else "#D97706",
            status_message=self._get_status_message(booking_obj.booking_status.lower() if hasattr(booking_obj, 'booking_status') else 'pending')
        )
        self._email(subject, html)
    
    def booking_cancellation_email(self, booking_obj, rider_obj: Users, slug: str, cancellation_reason: str = None):
        """Send email notification when booking is cancelled"""
        subject = "Booking Cancelled"
        
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Booking Cancelled</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f5f5f5;">
                <tr>
                    <td align="center" style="padding: 48px 16px;">
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
                            <tr>
                                <td style="padding: 40px 40px 32px 40px; text-align: center; background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%); border-radius: 8px 8px 0 0;">
                                    <h1 style="margin: 0; font-family: 'DM Sans', sans-serif; font-size: 32px; font-weight: 600; color: #ffffff; line-height: 1.2;">
                                        Booking Cancelled
                                    </h1>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 40px 40px 32px 40px;">
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 18px; line-height: 1.6; color: #1f2937; font-weight: 500;">
                                        Hello {full_name},
                                    </p>
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        Your booking #{booking_id} has been cancelled.
                                    </p>
                                    {cancellation_reason_row}
                                    <p style="margin: 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        If you have any questions or would like to book a new ride, please don't hesitate to contact us.
                                    </p>
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                        <tr>
                                            <td align="center" style="padding: 24px 0 8px 0;">
                                                <a href="{base_url}/{slug}/rider/book" style="display: inline-block; padding: 14px 32px; background-color: #9B61D1; color: #ffffff; text-decoration: none; font-family: 'Work Sans', sans-serif; font-size: 16px; font-weight: 500; border-radius: 8px; text-align: center;">
                                                    Book New Ride
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 32px 40px; background-color: #f9fafb; border-top: 1px solid #e5e7eb; border-radius: 0 0 8px 8px;">
                                    <p style="margin: 0; font-family: 'Work Sans', sans-serif; font-size: 13px; line-height: 1.5; color: #6b7280; text-align: center;">
                                        © 2024 All rights reserved.
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """.format(
            full_name=rider_obj.full_name,
            booking_id=booking_obj.id,
            cancellation_reason_row='<p style="margin: 0 0 24px 0; font-family: \'Inter\', system-ui, -apple-system, \'Segoe UI\', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;"><strong>Reason:</strong> {}</p>'.format(cancellation_reason) if cancellation_reason else '',
            base_url=self.BASE_URL,
            slug=slug
        )
        self._email(subject, html)
    
    def _get_status_message(self, status: str):
        """Helper method to get status-specific message"""
        messages = {
            'confirmed': '<p style="margin: 24px 0; font-family: \'Inter\', system-ui, -apple-system, \'Segoe UI\', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">Your ride has been confirmed. Your driver will be arriving at the scheduled pickup time.</p>',
            'completed': '<p style="margin: 24px 0; font-family: \'Inter\', system-ui, -apple-system, \'Segoe UI\', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">Your ride has been completed. Thank you for choosing our service!</p>',
            'delayed': '<p style="margin: 24px 0; font-family: \'Inter\', system-ui, -apple-system, \'Segoe UI\', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">Your ride has been delayed. We apologize for the inconvenience and will keep you updated.</p>',
            'cancelled': '<p style="margin: 24px 0; font-family: \'Inter\', system-ui, -apple-system, \'Segoe UI\', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">Your booking has been cancelled. If you have any questions, please contact support.</p>'
        }
        return messages.get(status, '<p style="margin: 24px 0; font-family: \'Inter\', system-ui, -apple-system, \'Segoe UI\', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">Your booking status has been updated.</p>')
    
    def _email(self, subject, html):
        self.send_email(to_email=self.to_email, from_email=self.from_email,
                        subject=subject, html=html)