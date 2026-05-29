from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
class Settings(BaseSettings):

    
    model_config = SettingsConfigDict(env_file='/.env')
    DATABASE_URL:str
    ANTHROPIC_API_KEY : str
    QDRANT_URL:str
    TOP_K_RESULTS:int



settings = Settings()