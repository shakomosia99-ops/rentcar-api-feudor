from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "RentCar API Feudor"
    database_url: str 
    secret_key: str = "change"
    algorithm: str = "HS256"
    access_token_min: int = 30
    refresh_token_days: int = 7
    upload_dir:str = "uploads"


    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()