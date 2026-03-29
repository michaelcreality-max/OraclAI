"""
Secure File System API for Code Editor
Provides safe file read/write operations restricted to project directory.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

log = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """File/directory information"""
    name: str
    path: str
    type: str  # 'file' or 'directory'
    size: int = 0
    modified: str = ""
    extension: str = ""


class SecureFileManager:
    """
    Secure file manager that restricts access to project directory only.
    Prevents directory traversal attacks and malicious file access.
    """
    
    # Allowed file extensions for editing
    ALLOWED_EXTENSIONS = {
        '.py', '.js', '.html', '.css', '.json', '.md', '.txt', '.yml', '.yaml',
        '.sql', '.sh', '.bat', '.ini', '.conf', '.cfg', '.xml', '.csv'
    }
    
    # Blocked patterns (security sensitive)
    BLOCKED_PATTERNS = [
        '..',  # Directory traversal
        '~',   # Home directory
        '//',  # URL patterns
        '\\',  # Windows traversal
        '.env',  # Environment files with secrets
        '.key',  # Key files
        '.pem',  # Certificate files
        '.p12',  # PKCS12 files
        '.pfx',  # Certificate files
        'id_rsa',  # SSH keys
        '.htpasswd',  # Apache password files
        '.htaccess',  # Apache config (may contain sensitive data)
        '.git',  # Git internals
        '__pycache__',  # Python cache
        '.pytest_cache',
        '.mypy_cache',
        'node_modules',
    ]
    
    def __init__(self, project_root: str = None):
        """
        Initialize secure file manager.
        
        Args:
            project_root: Absolute path to project root directory.
                         If None, uses directory containing this file.
        """
        if project_root is None:
            # Get project root (parent of quant_ecosystem)
            current_file = Path(__file__).resolve()
            self.project_root = current_file.parent.parent.resolve()
        else:
            self.project_root = Path(project_root).resolve()
        
        log.info(f"SecureFileManager initialized with root: {self.project_root}")
    
    def _validate_path(self, requested_path: str) -> Tuple[bool, Path, str]:
        """
        Validate and sanitize file path.
        
        Returns:
            (is_valid, resolved_path, error_message)
        """
        if not requested_path:
            return False, None, "Path is required"
        
        # Check for blocked patterns
        requested_lower = requested_path.lower()
        for pattern in self.BLOCKED_PATTERNS:
            if pattern in requested_path:
                return False, None, f"Access to paths containing '{pattern}' is blocked for security"
        
        # Normalize and resolve path
        try:
            # Join with project root and resolve
            full_path = (self.project_root / requested_path).resolve()
            
            # Ensure path is within project root (prevent traversal)
            try:
                full_path.relative_to(self.project_root)
            except ValueError:
                return False, None, "Access denied: Path outside project directory"
            
            # Check if path exists
            if not full_path.exists():
                # Allow creating new files within project
                parent = full_path.parent
                if not parent.exists():
                    return False, None, "Parent directory does not exist"
                try:
                    parent.relative_to(self.project_root)
                except ValueError:
                    return False, None, "Access denied: Parent outside project directory"
            
            return True, full_path, ""
            
        except Exception as e:
            return False, None, f"Path validation error: {str(e)}"
    
    def _is_editable(self, file_path: Path) -> bool:
        """Check if file type is editable"""
        if file_path.is_dir():
            return False
        ext = file_path.suffix.lower()
        return ext in self.ALLOWED_EXTENSIONS
    
    def list_directory(self, relative_path: str = "") -> Dict[str, Any]:
        """
        List files and directories in a path.
        
        Args:
            relative_path: Path relative to project root
            
        Returns:
            Dict with items list or error
        """
        is_valid, full_path, error = self._validate_path(relative_path)
        
        if not is_valid:
            return {"success": False, "error": error}
        
        if not full_path.exists():
            return {"success": False, "error": "Directory does not exist"}
        
        if not full_path.is_dir():
            return {"success": False, "error": "Path is not a directory"}
        
        try:
            items = []
            
            for item in sorted(full_path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                # Skip blocked patterns
                if any(pattern in item.name for pattern in self.BLOCKED_PATTERNS):
                    continue
                
                # Skip hidden files (starting with .)
                if item.name.startswith('.') and item.name != '.gitignore':
                    continue
                
                stat = item.stat()
                
                file_info = FileInfo(
                    name=item.name,
                    path=str(item.relative_to(self.project_root)),
                    type='directory' if item.is_dir() else 'file',
                    size=stat.st_size if item.is_file() else 0,
                    modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    extension=item.suffix if item.is_file() else ""
                )
                
                items.append({
                    "name": file_info.name,
                    "path": file_info.path,
                    "type": file_info.type,
                    "size": file_info.size,
                    "modified": file_info.modified,
                    "extension": file_info.extension,
                    "editable": self._is_editable(item) if item.is_file() else False
                })
            
            return {
                "success": True,
                "path": relative_path,
                "absolute_path": str(full_path),
                "items": items
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to list directory: {str(e)}"}
    
    def read_file(self, relative_path: str) -> Dict[str, Any]:
        """
        Read file contents.
        
        Args:
            relative_path: Path relative to project root
            
        Returns:
            Dict with content or error
        """
        is_valid, full_path, error = self._validate_path(relative_path)
        
        if not is_valid:
            return {"success": False, "error": error}
        
        if not full_path.exists():
            return {"success": False, "error": "File does not exist"}
        
        if full_path.is_dir():
            return {"success": False, "error": "Path is a directory, not a file"}
        
        if not self._is_editable(full_path):
            ext = full_path.suffix.lower()
            return {
                "success": False, 
                "error": f"Files with extension '{ext}' are not editable for security reasons"
            }
        
        try:
            # Check file size (max 1MB for safety)
            size = full_path.stat().st_size
            if size > 1_000_000:
                return {"success": False, "error": "File too large (>1MB)"}
            
            # Read with encoding detection
            content = full_path.read_text(encoding='utf-8', errors='replace')
            
            return {
                "success": True,
                "path": relative_path,
                "content": content,
                "size": size,
                "modified": datetime.fromtimestamp(full_path.stat().st_mtime).isoformat(),
                "language": self._detect_language(full_path.suffix)
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to read file: {str(e)}"}
    
    def write_file(self, relative_path: str, content: str) -> Dict[str, Any]:
        """
        Write content to file.
        
        Args:
            relative_path: Path relative to project root
            content: File content to write
            
        Returns:
            Dict with success status or error
        """
        is_valid, full_path, error = self._validate_path(relative_path)
        
        if not is_valid:
            return {"success": False, "error": error}
        
        # If file exists, check if editable
        if full_path.exists():
            if full_path.is_dir():
                return {"success": False, "error": "Cannot overwrite directory with file"}
            
            if not self._is_editable(full_path):
                ext = full_path.suffix.lower()
                return {
                    "success": False,
                    "error": f"Cannot modify files with extension '{ext}'"
                }
        else:
            # Creating new file - check extension
            ext = full_path.suffix.lower()
            if ext and ext not in self.ALLOWED_EXTENSIONS:
                return {
                    "success": False,
                    "error": f"Cannot create files with extension '{ext}'"
                }
        
        try:
            # Ensure parent directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            full_path.write_text(content, encoding='utf-8')
            
            log.info(f"File written: {relative_path}")
            
            return {
                "success": True,
                "path": relative_path,
                "size": len(content.encode('utf-8')),
                "modified": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to write file: {str(e)}"}
    
    def delete_file(self, relative_path: str) -> Dict[str, Any]:
        """
        Delete a file.
        
        Args:
            relative_path: Path relative to project root
            
        Returns:
            Dict with success status or error
        """
        is_valid, full_path, error = self._validate_path(relative_path)
        
        if not is_valid:
            return {"success": False, "error": error}
        
        if not full_path.exists():
            return {"success": False, "error": "File does not exist"}
        
        if full_path.is_dir():
            return {"success": False, "error": "Use directory delete for directories"}
        
        if not self._is_editable(full_path):
            return {"success": False, "error": "Cannot delete this file type"}
        
        try:
            full_path.unlink()
            log.info(f"File deleted: {relative_path}")
            return {"success": True, "path": relative_path}
            
        except Exception as e:
            return {"success": False, "error": f"Failed to delete file: {str(e)}"}
    
    def create_directory(self, relative_path: str) -> Dict[str, Any]:
        """
        Create a new directory.
        
        Args:
            relative_path: Path relative to project root
            
        Returns:
            Dict with success status or error
        """
        is_valid, full_path, error = self._validate_path(relative_path)
        
        if not is_valid:
            return {"success": False, "error": error}
        
        if full_path.exists():
            return {"success": False, "error": "Path already exists"}
        
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            log.info(f"Directory created: {relative_path}")
            return {
                "success": True,
                "path": relative_path,
                "type": "directory"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to create directory: {str(e)}"}
    
    def get_project_structure(self) -> Dict[str, Any]:
        """
        Get complete project structure as tree.
        
        Returns:
            Dict with tree structure
        """
        def build_tree(path: Path, current_depth: int = 0, max_depth: int = 10) -> Dict:
            if current_depth > max_depth:
                return {"name": path.name, "type": "directory", "truncated": True}
            
            result = {
                "name": path.name,
                "path": str(path.relative_to(self.project_root)),
                "type": "directory" if path.is_dir() else "file",
            }
            
            if path.is_dir():
                children = []
                try:
                    for item in sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                        # Skip blocked patterns and hidden files
                        if any(pattern in item.name for pattern in self.BLOCKED_PATTERNS):
                            continue
                        if item.name.startswith('.') and item.name != '.gitignore':
                            continue
                        
                        children.append(build_tree(item, current_depth + 1, max_depth))
                    
                    result["children"] = children
                except PermissionError:
                    result["error"] = "Permission denied"
            else:
                result["editable"] = self._is_editable(path)
                result["extension"] = path.suffix
            
            return result
        
        try:
            tree = build_tree(self.project_root)
            return {
                "success": True,
                "root": str(self.project_root),
                "tree": tree
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to build structure: {str(e)}"}
    
    def _detect_language(self, extension: str) -> str:
        """Detect programming language from file extension"""
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.md': 'markdown',
            '.sql': 'sql',
            '.sh': 'shell',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.xml': 'xml',
        }
        return language_map.get(extension.lower(), 'plaintext')
    
    def search_files(self, query: str, file_pattern: str = "*.py") -> Dict[str, Any]:
        """
        Search for text in files.
        
        Args:
            query: Search query string
            file_pattern: Glob pattern for files to search
            
        Returns:
            Dict with search results
        """
        if not query or len(query) < 2:
            return {"success": False, "error": "Query must be at least 2 characters"}
        
        results = []
        
        try:
            for file_path in self.project_root.rglob(file_pattern):
                # Skip blocked patterns
                if any(pattern in str(file_path) for pattern in self.BLOCKED_PATTERNS):
                    continue
                
                # Skip hidden files
                if any(part.startswith('.') for part in file_path.parts):
                    continue
                
                # Check if editable
                if not self._is_editable(file_path):
                    continue
                
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    if query.lower() in content.lower():
                        lines = content.split('\n')
                        matches = []
                        
                        for i, line in enumerate(lines, 1):
                            if query.lower() in line.lower():
                                matches.append({
                                    "line": i,
                                    "content": line.strip()[:100]  # Limit line length
                                })
                        
                        if matches:
                            results.append({
                                "path": str(file_path.relative_to(self.project_root)),
                                "matches": matches[:10]  # Limit matches per file
                            })
                except Exception:
                    continue
            
            return {
                "success": True,
                "query": query,
                "results": results[:50]  # Limit total results
            }
            
        except Exception as e:
            return {"success": False, "error": f"Search failed: {str(e)}"}


# Global instance
file_manager = SecureFileManager()
