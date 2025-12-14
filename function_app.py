import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import auth
from azure.identity import DefaultAzureCredential

# Microsoft Graph API endpoints
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
ALLOWED_TOOLS = [
    "list_files",
    "organize_files",
    "create_folder",
    "move_file",
    "delete_file",
    "search_files",
    "get_file_info",
    # New enhanced tools
    "upload_file",
    "download_file",
    "copy_file",
    "rename_file",
    "get_file_content",
    "get_file_thumbnail",
    "search_by_type",
    "search_by_date",
    "get_recent_files",
    "get_storage_usage",
    "bulk_move",
    "bulk_delete",
    "bulk_copy"
]

class OneDriveOrganizer:
    def __init__(self):
        self.access_token = None
        # Don't authenticate immediately - wait until first request
    
    def _authenticate(self):
        """Authenticate with Microsoft Graph API using Azure Identity (Client Secret or Managed Identity)"""
        if self.access_token:
            return  # Already authenticated
        
        # Set environment variables for DefaultAzureCredential if they are present in config but not environment
        import os
        if auth.client_id and "AZURE_CLIENT_ID" not in os.environ:
            os.environ["AZURE_CLIENT_ID"] = auth.client_id
        if auth.tenant_id and "AZURE_TENANT_ID" not in os.environ:
            os.environ["AZURE_TENANT_ID"] = auth.tenant_id
        if auth.client_secret and "AZURE_CLIENT_SECRET" not in os.environ:
            os.environ["AZURE_CLIENT_SECRET"] = auth.client_secret

        try:
            credential = DefaultAzureCredential()
            # Request token for Microsoft Graph
            token = credential.get_token("https://graph.microsoft.com/.default")
            self.access_token = token.token
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")
    
    def _make_request(self, method: str, endpoint: str, max_retries: int = 3, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Microsoft Graph API with retry logic"""
        if not self.access_token:
            self._authenticate()

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        url = f"{GRAPH_BASE_URL}{endpoint}"

        # Retry logic with exponential backoff
        for attempt in range(max_retries + 1):
            response = requests.request(method, url, headers=headers, **kwargs)

            if response.status_code in [200, 201, 204]:
                # Success - return response (handle 204 No Content for DELETE)
                if response.status_code == 204:
                    return {"success": True, "message": "Operation completed successfully"}
                return response.json() if response.content else {"success": True}

            elif response.status_code == 429:
                # Rate limit hit - check Retry-After header
                retry_after = int(response.headers.get('Retry-After', 2 ** attempt))
                if attempt < max_retries:
                    print(f"⚠️  Rate limit hit. Retrying after {retry_after} seconds... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_after)
                    continue
                else:
                    raise Exception(f"Rate limit exceeded after {max_retries} retries. Please try again later.")

            elif response.status_code == 401:
                # Unauthorized - token might have expired, re-authenticate once
                if attempt == 0:
                    print("🔄 Token expired, re-authenticating...")
                    self.access_token = None
                    self._authenticate()
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    continue
                else:
                    raise Exception(f"Authentication failed: {response.status_code} - {response.text}")

            elif response.status_code >= 500:
                # Server error - retry with exponential backoff
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    print(f"⚠️  Server error ({response.status_code}). Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue

            # For other errors, don't retry
            error_detail = response.text
            try:
                error_json = response.json()
                if 'error' in error_json:
                    error_detail = error_json['error'].get('message', error_detail)
            except:
                pass

            raise Exception(f"API request failed: {response.status_code} - {error_detail}")

        # Should never reach here, but just in case
        raise Exception("Maximum retry attempts exceeded")
    
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
            endpoint = f"/drives/{drive_id}/root/children?$top={limit}&$select=id,name,size,lastModifiedDateTime,file,folder,webUrl"
        else:
            # Specific folder
            endpoint = f"/drives/{drive_id}/root:{folder_path}:/children?$top={limit}&$select=id,name,size,lastModifiedDateTime,file,folder,webUrl"
        
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
    
    def move_file(self, file_id: str, new_parent_path: str, user_id: str = None) -> Dict[str, Any]:
        """Move a file to a new parent folder (FIXED IMPLEMENTATION)"""
        if not user_id:
            user_id = self._get_user_id()
        
        drive_id = self._get_drive_id(user_id)
        
        # Get the target folder ID first
        if new_parent_path == "/":
            target_folder_id = "root"
        else:
            # Get the target folder by path
            folder_endpoint = f"/drives/{drive_id}/root:{new_parent_path}:"
            folder_response = self._make_request('GET', folder_endpoint)
            target_folder_id = folder_response['id']
        
        # Move the file using the correct Microsoft Graph API method
        endpoint = f"/drives/{drive_id}/items/{file_id}"
        data = {
            "parentReference": {
                "driveId": drive_id,
                "id": target_folder_id
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
        endpoint = f"/drives/{drive_id}/root/search(q='{query}')?$top={limit}&$select=id,name,size,lastModifiedDateTime,file,folder,webUrl"
        return self._make_request('GET', endpoint)
    
    def get_file_info(self, file_id: str, user_id: str = None) -> Dict[str, Any]:
        """Get detailed information about a specific file"""
        if not user_id:
            user_id = self._get_user_id()
        
        drive_id = self._get_drive_id(user_id)
        endpoint = f"/drives/{drive_id}/items/{file_id}?$select=id,name,size,lastModifiedDateTime,file,folder,parentReference,webUrl,createdBy,lastModifiedBy"
        return self._make_request('GET', endpoint)
    
    def upload_file(self, file_path: str, target_path: str, user_id: str = None) -> Dict[str, Any]:
        """Upload a file to OneDrive"""
        if not user_id:
            user_id = self._get_user_id()
        
        drive_id = self._get_drive_id(user_id)
        
        # For small files (< 4MB), use simple upload
        # For larger files, we'd need to implement chunked upload
        with open(file_path, 'rb') as file:
            file_content = file.read()
        
        endpoint = f"/drives/{drive_id}/root:{target_path}:/content"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/octet-stream'
        }
        
        url = f"{GRAPH_BASE_URL}{endpoint}"
        response = requests.put(url, headers=headers, data=file_content)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Upload failed: {response.status_code} - {response.text}")
    
    def download_file(self, file_id: str, local_path: str, user_id: str = None) -> Dict[str, Any]:
        """Download a file from OneDrive"""
        if not user_id:
            user_id = self._get_user_id()
        
        drive_id = self._get_drive_id(user_id)
        endpoint = f"/drives/{drive_id}/items/{file_id}/content"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        url = f"{GRAPH_BASE_URL}{endpoint}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            with open(local_path, 'wb') as file:
                file.write(response.content)
            return {"success": True, "local_path": local_path, "size": len(response.content)}
        else:
            raise Exception(f"Download failed: {response.status_code} - {response.text}")
    
    def copy_file(self, file_id: str, new_name: str, target_path: str, user_id: str = None) -> Dict[str, Any]:
        """Copy a file to a new location"""
        if not user_id:
            user_id = self._get_user_id()
        
        drive_id = self._get_drive_id(user_id)
        
        # Get the target folder ID
        if target_path == "/":
            target_folder_id = "root"
        else:
            folder_endpoint = f"/drives/{drive_id}/root:{target_path}:"
            folder_response = self._make_request('GET', folder_endpoint)
            target_folder_id = folder_response['id']
        
        endpoint = f"/drives/{drive_id}/items/{file_id}/copy"
        data = {
            "parentReference": {
                "driveId": drive_id,
                "id": target_folder_id
            },
            "name": new_name
        }
        return self._make_request('POST', endpoint, json=data)
    
    def rename_file(self, file_id: str, new_name: str, user_id: str = None) -> Dict[str, Any]:
        """Rename a file or folder"""
        if not user_id:
            user_id = self._get_user_id()
        
        drive_id = self._get_drive_id(user_id)
        endpoint = f"/drives/{drive_id}/items/{file_id}"
        data = {"name": new_name}
        return self._make_request('PATCH', endpoint, json=data)
    
    def get_file_content(self, file_id: str, user_id: str = None) -> Dict[str, Any]:
        """Get file content for text files"""
        if not user_id:
            user_id = self._get_user_id()
        
        drive_id = self._get_drive_id(user_id)
        endpoint = f"/drives/{drive_id}/items/{file_id}/content"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        url = f"{GRAPH_BASE_URL}{endpoint}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return {"content": response.text, "encoding": response.encoding}
        else:
            raise Exception(f"Failed to get file content: {response.status_code} - {response.text}")
    
    def get_file_thumbnail(self, file_id: str, size: str = "large", user_id: str = None) -> Dict[str, Any]:
        """Get file thumbnail"""
        if not user_id:
            user_id = self._get_user_id()
        
        drive_id = self._get_drive_id(user_id)
        endpoint = f"/drives/{drive_id}/items/{file_id}/thumbnails?$select=large,medium,small"
        return self._make_request('GET', endpoint)
    
    def search_by_type(self, file_type: str, limit: int = 50, user_id: str = None) -> Dict[str, Any]:
        """Search files by MIME type"""
        if not user_id:
            user_id = self._get_user_id()
        
        drive_id = self._get_drive_id(user_id)
        # Search for files with specific extensions
        endpoint = f"/drives/{drive_id}/root/search(q='{file_type}')?$top={limit}&$select=id,name,size,lastModifiedDateTime,file,folder,webUrl"
        return self._make_request('GET', endpoint)
    
    def search_by_date(self, start_date: str, end_date: str, limit: int = 50, user_id: str = None) -> Dict[str, Any]:
        """Search files by modification date range"""
        if not user_id:
            user_id = self._get_user_id()
        
        drive_id = self._get_drive_id(user_id)
        # Filter by date range
        endpoint = f"/drives/{drive_id}/root/children?$filter=lastModifiedDateTime ge {start_date} and lastModifiedDateTime le {end_date}&$top={limit}&$select=id,name,size,lastModifiedDateTime,file,folder,webUrl"
        return self._make_request('GET', endpoint)
    
    def get_recent_files(self, days: int = 7, limit: int = 50, user_id: str = None) -> Dict[str, Any]:
        """Get recently modified files"""
        if not user_id:
            user_id = self._get_user_id()
        
        drive_id = self._get_drive_id(user_id)
        
        # Calculate date range
        end_date = datetime.now().isoformat() + 'Z'
        start_date = (datetime.now() - timedelta(days=days)).isoformat() + 'Z'
        
        endpoint = f"/drives/{drive_id}/root/children?$filter=lastModifiedDateTime ge {start_date}&$orderby=lastModifiedDateTime desc&$top={limit}&$select=id,name,size,lastModifiedDateTime,file,folder,webUrl"
        return self._make_request('GET', endpoint)
    
    def get_storage_usage(self, user_id: str = None) -> Dict[str, Any]:
        """Get OneDrive storage statistics"""
        if not user_id:
            user_id = self._get_user_id()
        
        drive_id = self._get_drive_id(user_id)
        endpoint = f"/drives/{drive_id}"
        return self._make_request('GET', endpoint)
    
    def bulk_move(self, file_ids: List[str], target_path: str, user_id: str = None) -> Dict[str, Any]:
        """Move multiple files to a target folder"""
        results = []
        for file_id in file_ids:
            try:
                result = self.move_file(file_id, target_path, user_id)
                results.append({"file_id": file_id, "status": "success", "result": result})
            except Exception as e:
                results.append({"file_id": file_id, "status": "error", "error": str(e)})
        return {"results": results}
    
    def bulk_delete(self, file_ids: List[str], user_id: str = None) -> Dict[str, Any]:
        """Delete multiple files"""
        results = []
        for file_id in file_ids:
            try:
                result = self.delete_file(file_id, user_id)
                results.append({"file_id": file_id, "status": "success", "result": result})
            except Exception as e:
                results.append({"file_id": file_id, "status": "error", "error": str(e)})
        return {"results": results}
    
    def bulk_copy(self, file_ids: List[str], target_path: str, user_id: str = None) -> Dict[str, Any]:
        """Copy multiple files to a target folder"""
        results = []
        for file_id in file_ids:
            try:
                # Get file info to preserve name
                file_info = self.get_file_info(file_id, user_id)
                file_name = file_info['name']
                result = self.copy_file(file_id, file_name, target_path, user_id)
                results.append({"file_id": file_id, "status": "success", "result": result})
            except Exception as e:
                results.append({"file_id": file_id, "status": "error", "error": str(e)})
        return {"results": results}
    
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
                                move_result = self.move_file(file['id'], target_folder)
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
            new_parent_path = data.get('new_parent_path')  # Changed from new_parent_id
            user_id = data.get('user_id')  # Optional: allow specifying user ID
            if not file_id or not new_parent_path:
                return {"success": False, "error": "File ID and new parent path are required"}
            result = organizer.move_file(file_id, new_parent_path, user_id)
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
        
        # New enhanced tools
        elif tool == "upload_file":
            file_path = data.get('file_path')
            target_path = data.get('target_path')
            user_id = data.get('user_id')
            if not file_path or not target_path:
                return {"success": False, "error": "File path and target path are required"}
            result = organizer.upload_file(file_path, target_path, user_id)
            return {"success": True, "data": result}
        
        elif tool == "download_file":
            file_id = data.get('file_id')
            local_path = data.get('local_path')
            user_id = data.get('user_id')
            if not file_id or not local_path:
                return {"success": False, "error": "File ID and local path are required"}
            result = organizer.download_file(file_id, local_path, user_id)
            return {"success": True, "data": result}
        
        elif tool == "copy_file":
            file_id = data.get('file_id')
            new_name = data.get('new_name')
            target_path = data.get('target_path')
            user_id = data.get('user_id')
            if not file_id or not new_name or not target_path:
                return {"success": False, "error": "File ID, new name, and target path are required"}
            result = organizer.copy_file(file_id, new_name, target_path, user_id)
            return {"success": True, "data": result}
        
        elif tool == "rename_file":
            file_id = data.get('file_id')
            new_name = data.get('new_name')
            user_id = data.get('user_id')
            if not file_id or not new_name:
                return {"success": False, "error": "File ID and new name are required"}
            result = organizer.rename_file(file_id, new_name, user_id)
            return {"success": True, "data": result}
        
        elif tool == "get_file_content":
            file_id = data.get('file_id')
            user_id = data.get('user_id')
            if not file_id:
                return {"success": False, "error": "File ID is required"}
            result = organizer.get_file_content(file_id, user_id)
            return {"success": True, "data": result}
        
        elif tool == "get_file_thumbnail":
            file_id = data.get('file_id')
            size = data.get('size', 'large')
            user_id = data.get('user_id')
            if not file_id:
                return {"success": False, "error": "File ID is required"}
            result = organizer.get_file_thumbnail(file_id, size, user_id)
            return {"success": True, "data": result}
        
        elif tool == "search_by_type":
            file_type = data.get('file_type')
            limit = data.get('limit', 50)
            user_id = data.get('user_id')
            if not file_type:
                return {"success": False, "error": "File type is required"}
            result = organizer.search_by_type(file_type, limit, user_id)
            return {"success": True, "data": result}
        
        elif tool == "search_by_date":
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            limit = data.get('limit', 50)
            user_id = data.get('user_id')
            if not start_date or not end_date:
                return {"success": False, "error": "Start date and end date are required"}
            result = organizer.search_by_date(start_date, end_date, limit, user_id)
            return {"success": True, "data": result}
        
        elif tool == "get_recent_files":
            days = data.get('days', 7)
            limit = data.get('limit', 50)
            user_id = data.get('user_id')
            result = organizer.get_recent_files(days, limit, user_id)
            return {"success": True, "data": result}
        
        elif tool == "get_storage_usage":
            user_id = data.get('user_id')
            result = organizer.get_storage_usage(user_id)
            return {"success": True, "data": result}
        
        elif tool == "bulk_move":
            file_ids = data.get('file_ids', [])
            target_path = data.get('target_path')
            user_id = data.get('user_id')
            if not file_ids or not target_path:
                return {"success": False, "error": "File IDs and target path are required"}
            result = organizer.bulk_move(file_ids, target_path, user_id)
            return {"success": True, "data": result}
        
        elif tool == "bulk_delete":
            file_ids = data.get('file_ids', [])
            user_id = data.get('user_id')
            if not file_ids:
                return {"success": False, "error": "File IDs are required"}
            result = organizer.bulk_delete(file_ids, user_id)
            return {"success": True, "data": result}
        
        elif tool == "bulk_copy":
            file_ids = data.get('file_ids', [])
            target_path = data.get('target_path')
            user_id = data.get('user_id')
            if not file_ids or not target_path:
                return {"success": False, "error": "File IDs and target path are required"}
            result = organizer.bulk_copy(file_ids, target_path, user_id)
            return {"success": True, "data": result}
        
        else:
            return {"success": False, "error": f"Unknown tool: {tool}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}
