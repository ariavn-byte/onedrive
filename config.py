import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Microsoft Graph API Configuration
# Get these values from Azure Portal > App Registrations > Your App
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")

# Server Configuration
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")

# Validation
def validate_config():
    """Validate that required configuration is present"""
    missing_vars = []
    
    if not CLIENT_ID:
        missing_vars.append("CLIENT_ID")
    if not CLIENT_SECRET:
        missing_vars.append("CLIENT_SECRET")
    if not TENANT_ID:
        missing_vars.append("TENANT_ID")
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return True

# Configuration help
CONFIG_HELP = """
Required Environment Variables:
- CLIENT_ID: Your Azure App Registration client ID
- CLIENT_SECRET: Your Azure App Registration client secret  
- TENANT_ID: Your Azure tenant ID

Optional Environment Variables:
- PORT: Server port (default: 8000)
- HOST: Server host (default: 0.0.0.0)

To get these values:
1. Go to Azure Portal > App Registrations
2. Create or select your app
3. Copy the Application (client) ID
4. Go to Certificates & secrets > New client secret
5. Copy the tenant ID from Overview page
"""
