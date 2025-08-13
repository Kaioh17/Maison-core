from pydantic import Field
from pydantic_settings import BaseSettings	


class Settings(BaseSettings):
	db_url: str 
	db_name: str = "test"
	db_user: str = "test"
	db_password: str = "test"
	db_host: str = "localhost"
	db_port: int = 5432
	redis_url: str = "redis://localhost:6379"
	host: str = "localhost"
	redis_port: int = 6379
	secret_key: str = "test_secret_key_for_testing_only"
	algorithm: str = "HS256"
	access_token_expire_minutes: int = 30
	pk_test: str = "test_pk"
	sk_test: str = "test_sk"

	class Config:
		env_file = ".env.test"
