#!/usr/bin/env python3
"""
Setup script for OneDrive Organizer MCP Server
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file already exists")
        return
    
    print("📝 Creating .env file...")
    env_content = """# Microsoft Graph API Configuration
# Get these values from Azure Portal > App Registrations > Your App
CLIENT_ID=your-client-id-here
CLIENT_SECRET=your-client-secret-here
TENANT_ID=your-tenant-id-here

# Optional: Port configuration
PORT=8000
HOST=0.0.0.0
"""
    
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print("✅ .env file created")
    print("⚠️  Please update .env with your actual Microsoft Graph API credentials")

def check_config():
    """Check if configuration is valid"""
    print("🔍 Checking configuration...")
    try:
        from config import validate_config
        validate_config()
        print("✅ Configuration is valid")
    except ImportError:
        print("❌ Configuration module not found")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please update your .env file with the required credentials")
        sys.exit(1)

def main():
    """Main setup function"""
    print("🚀 Setting up OneDrive Organizer MCP Server...")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    install_dependencies()
    
    # Create .env file
    create_env_file()
    
    # Check configuration
    check_config()
    
    print("=" * 50)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Update .env file with your Microsoft Graph API credentials")
    print("2. Run: python main.py")
    print("3. Or run: uvicorn main:app --reload")
    print("\nFor deployment on Render:")
    print("- Set start command to: uvicorn main:app --host 0.0.0.0 --port 8000")
    print("- Add your environment variables in Render dashboard")

if __name__ == "__main__":
    main()
