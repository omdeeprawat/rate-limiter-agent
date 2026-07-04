from pydantic_settings import BaseSettings, SettingsConfigDict

class AgentSettings(BaseSettings):
  groq_api_key: str
  groq_model: str  = "llama-3.3-70b-versatile"
  rate_limiter_url: str = "http://localhost:8000"
  max_revisions: int = 3

  model_config = SettingsConfigDict(
    env_file = ".env",
    env_file_encoding = "utf-8",
    extra = "ignore"
  )


agent_settings = AgentSettings()