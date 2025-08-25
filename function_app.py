import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List
import auth

# Microsoft Graph API endpoints
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
ALLOWED_TOOLS = [
    "list_files",
    "organize_files",
    "create_folder",
    "move_file",
    "delete_file",
    "search_files",
    "get_file_info"
]

class OneDriveOrganizer:
    def __init__(self):
        self.access_token = None
        # Don't authenticate immediately - wait until first request
    
    def _authenticate(self):
        """Authenticate with Microsoft Graph API using client credentials flow"""
        if self.access_token:
            return  # Already authenticated
        
        # Check if we have credentials
        if not auth.client_id or not auth.client_secret or not auth.tenant_id:
            raise Exception("Missing Microsoft Graph API credentials. Please check your .env file.")
        
        token_url = f"https://login.microsoftonline.com/{auth.tenant_id}/oauth2/v2.0/token"
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': auth.client_id,
            'client_secret': auth.client_secret,
            'scope': 'https://graph.microsoft.com/.default'
        }
        
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            self.access_token = response.json()['access_token']
        else:
            raise Exception(f"Authentication failed: {response.text}")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Microsoft Graph API"""
        if not self.access_token:
            self._authenticate()
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{GRAPH_BASE_URL}{endpoint}"
        response = requests.request(method, url, headers=headers, **kwargs)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
    
    def _get_user_id(self) -> str:
        """Get the first available user ID for application-level access"""
        # For application permissions, we need to use a specific user ID
        # This gets the first user in the organization
        endpoint = "/users?$top=1&$select=id"
        response = self._make_request('GET', endpoint)
        
        if response.get('value') and len(response['value']) > 0:
            return response['value'][0]['id']
        else:
            raise Exception("No users found in the organization")
    
    def _get_drive_id(self, user_id: str) -> str:
        """Get the default drive ID for a user"""
        endpoint = f"/users/{user_id}/drives"
        response = self._make_request('GET', endpoint)
        
        if response.get('value') and len(response['value']) > 0:
            # Get the default drive (usually the first one)
            return response['value'][0]['id']
        else:
            raise Exception(f"No drives found for user {user_id}")
    
    def list_files(self, folder_path: str = "/", limit: int = 100, user_id: str = None) -> Dict[str, Any]:
        """List files in a OneDrive folder"""
        if not user_id:
            user_id = self._get_user_id()
        
        drive_id = self._get_drive_id(user_id)
        
        if folder_path == "/":
            # Root folder
            endpoint = f"/drives/{drive_id}/root/children?$top={limit}&$select=id,name,size,lastModifiedDateTime,file,folder"
        else:
            # Specific folder
            endpoint = f"/drives/{drive_id}/root:{folder_path}:/children?$top={limit}&$select=id,name,size,lastModifiedDateTime,file,folder"
        
        return self._make_request('GET', endpoint)
    
    def create_folder(self, name: str, parent_path: str = "/", user_id: str = None) -> Dict[str, Any]:
        """Create a new folder in OneDrive"""
        if not user_id:
            user_id = self._get_user_id()
        
        drive_id = self._get_drive_id(user_id)
        
        if parent_path == "/":
            # Root folder
            endpoint = f"/drives/{drive_id}/root/children"
        else:
            # Specific folder
            endpoint = f"/drives/{drive_id}/root:{parent_path}:/children"
        
        data = {
            "name": name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename"
        }
        return self._make_request('POST', endpoint, json=data)
    
    def move_file(self, file_id: str, new_parent_id: str, user_id: str = None) -> Dict[str, Any]:
        """Move a file to a new parent folder"""
        if not user_id:
            user_id = self._get_user_id()
        
        drive_id = self._get_drive_id(user_id)
        endpoint = f"/drives/{drive_id}/items/{file_id}"
        data = {
            "parentReference": {
                "id": new_parent_id
            }
        }
        return self._make_request('PATCH', endpoint, json=data)
    
    def delete_file(self, file_id: str, user_id: str = None) -> Dict[str, Any]:
        """Delete a file from OneDrive"""
        if not user_id:
            user_id = self._get_user_id()
        
        drive_id = self._get_drive_id(user_id)
        endpoint = f"/drives/{drive_id}/items/{file_id}"
        return self._make_request('DELETE', endpoint)
    
    def search_files(self, query: str, limit: int = 50, user_id: str = None) -> Dict[str, Any]:
        """Search for files in OneDrive"""
        if not user_id:
            user_id = self._get_user_id()
        
        drive_id = self._get_drive_id(user_id)
        endpoint = f"/drives/{drive_id}/root/search(q='{query}')?$top={limit}&$select=id,name,size,lastModifiedDateTime,file,folder"
        return self._make_request('GET', endpoint)
    
    def get_file_info(self, file_id: str, user_id: str = None) -> Dict[str, Any]:
        """Get detailed information about a specific file"""
        if not user_id:
            user_id = self._get_user_id()
        
        drive_id = self._get_drive_id(user_id)
        endpoint = f"/drives/{drive_id}/items/{file_id}?$select=id,name,size,lastModifiedDateTime,file,folder,parentReference"
        return self._make_request('GET', endpoint)
    
    def organize_files(self, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Organize files based on specified rules"""
        results = []
        
        for rule in rules:
            try:
                if rule['action'] == 'move':
                    # Get files matching criteria
                    search_query = rule.get('search_query', '')
                    if search_query:
                        files = self.search_files(search_query)
                        for file in files.get('value', []):
                            if file.get('file'):  # Only move files, not folders
                                # Create target folder if it doesn't exist
                                target_folder = rule['target_folder']
                                folder_result = self.create_folder(target_folder)
                                
                                # Move file to target folder
                                move_result = self.move_file(file['id'], folder_result['id'])
                                results.append({
                                    'file': file['name'],
                                    'action': 'moved',
                                    'target': target_folder,
                                    'status': 'success'
                                })
                
                elif rule['action'] == 'delete':
                    # Delete files matching criteria
                    search_query = rule.get('search_query', '')
                    if search_query:
                        files = self.search_files(search_query)
                        for file in files.get('value', []):
                            if file.get('file'):
                                self.delete_file(file['id'])
                                results.append({
                                    'file': file['name'],
                                    'action': 'deleted',
                                    'status': 'success'
                                })
            
            except Exception as e:
                results.append({
                    'rule': rule,
                    'status': 'error',
                    'error': str(e)
                })
        
        return {'results': results}

