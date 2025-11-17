from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):

    gemini_api_key: str = Field(..., env="GEMINI_API_KEY") 
    ai_provider: str = Field(..., env="AI_PROVIDER")
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    mongodb_uri: str = Field(..., env="MONGODB_URI")
    db_name: str = Field("aibot", env="DB_NAME")
    orders_collection: str = Field("orders", env="ORDERS_COLLECTION")
    stripe_secret_key: str = Field(..., env="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field(..., env="STRIPE_WEBHOOK_SECRET")
    paystack_secret_key: str = Field(..., env="PAYSTACK_SECRET_KEY")
    paystack_public_key: str = Field(..., env="PAYSTACK_PUBLIC_KEY")
    paypal_client_id: str = Field(..., env="PAYPAL_CLIENT_ID")
    paypal_secret: str = Field(..., env="PAYPAL_SECRET")
    sendgrid_api_key: str = Field(..., env="SENDGRID_API_KEY")
    from_email: str = Field(..., env="FROM_EMAIL")
    owner_email: str = Field(..., env="OWNER_EMAIL")
    bank_name: str = Field("Fidelity Bank", env="BANK_NAME")
    account_name: str = Field("Your Business", env="ACCOUNT_NAME")
    account_number: str = Field("1234567890", env="ACCOUNT_NUMBER")
    
    #gcs_bucket_name: str = Field(..., env="GCS_BUCKET_NAME") (# i will uncomment when the cloud is set up)

settings = Settings()
