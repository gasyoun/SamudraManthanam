from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    APP_ENV: str = "development"
    DB_PATH: str = "corpus.db"
    STATE_DB_PATH: str = ""
    CORPUS_PATH: str = ""
    PUBLIC_BASE_URL: str = ""
    ALLOWED_ORIGINS: str = ""

    # Funnel / marketing
    SYSTEMA_SANSCRITICUM_URL: str = ""
    SITE_DESCRIPTION: str = "Поисковая система по санскрито-русскому параллельному корпусу: «Бхагавадгита», «Махабхарата», упанишады и другие тексты."

    # Admin
    ADMIN_SECRET_KEY: str = ""

    # AI Settings
    AI_PROVIDER: str = "openai-compatible"
    AI_BASE_URL: str = ""
    AI_API_KEY: str = ""
    AI_MODEL: str = "gpt-3.5-turbo" # or local model name

    model_config = ConfigDict(
        env_file=".env",
        extra="allow"
    )

settings = Settings()
