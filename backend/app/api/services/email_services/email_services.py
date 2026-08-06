import resend
from app.config import Settings
# from app.config import Settings
settings = Settings()
class EmailServices:
    settings = Settings()
    resend.api_key =settings.resend_key
    
    BASE_URL = settings.base_url
    DOMAIN=settings.domain
    ENV=settings.environment


    # Verified Resend sending domain. Used in every env: Resend disables the
    # onboarding@resend.dev sandbox once an account has a verified domain.
    MAIL_DOMAIN = "usemaison.io"

    def _format_from(self, local_part: str, display_name: str, service: str = "bookings") -> str:
        """Build Resend From header: display name + local@MAIL_DOMAIN."""
        if "@" in local_part:
            local_part = f"{display_name.lower()}.{service}"
        local_part = local_part.strip().replace(" ", "-")
        return f"{display_name} <{local_part}@{self.MAIL_DOMAIN}>"

    def send_email(self,from_email,to_email, subject, html):
        
        params:resend.Emails.SendParams = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": html
        }
        resend.Emails.send(params)
# 
# params: resend.Emails.SendParams = {
#   "from": "Acme <onboarding@resend.dev>",
#   "to": ["delivered@resend.dev"],
#   "subject": "hello world",
#   "html": "<p>it works!</p>"
# }

# email = resend.Emails.send(params)
# print(email)


# class 
# tenants, drivers, admin, riders