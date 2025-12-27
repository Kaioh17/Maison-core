import resend
from app.config import Settings
from .email_services import EmailServices
from app.models.tenant import Tenants

class AdminEmailServices(EmailServices):
    """
        Inherits the parentclass EmailServices with the set
        purpose: As the name implies, it will be used to send admin related emails for all tenants on our service.
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
    
    def notify_new_tenant(self, tenant_obj: Tenants):
        """Notify admin when a new tenant is registered"""
        self.new_tenant_notification_email(tenant_obj)
    
    def new_tenant_notification_email(self, tenant_obj: Tenants):
        """Send email notification to admin when a new tenant registers"""
        subject = "New Tenant Registration"
        
        company_name = tenant_obj.profile.company_name if hasattr(tenant_obj, 'profile') and tenant_obj.profile else "N/A"
        slug = tenant_obj.slug if hasattr(tenant_obj, 'slug') else "N/A"
        created_date = tenant_obj.created_on.strftime("%B %d, %Y at %I:%M %p") if hasattr(tenant_obj.created_on, 'strftime') else str(tenant_obj.created_on)
        
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>New Tenant Registration</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f5f5f5;">
                <tr>
                    <td align="center" style="padding: 48px 16px;">
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
                            <tr>
                                <td style="padding: 40px 40px 32px 40px; text-align: center; background: linear-gradient(135deg, #9B61D1 0%, #8750BD 100%); border-radius: 8px 8px 0 0;">
                                    <h1 style="margin: 0; font-family: 'DM Sans', sans-serif; font-size: 32px; font-weight: 600; color: #ffffff; line-height: 1.2;">
                                        New Tenant Registered
                                    </h1>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 40px 40px 32px 40px;">
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 18px; line-height: 1.6; color: #1f2937; font-weight: 500;">
                                        New Tenant Registration
                                    </p>
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        A new tenant has been registered on the platform. Here are the details:
                                    </p>
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: 32px 0; background-color: #f9fafb; border-left: 4px solid #9B61D1; border-radius: 4px;">
                                        <tr>
                                            <td style="padding: 20px 24px;">
                                                <p style="margin: 0 0 12px 0; font-family: 'Work Sans', sans-serif; font-size: 13px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">
                                                    Tenant Information
                                                </p>
                                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                                    <tr>
                                                        <td style="padding: 4px 0;">
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Tenant ID:</span>
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">#{tenant_id}</span>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding: 4px 0;">
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Company Name:</span>
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{company_name}</span>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding: 4px 0;">
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Contact Name:</span>
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{full_name}</span>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding: 4px 0;">
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Email:</span>
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{email}</span>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding: 4px 0;">
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Slug:</span>
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{slug}</span>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding: 4px 0;">
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Registered On:</span>
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{created_date}</span>
                                                        </td>
                                                    </tr>
                                                    {phone_row}
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                    <p style="margin: 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        Please review the tenant account and verify their information as needed.
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
            tenant_id=tenant_obj.id,
            company_name=company_name,
            full_name=tenant_obj.full_name,
            email=tenant_obj.email,
            slug=slug,
            created_date=created_date,
            phone_row='<tr><td style="padding: 4px 0;"><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Phone:</span><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{}</span></td></tr>'.format(tenant_obj.phone_no) if hasattr(tenant_obj, 'phone_no') and tenant_obj.phone_no else ''
        )
        self._email(subject, html)
    
    def tenant_deletion_confirmation_email(self, tenant_id: int, company_name: str = None, deleted_by: str = None):
        """Send email confirmation to admin when a tenant is deleted"""
        subject = "Tenant Account Deleted"
        
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Tenant Deleted</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f5f5f5;">
                <tr>
                    <td align="center" style="padding: 48px 16px;">
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
                            <tr>
                                <td style="padding: 40px 40px 32px 40px; text-align: center; background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%); border-radius: 8px 8px 0 0;">
                                    <h1 style="margin: 0; font-family: 'DM Sans', sans-serif; font-size: 32px; font-weight: 600; color: #ffffff; line-height: 1.2;">
                                        Tenant Account Deleted
                                    </h1>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 40px 40px 32px 40px;">
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 18px; line-height: 1.6; color: #1f2937; font-weight: 500;">
                                        Tenant Deletion Confirmation
                                    </p>
                                    <p style="margin: 0 0 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        A tenant account has been deleted from the platform.
                                    </p>
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: 32px 0; background-color: #f9fafb; border-left: 4px solid #DC2626; border-radius: 4px;">
                                        <tr>
                                            <td style="padding: 20px 24px;">
                                                <p style="margin: 0 0 12px 0; font-family: 'Work Sans', sans-serif; font-size: 13px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">
                                                    Deletion Details
                                                </p>
                                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                                    <tr>
                                                        <td style="padding: 4px 0;">
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Tenant ID:</span>
                                                            <span style="font-family: 'Work Sans', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">#{tenant_id}</span>
                                                        </td>
                                                    </tr>
                                                    {company_row}
                                                    {deleted_by_row}
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                    <p style="margin: 24px 0; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #1f2937;">
                                        All associated data including drivers, vehicles, and bookings have been removed from the system.
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
            tenant_id=tenant_id,
            company_row='<tr><td style="padding: 4px 0;"><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Company Name:</span><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{}</span></td></tr>'.format(company_name) if company_name else '',
            deleted_by_row='<tr><td style="padding: 4px 0;"><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #6b7280; font-weight: 500;">Deleted By:</span><span style="font-family: \'Work Sans\', sans-serif; font-size: 14px; color: #1f2937; margin-left: 8px;">{}</span></td></tr>'.format(deleted_by) if deleted_by else ''
        )
        self._email(subject, html)
    
    def _email(self, subject, html):
        self.send_email(to_email=self.to_email, from_email=self.from_email,
                        subject=subject, html=html)