import resend
from app.config import Settings
from .email_services import EmailServices

class RiderEmailServices(EmailServices):
    """
        Inherits the parentclas EmailServices with the set
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
    def onboarding_email(self):
        
        params:resend.Emails.SendParams = {
        "from": self.from_email,
        "to": [self.to_email],
        "subject": "You have been successfully registered",
        "html": f"<p>Enter this </p>"
        }
        resend.Emails.send(params)