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

    def _format_from(self, local_part: str, display_name: str) -> str:
        """Build Resend From header: dev uses Resend sandbox; prod uses display name + local@DOMAIN."""
        if self.ENV == "development":
            return "Acme <onboarding@resend.dev>"
        return f"{display_name} <{local_part}@{self.DOMAIN}>"

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