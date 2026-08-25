from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg://cyberdex:cyberdex_dev_password@localhost:5432/cyberdex"
    )

    # The Movie Database
    tmdb_api_key: str = ""
    tmdb_base_url: str = "https://api.themoviedb.org/3"
    tmdb_image_base: str = "https://image.tmdb.org/t/p/w500"

    # OpenLibrary
    openlibrary_base_url: str = "https://openlibrary.org"
    openlibrary_covers_base: str = "https://covers.openlibrary.org/b"


    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8"
    )

settings = Settings()