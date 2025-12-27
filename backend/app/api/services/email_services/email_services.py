import resend
from app.config import Settings

class EmailServices:
    settings = Settings()
    resend.api_key =settings.resend_key
    BASE_URL = settings.base_url
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