from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    tg_api_token: str

    class Config:
        env_file = "app/.env"

settings = Settings()