import resend
from app.config import Settings
from .email_services import EmailServices

class DriverEmailServices(EmailServices):
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
    def onboarding_email(self, token):
        subject = "You have been successfully registered"
        html = f"<p> Enter this token {token} in the next 24hrs </p>"
        self._email(subject, html)
        
    def welcome_(self, name):
        
        params:resend.Emails.SendParams = {
        "from": self.from_email,
        "to": [self.to_email],
        "subject": "You have been successfully registered",
        "html": f"<p>Welcome {name}</p>"
        }
        resend.Emails.send(params)
   
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
    