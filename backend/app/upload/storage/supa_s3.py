from supabase import create_client, Client
from app.config import Settings
from app.utils.logging import logger

settings = Settings()
url = settings.supabase_url
key = settings.supabase_anon_key
# resend = settings.resend_key
# logger.debug(resend)
try:
    supabase: Client =create_client(url, key)
  
    print('^_^ supabase connect successful')
except Exception as e:
    raise e
