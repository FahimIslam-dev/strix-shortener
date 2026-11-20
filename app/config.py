import os
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "StrixShort - Premium Link Intelligence & Shortener"
    COMPANY_NAME: str = "StrixDevs"
    COMPANY_URL: str = "https://strixdevs.com"
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "strixdevs_super_secure_key_2026")
    
    # Google AdSense Configuration
    ADSENSE_CLIENT_ID: str = os.getenv("ADSENSE_CLIENT_ID", "ca-pub-XXXXXXXXXXXXXXXX")
    ADSENSE_ENABLED: bool = os.getenv("ADSENSE_ENABLED", "true").lower() in ("true", "1")
    
    # Safe Transit / Ad-Supported Preview Page
    DEFAULT_TRANSIT_DELAY: int = 4  # seconds countdown on monetization transit page
    
    # SEO & Metadata
    SITE_DESCRIPTION: str = (
        "StrixDevs StrixShort is a premium enterprise-grade URL shortener, QR code generator, "
        "and link intelligence platform. Track clicks, analyze audiences, build UTM campaigns, "
        "and protect links with advanced cybersecurity."
    )
    SITE_KEYWORDS: str = (
        "URL shortener, link shortener, free custom link, QR code generator, UTM builder, "
        "link analytics, safe link expander, StrixDevs, branded short links, digital marketing tools"
    )

settings = Settings()
