from pydantic import AliasChoices, Field
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
    refresh_token_expire_days: int
    
    stripe_public_key: str = Field(validation_alias=AliasChoices("stripe_public_key", "pk_test"))
    stripe_secret_key: str = Field(validation_alias=AliasChoices("stripe_secret_key", "sk_test"))
    resend_key:str
    supabase_anon_key: str
    supabase_url: str
    base_url: str
    api_url: str
    webhook_secret: str
    environment: str
    connect_webhook_secret:str
    mapbox_api: str
    api_key: str
    cors_origins: str
    domain: str
    class Config:
        # env_file = "/backend/docker/.env"
        env_file ="/backend/app/.env"