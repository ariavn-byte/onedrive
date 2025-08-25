# OneDrive Organizer MCP Server

#### 🧠 Project Overview
This project provides a FastAPI-based MCP (Modular Copilot Plugin) server that integrates with Microsoft Graph API to organize OneDrive content using intelligent agents.

- **Modular architecture** for tool-based invocation
- **Integration with Microsoft Graph API** for OneDrive management
- **Designed for deployment on Render** with proper configuration
- **OpenAPI specification** included for easy integration
- **Comprehensive error handling** and validation

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Microsoft Azure account with Graph API access
- OneDrive for Business or Personal account

### 1. Clone and Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd onedrive

# Run the automated setup
python setup.py
```

### 2. Configure Microsoft Graph API
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **App Registrations** → **New registration**
3. Give it a name (e.g., "OneDrive Organizer")
4. Select **Accounts in this organizational directory only**
5. Click **Register**
6. Copy the **Application (client) ID** and **Directory (tenant) ID**
7. Go to **Certificates & secrets** → **New client secret**
8. Copy the **Value** (this is your client secret)
9. Go to **API permissions** → **Add permission**
10. Select **Microsoft Graph** → **Application permissions**
11. Add these permissions:
    - `Files.ReadWrite.All`
    - `Sites.ReadWrite.All`
    - `User.Read.All`
12. Click **Grant admin consent**

### 3. Update Environment Variables
Edit the `.env` file with your credentials:
```env
CLIENT_ID=your-client-id-here
CLIENT_SECRET=your-client-secret-here
TENANT_ID=your-tenant-id-here
PORT=8000
HOST=0.0.0.0
```

### 4. Run the Server
```bash
# Development mode
uvicorn main:app --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📡 API Endpoints

### Core Endpoints
- `GET /` - API information and available tools
- `GET /health` - Health check
- `GET /tools` - List all available tools
- `POST /invoke/{tool}` - Invoke a specific tool

### Available Tools

#### 📁 File Management
- **`list_files`** - List files in a OneDrive folder
- **`create_folder`** - Create a new folder
- **`move_file`** - Move a file to a different folder
- **`delete_file`** - Delete a file
- **`get_file_info`** - Get detailed file information

#### 🔍 Search & Organization
- **`search_files`** - Search for files by query
- **`organize_files`** - Apply organization rules to files

## 🛠️ Usage Examples

### List Files
```bash
curl -X POST "http://localhost:8000/invoke/list_files" \
  -H "Content-Type: application/json" \
  -d '{"folder_path": "/", "limit": 20}'
```

### Create Folder
```bash
curl -X POST "http://localhost:8000/invoke/create_folder" \
  -H "Content-Type: application/json" \
  -d '{"name": "Work Documents", "parent_path": "/"}'
```

### Search Files
```bash
curl -X POST "http://localhost:8000/invoke/search_files" \
  -H "Content-Type: application/json" \
  -d '{"query": "*.pdf", "limit": 50}'
```

### Organize Files with Rules
```bash
curl -X POST "http://localhost:8000/invoke/organize_files" \
  -H "Content-Type: application/json" \
  -d '{
    "rules": [
      {
        "action": "move",
        "search_query": "*.pdf",
        "target_folder": "PDFs"
      },
      {
        "action": "move",
        "search_query": "*.docx",
        "target_folder": "Documents"
      }
    ]
  }'
```

## 🧪 Testing

Run the test suite to verify your setup:
```bash
python test_api.py
```

## 🚀 Deployment on Render

1. **Push to GitHub** - Ensure your code is in a GitHub repository
2. **Create Web Service** - In Render dashboard, create a new **Web Service**
3. **Connect Repository** - Link your GitHub repository
4. **Configure Build**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 8000`
5. **Environment Variables** - Add your `.env` variables in Render dashboard
6. **Deploy** - Click deploy and wait for build completion

## 📁 Project Structure

```
onedrive/
├── main.py              # FastAPI application entry point
├── function_app.py      # Core MCP functionality and OneDrive tools
├── auth.py              # Authentication configuration
├── config.py            # Configuration validation and management
├── setup.py             # Automated setup script
├── test_api.py          # API testing script
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🔧 Configuration

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `CLIENT_ID` | Azure App Registration client ID | ✅ |
| `CLIENT_SECRET` | Azure App Registration client secret | ✅ |
| `TENANT_ID` | Azure tenant ID | ✅ |
| `PORT` | Server port (default: 8000) | ❌ |
| `HOST` | Server host (default: 0.0.0.0) | ❌ |

### Microsoft Graph API Permissions
- `Files.ReadWrite.All` - Read and write all files
- `Sites.ReadWrite.All` - Read and write all sites
- `User.Read.All` - Read user information

## 🚨 Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify your Azure App Registration credentials
   - Ensure admin consent is granted for permissions
   - Check that your app has the correct API permissions

2. **Permission Denied**
   - Verify the user has access to the OneDrive content
   - Check API permission scopes

3. **Server Won't Start**
   - Verify Python 3.8+ is installed
   - Check all dependencies are installed: `pip install -r requirements.txt`
   - Ensure `.env` file exists with valid credentials

### Debug Mode
Enable debug logging by setting environment variable:
```bash
export PYTHONPATH=.
python -m uvicorn main:app --reload --log-level debug
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify your Microsoft Graph API configuration
3. Check the server logs for error details
4. Open an issue on GitHub with detailed error information

---

**Happy organizing! 🎉**
