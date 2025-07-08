from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_url: str
    db_name: str
    db_user: str
    db_password: str
    db_host: str = "db" 
    db_port: int = 5432

    class Config:
        env_file = "backend/.env"