# Global instance - but don't authenticate immediately
organizer = OneDriveOrganizer()

def _handle(tool: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tool invocation requests"""
    try:
        if tool == "list_files":
            folder_path = data.get('folder_path', '/')
            limit = data.get('limit', 100)
            user_id = data.get('user_id')  # Optional: allow specifying user ID
            result = organizer.list_files(folder_path, limit, user_id)
            return {"success": True, "data": result}
        
        elif tool == "create_folder":
            name = data.get('name')
            parent_path = data.get('parent_path', '/')
            user_id = data.get('user_id')  # Optional: allow specifying user ID
            if not name:
                return {"success": False, "error": "Folder name is required"}
            result = organizer.create_folder(name, parent_path, user_id)
            return {"success": True, "data": result}
        
        elif tool == "move_file":
            file_id = data.get('file_id')
            new_parent_id = data.get('new_parent_id')
            user_id = data.get('user_id')  # Optional: allow specifying user ID
            if not file_id or not new_parent_id:
                return {"success": False, "error": "File ID and new parent ID are required"}
            result = organizer.move_file(file_id, new_parent_id, user_id)
            return {"success": True, "data": result}
        
        elif tool == "delete_file":
            file_id = data.get('file_id')
            user_id = data.get('user_id')  # Optional: allow specifying user ID
            if not file_id:
                return {"success": False, "error": "File ID is required"}
            result = organizer.delete_file(file_id, user_id)
            return {"success": True, "data": result}
        
        elif tool == "search_files":
            query = data.get('query')
            limit = data.get('limit', 50)
            user_id = data.get('user_id')  # Optional: allow specifying user ID
            if not query:
                return {"success": False, "error": "Search query is required"}
            result = organizer.search_files(query, limit, user_id)
            return {"success": True, "data": result}
        
        elif tool == "get_file_info":
            file_id = data.get('file_id')
            user_id = data.get('user_id')  # Optional: allow specifying user ID
            if not file_id:
                return {"success": False, "error": "File ID is required"}
            result = organizer.get_file_info(file_id, user_id)
            return {"success": True, "data": result}
        
        elif tool == "organize_files":
            rules = data.get('rules', [])
            if not rules:
                return {"success": False, "error": "Organization rules are required"}
            result = organizer.organize_files(rules)
            return {"success": True, "data": result}
        
        else:
            return {"success": False, "error": f"Unknown tool: {tool}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}
