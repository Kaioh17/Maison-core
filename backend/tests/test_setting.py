from pydantic import AliasChoices, Field
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
	stripe_public_key: str = Field(default="test_pk", validation_alias=AliasChoices("stripe_public_key", "pk_test"))
	stripe_secret_key: str = Field(default="test_sk", validation_alias=AliasChoices("stripe_secret_key", "sk_test"))

	class Config:
		env_file = ".env.test"
