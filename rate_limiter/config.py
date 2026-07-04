from pydantic_settings import BaseSettings

class Settings(BaseSettings):
  redis_url : str = "redis://localhost:6379"
  max_tokens : int = 10
  refill_rate : int = 2
  interval : float = 60.0
  key_ttl : int = 3600

  model_config = {"env_file": ".env", "env_file_encoding" : "utf-8"}

settings = Settings()