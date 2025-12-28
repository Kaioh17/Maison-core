import resend
from app.config import Settings
from .email_services import EmailServices
from app.models.tenant import Tenants

class TenantEmailServices(EmailServices):
    """
        Inherits the parentclass EmailServices with the set
        purpose: As the name implies, it will be used to send tenant related emails for all tenants on our service.
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
    
    def welcome_email(self, obj: Tenants, slug: str):
        """Send welcome email to tenant after account creation"""
        subject = "Welcome to Our Platform!"
        
        company_name = obj.profile.company_name if hasattr(obj, 'profile') and obj.profile else "Your Company"
        
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
                                        Welcome to Our Platform!
                                    </h1>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 40px 40px 32px 40px;">
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 18px; line-height: 1.6; color: #1f2937; font-weight: 500;">
                                        Hello {full_name},
                                    </p>
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        Congratulations! Your account for <strong>{company_name}</strong> has been successfully created.
                                    </p>
                                    <p style="margin: 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        You can now start managing your drivers, vehicles, and bookings through your tenant dashboard.
                                    </p>
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                        <tr>
                                            <td align="center" style="padding: 24px 0 8px 0;">
                                                <a href="{base_url}/{slug}/tenant/login" style="display: inline-block; padding: 14px 32px; background-color: #9B61D1; color: #ffffff; text-decoration: none; font-family: 'Work Sans', sans-serif; font-size: 16px; font-weight: 500; border-radius: 8px; text-align: center;">
                                                    Access Dashboard
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
            company_name=company_name,
            base_url=self.BASE_URL,
            slug=slug
        )
        self._email(subject, html)
    
    async def booking_notification_email(self, booking_obj, tenant_obj: Tenants, slug: str, rider_name: str = None, vehicle_info: str = None):
        """Send email notification to tenant when a new booking is created"""
        subject = "New Booking Received"
        
        pickup_time = booking_obj.pickup_time.strftime("%B %d, %Y at %I:%M %p") if hasattr(booking_obj.pickup_time, 'strftime') else str(booking_obj.pickup_time)
        estimated_price = f"${booking_obj.estimated_price:.2f}" if hasattr(booking_obj, 'estimated_price') and booking_obj.estimated_price else "TBD"
        
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>New Booking</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f5f5f5;">
                <tr>
                    <td align="center" style="padding: 48px 16px;">
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
                            <tr>
                                <td style="padding: 40px 40px 32px 40px; text-align: center; background: linear-gradient(135deg, #9B61D1 0%, #8750BD 100%); border-radius: 8px 8px 0 0;">
                                    <h1 style="margin: 0; font-family: 'DM Sans', sans-serif; font-size: 32px; font-weight: 600; color: #ffffff; line-height: 1.2;">
                                        New Booking Received
                                    </h1>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 40px 40px 32px 40px;">
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 18px; line-height: 1.6; color: #1f2937; font-weight: 500;">
                                        Hello {full_name},
                                    </p>
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        You have received a new booking request. Here are the details:
                                    </p>
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: 32px 0; background-color: #f9fafb; border-left: 4px solid #9B61D1; border-radius: 4px;">
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
                                                    {rider_row}
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
                                        Please review and manage this booking through your dashboard.
                                    </p>
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                        <tr>
                                            <td align="center" style="padding: 24px 0 8px 0;">
                                                <a href="{base_url}/{slug}/tenant/bookings" style="display: inline-block; padding: 14px 32px; background-color: #9B61D1; color: #ffffff; text-decoration: none; font-family: 'Work Sans', sans-serif; font-size: 16px; font-weight: 500; border-radius: 8px; text-align: center;">
                                                    View Booking
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
            full_name=tenant_obj.full_name,
            booking_id=booking_obj.id,
            rider_row='<tr><td style="padding: 4px 0;"><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Rider:</span><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{}</span></td></tr>'.format(rider_name) if rider_name else '',
            pickup_location=booking_obj.pickup_location,
            dropoff_row='<tr><td style="padding: 4px 0;"><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Dropoff Location:</span><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{}</span></td></tr>'.format(booking_obj.dropoff_location) if hasattr(booking_obj, 'dropoff_location') and booking_obj.dropoff_location else '',
            pickup_time=pickup_time,
            vehicle_row='<tr><td style="padding: 4px 0;"><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Vehicle:</span><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{}</span></td></tr>'.format(vehicle_info) if vehicle_info else '',
            estimated_price=estimated_price,
            base_url=self.BASE_URL,
            slug=slug
        )
        self._email(subject, html)
    
    def settings_change_email(self, tenant_obj: Tenants, slug: str, changed_settings: dict = None):
        """Send email notification when critical tenant settings are changed"""
        subject = "Settings Updated"
        
        settings_list = ""
        if changed_settings:
            for key, value in changed_settings.items():
                settings_list += f"<li style='margin-bottom: 8px;'><strong>{key.replace('_', ' ').title()}:</strong> {value}</li>"
        
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Settings Updated</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f5f5f5;">
                <tr>
                    <td align="center" style="padding: 48px 16px;">
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
                            <tr>
                                <td style="padding: 40px 40px 32px 40px; text-align: center; background: linear-gradient(135deg, #9B61D1 0%, #8750BD 100%); border-radius: 8px 8px 0 0;">
                                    <h1 style="margin: 0; font-family: 'DM Sans', sans-serif; font-size: 32px; font-weight: 600; color: #ffffff; line-height: 1.2;">
                                        Settings Updated
                                    </h1>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 40px 40px 32px 40px;">
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 18px; line-height: 1.6; color: #1f2937; font-weight: 500;">
                                        Hello {full_name},
                                    </p>
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        Your tenant settings have been successfully updated.
                                    </p>
                                    {settings_list}
                                    <p style="margin: 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        If you did not make these changes, please contact support immediately.
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
            full_name=tenant_obj.full_name,
            settings_list='<ul style="margin: 24px 0; padding-left: 20px; font-family: \'Work Sans\', sans-serif; font-size: 15px; line-height: 1.8; color: #1f2937;">{}</ul>'.format(settings_list) if settings_list else '<p style="margin: 24px 0; font-family: \'Inter\', system-ui, -apple-system, \'Segoe UI\', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">Your settings have been updated successfully.</p>'
        )
        self._email(subject, html)
    
    def logo_update_confirmation_email(self, tenant_obj: Tenants, slug: str, logo_url: str = None):
        """Send email confirmation when tenant logo is updated"""
        subject = "Logo Updated Successfully"
        
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Logo Updated</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f5f5f5;">
                <tr>
                    <td align="center" style="padding: 48px 16px;">
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
                            <tr>
                                <td style="padding: 40px 40px 32px 40px; text-align: center; background: linear-gradient(135deg, #9B61D1 0%, #8750BD 100%); border-radius: 8px 8px 0 0;">
                                    <h1 style="margin: 0; font-family: 'DM Sans', sans-serif; font-size: 32px; font-weight: 600; color: #ffffff; line-height: 1.2;">
                                        Logo Updated
                                    </h1>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 40px 40px 32px 40px;">
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 18px; line-height: 1.6; color: #1f2937; font-weight: 500;">
                                        Hello {full_name},
                                    </p>
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        Your company logo has been successfully updated.
                                    </p>
                                    {logo_image}
                                    <p style="margin: 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        The new logo will be displayed across your tenant dashboard and customer-facing interfaces.
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
            full_name=tenant_obj.full_name,
            logo_image='<div style="text-align: center; margin: 24px 0;"><img src="{}" alt="Company Logo" style="max-width: 200px; height: auto; border-radius: 8px;"></div>'.format(logo_url) if logo_url else ''
        )
        self._email(subject, html)
    
    def _email(self, subject, html):
        self.send_email(to_email=self.to_email, from_email=self.from_email,
                        subject=subject, html=html)