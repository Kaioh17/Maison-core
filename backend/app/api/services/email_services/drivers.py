import resend
from app.config import Settings
from .email_services import EmailServices
from app.models.driver import Drivers
# from app.config import Settings

class DriverEmailServices(EmailServices):
    """
        Inherits the parentclass EmailServices with the set
        purpose: As the name implies, it will be used to send driver related emails for all tenants on our service.
        The from email used here should be tailored by the tenenats, 
        the content of the email can be tailored too if not there will be a default service that handles this.
    Args:
        EmailServices (_type_): _description_
    """
    def __init__(self, to_email, from_email):
        self.to_email = 'mubskill@gmail.com'
        self.from_email = 'Acme <onboarding@resend.dev>'
    # from_email = "Acme <onboarding@resend.dev>"
    def onboarding_email(self, token, slug):
        subject = "Welcome to Our Team - Complete Your Driver Registration"

        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Driver Registration - Verification Token</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f5f5f5;">
                <tr>
                    <td align="center" style="padding: 48px 16px;">
                        <!-- Email Container -->
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
                            <!-- Header -->
                            <tr>
                                <td style="padding: 40px 40px 32px 40px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                                    <h1 style="margin: 0; font-family: 'DM Sans', sans-serif; font-size: 28px; font-weight: 600; color: #1f2937; line-height: 1.2;">
                                        Welcome to Our Team!
                                    </h1>
                                </td>
                            </tr>
                            
                            <!-- Main Content -->
                            <tr>
                                <td style="padding: 32px 40px;">
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        Congratulations! You have been successfully registered as a driver with our platform.
                                    </p>
                                    
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        To complete your registration and access your driver dashboard, please use the verification token below:
                                    </p>
                                    
                                    <!-- Token Box -->
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: 24px 0; background-color: #f9fafb; border: 2px solid #9B61D1; border-radius: 8px;">
                                        <tr>
                                            <td style="padding: 20px; text-align: center;">
                                                <p style="margin: 0 0 8px 0; font-family: 'Work Sans', sans-serif; font-size: 13px; font-weight: 500; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">
                                                    Verification Token
                                                </p>
                                                <p style="margin: 0; font-family: 'DM Sans', sans-serif; font-size: 24px; font-weight: 600; color: #9B61D1; letter-spacing: 2px; word-break: break-all;">
                                                    {token}
                                                </p>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <p style="margin: 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        <strong style="color: #9B61D1;">Important:</strong> This token is valid for the next 24 hours. Please complete your registration before it expires.
                                    </p>
                                    
                                    <!-- CTA Button -->
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                        <tr>
                                            <td align="center" style="padding: 24px 0 8px 0;">
                                                <a href="{BASE_URL}/{slug}/driver/verify" style="display: inline-block; padding: 14px 32px; background-color: #9B61D1; color: #ffffff; text-decoration: none; font-family: 'Work Sans', sans-serif; font-size: 16px; font-weight: 500; border-radius: 8px; text-align: center;">
                                                    Complete Registration
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <p style="margin: 16px 0 0 0; font-family: 'Work Sans', sans-serif; font-size: 13px; line-height: 1.5; color: #6b7280; text-align: center;">
                                        Or copy and paste this link into your browser:<br>
                                        <a href="{BASE_URL}/{slug}/driver/verify" style="color: #9B61D1; text-decoration: underline; word-break: break-all;">
                                            {BASE_URL}/{slug}/driver/verify
                                        </a>
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="padding: 32px 40px; background-color: #f9fafb; border-top: 1px solid #e5e7eb; border-radius: 0 0 8px 8px;">
                                    <p style="margin: 0 0 8px 0; font-family: 'Work Sans', sans-serif; font-size: 13px; line-height: 1.5; color: #6b7280; text-align: center;">
                                        If you did not request this registration, please ignore this email.
                                    </p>
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
        """.format(token=token, BASE_URL=self.BASE_URL, slug=slug)

        self._email(subject, html)
        
    def welcome_(self, obj: Drivers):
        subject = "You have been successfully registered"

        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to Our Team</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f5f5f5;">
                <tr>
                    <td align="center" style="padding: 48px 16px;">
                        <!-- Email Container -->
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
                            <!-- Header with Accent Color -->
                            <tr>
                                <td style="padding: 40px 40px 32px 40px; text-align: center; background: linear-gradient(135deg, #9B61D1 0%, #8750BD 100%); border-radius: 8px 8px 0 0;">
                                    <h1 style="margin: 0; font-family: 'DM Sans', sans-serif; font-size: 32px; font-weight: 600; color: #ffffff; line-height: 1.2;">
                                        Welcome to Our Team!
                                    </h1>
                                </td>
                            </tr>
                            
                            <!-- Main Content -->
                            <tr>
                                <td style="padding: 40px 40px 32px 40px;">
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 18px; line-height: 1.6; color: #1f2937; font-weight: 500;">
                                        Welcome {full_name}!
                                    </p>
                                    
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        Congratulations! Your driver account has been successfully registered with our platform. We're excited to have you join our team of professional drivers.
                                    </p>
                                    
                                    <!-- Account Information Card -->
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: 32px 0; background-color: #f9fafb; border-left: 4px solid #9B61D1; border-radius: 4px;">
                                        <tr>
                                            <td style="padding: 20px 24px;">
                                                <p style="margin: 0 0 12px 0; font-family: 'Work Sans', sans-serif; font-size: 13px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">
                                                    Your Account Details
                                                </p>
                                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                                    <tr>
                                                        <td style="padding: 4px 0;">
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Name:</span>
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{full_name}</span>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding: 4px 0;">
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Email:</span>
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{email}</span>
                                                        </td>
                                                    </tr>
                                                    {phone_row}
                                                    <tr>
                                                        <td style="padding: 4px 0;">
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Driver Type:</span>
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px; text-transform: capitalize;">{driver_type}</span>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding: 4px 0;">
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Status:</span>
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #1E7F4A; margin-left: 8px; font-weight: 500; text-transform: capitalize;">{is_registered}</span>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <p style="margin: 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        Your account is currently in <strong style="color: #9B61D1;">{is_registered}</strong> status. Once your registration is fully processed, you'll be able to start accepting rides and managing your driver profile.
                                    </p>
                                    
                                    <!-- Next Steps Section -->
                                    <div style="margin: 32px 0; padding: 24px; background-color: #f9fafb; border-radius: 8px;">
                                        <h3 style="margin: 0 0 16px 0; font-family: 'DM Sans', sans-serif; font-size: 20px; font-weight: 600; color: #1f2937;">
                                            What's Next?
                                        </h3>
                                        <ul style="margin: 0; padding-left: 20px; font-family: 'Work Sans', sans-serif; font-size: 15px; line-height: 1.8; color: #1f2937;">
                                            <li style="margin-bottom: 8px;">Complete your driver profile with additional information</li>
                                            <li style="margin-bottom: 8px;">Set up your vehicle information (if applicable)</li>
                                            <li style="margin-bottom: 8px;">Review and accept our driver terms and conditions</li>
                                            <li style="margin-bottom: 8px;">Wait for account activation confirmation</li>
                                        </ul>
                                    </div>
                                    
                                    <!-- CTA Button -->
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                        <tr>
                                            <td align="center" style="padding: 24px 0 8px 0;">
                                                <a href="{base_url}/{slug}/driver/login" style="display: inline-block; padding: 14px 32px; background-color: #9B61D1; color: #ffffff; text-decoration: none; font-family: 'Work Sans', sans-serif; font-size: 16px; font-weight: 500; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(155, 97, 209, 0.3);">
                                                    Sign In to Your Account
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <p style="margin: 16px 0 0 0; font-family: 'Work Sans', sans-serif; font-size: 13px; line-height: 1.5; color: #6b7280; text-align: center;">
                                        Or copy and paste this link into your browser:<br>
                                        <a href="{base_url}/{slug}/driver/login" style="color: #9B61D1; text-decoration: underline; word-break: break-all;">
                                            {base_url}/{slug}/driver/login
                                        </a>
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="padding: 32px 40px; background-color: #f9fafb; border-top: 1px solid #e5e7eb; border-radius: 0 0 8px 8px;">
                                    <p style="margin: 0 0 12px 0; font-family: 'Work Sans', sans-serif; font-size: 13px; line-height: 1.5; color: #6b7280; text-align: center;">
                                        If you have any questions or need assistance, please don't hesitate to contact our support team.
                                    </p>
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
            email=obj.email,
            phone_row='<tr><td style="padding: 4px 0;"><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Phone:</span><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{}</span></td></tr>'.format(obj.phone_no) if obj.phone_no else '',
            driver_type=obj.driver_type.replace('_', ' ').title(),
            is_registered=obj.is_registered.title(),
            base_url=self.BASE_URL,
            slug=obj.slug
        )
        self._email(subject, html)
   
    def new_ride(self,booking_obj:object ,assigned:bool = False):
        if not assigned:
            subject = "You  Have a new ride"
            html = f"<p> Are you ready to take on this ride </p>"
            self._email(subject, html)
        else:
            subject = "You  Have a been assigned a ride"
            html = f"<p> You have been assigned a ride {booking_obj} </p>"
            self._email(subject, html)
    def _email(self, subject, html):
        self.send_email(to_email=self.to_email, from_email=self.from_email,
                        subject=subject, html=html) 
    