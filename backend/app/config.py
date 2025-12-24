from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_url: str
    db_name: str
    db_user: str
    db_password: str
    db_host: str = "db"
    db_port: int = 5432
    redis_url: str 
    host: str
    redis_port: int
    secret_key: str 
    algorithm: str 
    access_token_expire_minutes: int
    pk_test: str
    sk_test: str
    resend_key:str
    supabase_anon_key: str
    supabase_url: str
    class Config:
        # env_file = "/backend/docker/.env"
        env_file ="/backend/app/.env"