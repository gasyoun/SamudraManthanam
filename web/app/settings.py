import os

class Settings:
    DB_PATH: str = os.environ.get("DB_PATH", "corpus.db")

settings = Settings()
