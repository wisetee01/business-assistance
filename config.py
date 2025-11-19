from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv
from typing import Optional 
load_dotenv()

class Settings(BaseSettings):

    gemini_api_key: str = Field(..., env="GEMINI_API_KEY") 
    ai_provider: str = Field(None, env="AI_PROVIDER") 
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    mongodb_uri: str = Field(..., env="MONGODB_URI")
    db_name: str = Field("aibot", env="DB_NAME")
    orders_collection: str = Field("orders", env="ORDERS_COLLECTION")
    stripe_secret_key: Optional[str] = Field(None, env="STRIPE_SECRET_KEY") # Changed from ... to None
    stripe_webhook_secret: Optional[str] = Field(None, env="STRIPE_WEBHOOK_SECRET") # Changed from ... to None
    paystack_secret_key: Optional[str] = Field(None, env="PAYSTACK_SECRET_KEY") # Changed from ... to None
    paystack_public_key: Optional[str] = Field(None, env="PAYSTACK_PUBLIC_KEY") # Changed from ... to None
    paypal_client_id: Optional[str] = Field(None, env="PAYPAL_CLIENT_ID") # Changed from ... to None
    paypal_secret: Optional[str] = Field(None, env="PAYPAL_SECRET") # Changed from ... to None
    sendgrid_api_key: Optional[str] = Field(None, env="SENDGRID_API_KEY") # Changed from ... to None
    from_email: Optional[str] = Field(None, env="FROM_EMAIL") # Changed from ... to None
    owner_email: Optional[str] = Field(None, env="OWNER_EMAIL") # Changed from ... to None
    bank_name: Optional[str] = Field(None, env="BANK_NAME") # Changed from ... to None
    account_name: Optional[str] = Field(None, env="ACCOUNT_NAME") 
    account_number: Optional[str] = Field(None, env="ACCOUNT_NUMBER") 
    
    #gcs_bucket_name: str = Field(..., env="GCS_BUCKET_NAME") (# i will uncomment when the cloud is set up)

settings = Settings()