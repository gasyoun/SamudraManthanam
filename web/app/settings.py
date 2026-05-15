import os

class Settings:
    DB_PATH: str = os.environ.get("DB_PATH", "corpus.db")
    # Path to the unpacked corpus directory (contains Data/ and Programdata/).
    # Must be set via environment variable for VPS deployment.
    CORPUS_PATH: str = os.environ.get("CORPUS_PATH", "")

settings = Settings()
