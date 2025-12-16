#!/usr/bin/env python3
"""
Simple startup script for OneDrive Organizer MCP Server
"""

import uvicorn
import config

if __name__ == "__main__":
    print("🚀 Starting OneDrive Organizer MCP Server...")
    print(f"📍 Server will be available at: http://{config.HOST}:{config.PORT}")
    print(f"📚 API Documentation: http://{config.HOST}:{config.PORT}/docs")
    print("=" * 60)
    
    try:
        # Validate configuration before starting
        config.validate_config()
        print("✅ Configuration validated successfully")
        
        # Start the server
        uvicorn.run(
            "main:app",
            host=config.HOST,
            port=config.PORT,
            reload=True,
            log_level="info"
        )
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease check your .env file and ensure all required variables are set.")
        print("Run 'python setup.py' to create the .env file automatically.")
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        print("\nCheck the error details above and ensure all dependencies are installed.")
        print("Run 'pip install -r requirements.txt' to install dependencies.")
