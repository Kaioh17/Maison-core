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
   
    def new_ride(self, booking_obj: object, assigned: bool = False, slug: str = None):
        """Send email notification to driver about a new ride or assigned ride"""
        if not assigned:
            subject = "New Ride Available - Action Required"
        else:
            subject = "You Have Been Assigned a Ride"
        
        pickup_time = booking_obj.pickup_time.strftime("%B %d, %Y at %I:%M %p") if hasattr(booking_obj.pickup_time, 'strftime') else str(booking_obj.pickup_time)
        dropoff_time = booking_obj.dropoff_time.strftime("%B %d, %Y at %I:%M %p") if hasattr(booking_obj, 'dropoff_time') and booking_obj.dropoff_time and hasattr(booking_obj.dropoff_time, 'strftime') else None
        estimated_price = f"${booking_obj.estimated_price:.2f}" if hasattr(booking_obj, 'estimated_price') and booking_obj.estimated_price else "TBD"
        service_type = booking_obj.service_type.title() if hasattr(booking_obj, 'service_type') else "Standard"
        payment_method = booking_obj.payment_method.title() if hasattr(booking_obj, 'payment_method') and booking_obj.payment_method else "Not specified"
        notes = booking_obj.notes if hasattr(booking_obj, 'notes') and booking_obj.notes else "No special notes"
        
        header_text = "New Ride Available" if not assigned else "Ride Assigned"
        header_color = "#F59E0B" if not assigned else "#1E7F4A"
        header_color_dark = "#D97706" if not assigned else "#1A6B3A"
        message_text = "A new ride has been posted and is available for you to accept." if not assigned else "You have been assigned to this ride. Please review the details below."
        cta_text = "View Ride Details" if not assigned else "View Booking Details"
        cta_url_suffix = "/driver/bookings" if not assigned else "/driver/bookings"
        
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{header_text}</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f5f5f5;">
                <tr>
                    <td align="center" style="padding: 48px 16px;">
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
                            <tr>
                                <td style="padding: 40px 40px 32px 40px; text-align: center; background: linear-gradient(135deg, {header_color} 0%, {header_color_dark} 100%); border-radius: 8px 8px 0 0;">
                                    <h1 style="margin: 0; font-family: 'DM Sans', sans-serif; font-size: 32px; font-weight: 600; color: #ffffff; line-height: 1.2;">
                                        {header_text}
                                    </h1>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 40px 40px 32px 40px;">
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 18px; line-height: 1.6; color: #1f2937; font-weight: 500;">
                                        Hello Driver,
                                    </p>
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        {message_text}
                                    </p>
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: 32px 0; background-color: #f9fafb; border-left: 4px solid {header_color}; border-radius: 4px;">
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
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Service Type:</span>
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{service_type}</span>
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
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px; font-weight: 600;">{pickup_time}</span>
                                                        </td>
                                                    </tr>
                                                    {dropoff_time_row}
                                                    {city_row}
                                                    <tr>
                                                        <td style="padding: 4px 0;">
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Estimated Price:</span>
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px; font-weight: 600;">{estimated_price}</span>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding: 4px 0;">
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Payment Method:</span>
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{payment_method}</span>
                                                        </td>
                                                    </tr>
                                                    {notes_row}
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                    {action_message}
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                        <tr>
                                            <td align="center" style="padding: 24px 0 8px 0;">
                                                <a href="{base_url}/{slug}{cta_url_suffix}" style="display: inline-block; padding: 14px 32px; background-color: {header_color}; color: #ffffff; text-decoration: none; font-family: 'Work Sans', sans-serif; font-size: 16px; font-weight: 500; border-radius: 8px; text-align: center;">
                                                    {cta_text}
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
            header_text=header_text,
            header_color=header_color,
            header_color_dark=header_color_dark,
            message_text=message_text,
            booking_id=booking_obj.id,
            service_type=service_type,
            pickup_location=booking_obj.pickup_location,
            dropoff_row='<tr><td style="padding: 4px 0;"><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Dropoff Location:</span><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{}</span></td></tr>'.format(booking_obj.dropoff_location) if hasattr(booking_obj, 'dropoff_location') and booking_obj.dropoff_location else '',
            pickup_time=pickup_time,
            dropoff_time_row='<tr><td style="padding: 4px 0;"><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Dropoff Time:</span><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{}</span></td></tr>'.format(dropoff_time) if dropoff_time else '',
            city_row='<tr><td style="padding: 4px 0;"><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">City:</span><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{}</span></td></tr>'.format(booking_obj.city) if hasattr(booking_obj, 'city') and booking_obj.city else '',
            estimated_price=estimated_price,
            payment_method=payment_method,
            notes_row='<tr><td style="padding: 4px 0;"><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Notes:</span><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{}</span></td></tr>'.format(notes) if notes and notes != "No special notes" else '',
            action_message='<p style="margin: 24px 0; font-family: \'Inter\', system-ui, -apple-system, \'Segoe UI\', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">Please review the ride details and confirm if you can accept this booking.</p>' if not assigned else '<p style="margin: 24px 0; font-family: \'Inter\', system-ui, -apple-system, \'Segoe UI\', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">Please ensure you arrive at the pickup location on time and provide excellent service.</p>',
            cta_text=cta_text,
            cta_url_suffix=cta_url_suffix,
            base_url=self.BASE_URL,
            slug=slug if slug else 'default'
        )
        self._email(subject, html)
    
    def status_change_email(self, obj: Drivers, is_active: bool):
        """Send email notification when driver status changes (active/inactive)"""
        status_text = "activated" if is_active else "deactivated"
        status_color = "#1E7F4A" if is_active else "#DC2626"
        
        subject = f"Driver Account {status_text.title()}"
        
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Driver Status Update</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f5f5f5;">
                <tr>
                    <td align="center" style="padding: 48px 16px;">
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
                            <tr>
                                <td style="padding: 40px 40px 32px 40px; text-align: center; background: linear-gradient(135deg, {status_color} 0%, {status_color_dark} 100%); border-radius: 8px 8px 0 0;">
                                    <h1 style="margin: 0; font-family: 'DM Sans', sans-serif; font-size: 32px; font-weight: 600; color: #ffffff; line-height: 1.2;">
                                        Account {status_text.title()}
                                    </h1>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 40px 40px 32px 40px;">
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 18px; line-height: 1.6; color: #1f2937; font-weight: 500;">
                                        Hello {full_name},
                                    </p>
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        Your driver account has been <strong style="color: {status_color};">{status_text}</strong> by the administrator.
                                    </p>
                                    {status_message}
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                        <tr>
                                            <td align="center" style="padding: 24px 0 8px 0;">
                                                <a href="{base_url}/{slug}/driver/login" style="display: inline-block; padding: 14px 32px; background-color: {status_color}; color: #ffffff; text-decoration: none; font-family: 'Work Sans', sans-serif; font-size: 16px; font-weight: 500; border-radius: 8px; text-align: center;">
                                                    {button_text}
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                    <p style="margin: 16px 0 0 0; font-family: 'Work Sans', sans-serif; font-size: 13px; line-height: 1.5; color: #6b7280; text-align: center;">
                                        If you have any questions, please contact support.
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
            full_name=obj.full_name,
            status_text=status_text,
            status_color=status_color,
            status_color_dark="#1A6B3A" if is_active else "#B91C1C",
            status_message='<p style="margin: 24px 0; font-family: \'Inter\', system-ui, -apple-system, \'Segoe UI\', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">You can now accept rides and manage your bookings through the driver dashboard.</p>' if is_active else '<p style="margin: 24px 0; font-family: \'Inter\', system-ui, -apple-system, \'Segoe UI\', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">Your account is currently inactive. Please contact support if you believe this is an error.</p>',
            button_text="Access Dashboard" if is_active else "Contact Support",
            base_url=self.BASE_URL,
            slug=obj.slug
        )
        self._email(subject, html)
    
    def vehicle_assignment_email(self, obj: Drivers, vehicle_obj):
        """Send email notification when a vehicle is assigned to a driver"""
        subject = "Vehicle Assignment Notification"
        
        vehicle_name = f"{vehicle_obj.make} {vehicle_obj.model} {vehicle_obj.year}" if vehicle_obj.year else f"{vehicle_obj.make} {vehicle_obj.model}"
        
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Vehicle Assignment</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f5f5f5;">
                <tr>
                    <td align="center" style="padding: 48px 16px;">
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
                            <tr>
                                <td style="padding: 40px 40px 32px 40px; text-align: center; background: linear-gradient(135deg, #9B61D1 0%, #8750BD 100%); border-radius: 8px 8px 0 0;">
                                    <h1 style="margin: 0; font-family: 'DM Sans', sans-serif; font-size: 32px; font-weight: 600; color: #ffffff; line-height: 1.2;">
                                        Vehicle Assigned
                                    </h1>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 40px 40px 32px 40px;">
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 18px; line-height: 1.6; color: #1f2937; font-weight: 500;">
                                        Hello {full_name},
                                    </p>
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        A vehicle has been assigned to your driver account.
                                    </p>
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: 32px 0; background-color: #f9fafb; border-left: 4px solid #9B61D1; border-radius: 4px;">
                                        <tr>
                                            <td style="padding: 20px 24px;">
                                                <p style="margin: 0 0 12px 0; font-family: 'Work Sans', sans-serif; font-size: 13px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">
                                                    Vehicle Details
                                                </p>
                                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                                    <tr>
                                                        <td style="padding: 4px 0;">
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Vehicle:</span>
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{vehicle_name}</span>
                                                        </td>
                                                    </tr>
                                                    {license_plate_row}
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                    <p style="margin: 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        You can now use this vehicle for your bookings. Make sure to keep the vehicle in good condition and follow all safety guidelines.
                                    </p>
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                        <tr>
                                            <td align="center" style="padding: 24px 0 8px 0;">
                                                <a href="{base_url}/{slug}/driver/login" style="display: inline-block; padding: 14px 32px; background-color: #9B61D1; color: #ffffff; text-decoration: none; font-family: 'Work Sans', sans-serif; font-size: 16px; font-weight: 500; border-radius: 8px; text-align: center;">
                                                    View Vehicle Details
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
            vehicle_name=vehicle_name,
            license_plate_row='<tr><td style="padding: 4px 0;"><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">License Plate:</span><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{}</span></td></tr>'.format(vehicle_obj.license_plate) if hasattr(vehicle_obj, 'license_plate') and vehicle_obj.license_plate else '',
            base_url=self.BASE_URL,
            slug=obj.slug
        )
        self._email(subject, html)
    
    def vehicle_unassignment_email(self, obj: Drivers, vehicle_obj):
        """Send email notification when a vehicle is unassigned from a driver"""
        subject = "Vehicle Unassignment Notification"
        
        vehicle_name = f"{vehicle_obj.vehicle_name}" if vehicle_obj.year else f"{vehicle_obj.make} {vehicle_obj.model}"
        
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Vehicle Unassignment</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f5f5f5;">
                <tr>
                    <td align="center" style="padding: 48px 16px;">
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
                            <tr>
                                <td style="padding: 40px 40px 32px 40px; text-align: center; background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%); border-radius: 8px 8px 0 0;">
                                    <h1 style="margin: 0; font-family: 'DM Sans', sans-serif; font-size: 32px; font-weight: 600; color: #ffffff; line-height: 1.2;">
                                        Vehicle Unassigned
                                    </h1>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 40px 40px 32px 40px;">
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 18px; line-height: 1.6; color: #1f2937; font-weight: 500;">
                                        Hello {full_name},
                                    </p>
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        You have been unassigned from the vehicle that was previously assigned to your driver account.
                                    </p>
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: 32px 0; background-color: #f9fafb; border-left: 4px solid #DC2626; border-radius: 4px;">
                                        <tr>
                                            <td style="padding: 20px 24px;">
                                                <p style="margin: 0 0 12px 0; font-family: 'Work Sans', sans-serif; font-size: 13px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">
                                                    Vehicle Details
                                                </p>
                                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                                    <tr>
                                                        <td style="padding: 4px 0;">
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Vehicle:</span>
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{vehicle_name}</span>
                                                        </td>
                                                    </tr>
                                                    {license_plate_row}
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                    <p style="margin: 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        You will no longer be able to use this vehicle for bookings. If you have any questions about this change or need assistance, please contact your administrator.
                                    </p>
                                    <p style="margin: 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        If you believe this is an error, please reach out to support immediately.
                                    </p>
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                        <tr>
                                            <td align="center" style="padding: 24px 0 8px 0;">
                                                <a href="{base_url}/{slug}/driver/login" style="display: inline-block; padding: 14px 32px; background-color: #DC2626; color: #ffffff; text-decoration: none; font-family: 'Work Sans', sans-serif; font-size: 16px; font-weight: 500; border-radius: 8px; text-align: center;">
                                                    Contact Support
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
            vehicle_name=vehicle_name,
            license_plate_row='<tr><td style="padding: 4px 0;"><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">License Plate:</span><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{}</span></td></tr>'.format(vehicle_obj.license_plate) if hasattr(vehicle_obj, 'license_plate') and vehicle_obj.license_plate else '',
            base_url=self.BASE_URL,
            slug=obj.slug
        )
        self._email(subject, html)
    
    def _email(self, subject, html):
        self.send_email(to_email=self.to_email, from_email=self.from_email,
                        subject=subject, html=html) 
    