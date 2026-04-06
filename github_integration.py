"""
GitHub Integration Module - Real Production Implementation
Enables actual GitHub API connections for repository management
"""

import os
import json
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests


class GitHubIntegration:
    """
    Production-ready GitHub API integration for repository management,
    code deployment, and CI/CD pipeline integration.
    """
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {self.token}" if self.token else None
        }
        if not self.token:
            self.headers.pop("Authorization", None)
    
    def is_authenticated(self) -> bool:
        """Check if GitHub token is valid and authenticated"""
        if not self.token:
            return False
        try:
            response = requests.get(f"{self.base_url}/user", headers=self.headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"GitHub authentication check failed: {e}")
            return False
    
    def get_user(self) -> Dict[str, Any]:
        """Get authenticated user information"""
        try:
            response = requests.get(f"{self.base_url}/user", headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "authenticated": False}
    
    def list_repositories(self, username: Optional[str] = None, 
                         type_: str = "owner",
                         sort: str = "updated",
                         direction: str = "desc",
                         per_page: int = 30) -> List[Dict]:
        """
        List repositories for a user or the authenticated user
        
        Args:
            username: GitHub username (None for authenticated user)
            type_: all, owner, member
            sort: created, updated, pushed, full_name
            direction: asc, desc
            per_page: Number of results (max 100)
        """
        try:
            if username:
                url = f"{self.base_url}/users/{username}/repos"
            else:
                url = f"{self.base_url}/user/repos"
            
            params = {
                "type": type_,
                "sort": sort,
                "direction": direction,
                "per_page": per_page
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return [{"error": str(e)}]
    
    def create_repository(self, name: str, 
                         description: str = "",
                         private: bool = False,
                         auto_init: bool = True,
                         gitignore_template: Optional[str] = None,
                         license_template: Optional[str] = None) -> Dict:
        """
        Create a new GitHub repository
        
        Args:
            name: Repository name
            description: Repository description
            private: Whether repository is private
            auto_init: Initialize with README
            gitignore_template: e.g., "Python", "Node"
            license_template: e.g., "mit", "apache-2.0"
        """
        if not self.token:
            return {"error": "Authentication required", "success": False}
        
        try:
            url = f"{self.base_url}/user/repos"
            data = {
                "name": name,
                "description": description,
                "private": private,
                "auto_init": auto_init
            }
            
            if gitignore_template:
                data["gitignore_template"] = gitignore_template
            if license_template:
                data["license_template"] = license_template
            
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            result["success"] = True
            return result
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 422:
                return {"error": "Repository already exists or invalid name", "success": False}
            return {"error": str(e), "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def get_repository(self, owner: str, repo: str) -> Dict:
        """Get detailed information about a repository"""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def update_repository(self, owner: str, repo: str, 
                         updates: Dict[str, Any]) -> Dict:
        """Update repository settings"""
        if not self.token:
            return {"error": "Authentication required", "success": False}
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}"
            response = requests.patch(url, headers=self.headers, json=updates, timeout=10)
            response.raise_for_status()
            result = response.json()
            result["success"] = True
            return result
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def delete_repository(self, owner: str, repo: str) -> Dict:
        """Delete a repository (requires admin access)"""
        if not self.token:
            return {"error": "Authentication required", "success": False}
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}"
            response = requests.delete(url, headers=self.headers, timeout=10)
            
            if response.status_code == 204:
                return {"success": True, "message": f"Repository {owner}/{repo} deleted"}
            else:
                return {"success": False, "error": f"Status code: {response.status_code}"}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def list_branches(self, owner: str, repo: str, protected_only: bool = False) -> List[Dict]:
        """List branches in a repository"""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/branches"
            params = {"protected": "true"} if protected_only else {}
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_file_contents(self, owner: str, repo: str, 
                         path: str, 
                         ref: Optional[str] = None) -> Dict:
        """
        Get contents of a file or directory
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File or directory path
            ref: Branch name, tag, or commit SHA
        """
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
            params = {}
            if ref:
                params["ref"] = ref
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Decode content if it's a file
            if isinstance(data, dict) and data.get("content"):
                import base64
                try:
                    data["decoded_content"] = base64.b64decode(data["content"].replace("\n", "")).decode('utf-8')
                except:
                    data["decoded_content"] = None
            
            return data
        except Exception as e:
            return {"error": str(e)}
    
    def create_or_update_file(self, owner: str, repo: str,
                              path: str,
                              message: str,
                              content: str,
                              branch: str = "main",
                              sha: Optional[str] = None) -> Dict:
        """
        Create or update a file in a repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            message: Commit message
            content: File content (plain text, will be base64 encoded)
            branch: Branch name
            sha: Required SHA of the file being replaced (for updates)
        """
        if not self.token:
            return {"error": "Authentication required", "success": False}
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
            
            # Encode content to base64
            encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            
            data = {
                "message": message,
                "content": encoded_content,
                "branch": branch
            }
            
            if sha:
                data["sha"] = sha
            
            response = requests.put(url, headers=self.headers, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            result["success"] = True
            return result
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def delete_file(self, owner: str, repo: str,
                   path: str,
                   message: str,
                   sha: str,
                   branch: str = "main") -> Dict:
        """Delete a file from a repository"""
        if not self.token:
            return {"error": "Authentication required", "success": False}
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
            data = {
                "message": message,
                "sha": sha,
                "branch": branch
            }
            
            response = requests.delete(url, headers=self.headers, json=data, timeout=10)
            response.raise_for_status()
            return {"success": True, "message": f"File {path} deleted"}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def create_pull_request(self, owner: str, repo: str,
                          title: str,
                          head: str,
                          base: str,
                          body: str = "",
                          draft: bool = False) -> Dict:
        """
        Create a pull request
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: PR title
            head: Branch with changes
            base: Branch to merge into
            body: PR description
            draft: Whether PR is a draft
        """
        if not self.token:
            return {"error": "Authentication required", "success": False}
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
            data = {
                "title": title,
                "head": head,
                "base": base,
                "body": body,
                "draft": draft
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            result["success"] = True
            return result
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def list_pull_requests(self, owner: str, repo: str,
                          state: str = "open",
                          sort: str = "created",
                          direction: str = "desc") -> List[Dict]:
        """List pull requests in a repository"""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
            params = {
                "state": state,
                "sort": sort,
                "direction": direction
            }
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return [{"error": str(e)}]
    
    def merge_pull_request(self, owner: str, repo: str,
                          pull_number: int,
                          commit_title: Optional[str] = None,
                          commit_message: Optional[str] = None,
                          sha: Optional[str] = None,
                          merge_method: str = "merge") -> Dict:
        """
        Merge a pull request
        
        Args:
            owner: Repository owner
            repo: Repository name
            pull_number: PR number
            commit_title: Custom commit title
            commit_message: Custom commit message
            sha: SHA that PR head must match
            merge_method: merge, squash, or rebase
        """
        if not self.token:
            return {"error": "Authentication required", "success": False}
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}/merge"
            data = {"merge_method": merge_method}
            
            if commit_title:
                data["commit_title"] = commit_title
            if commit_message:
                data["commit_message"] = commit_message
            if sha:
                data["sha"] = sha
            
            response = requests.put(url, headers=self.headers, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            result["success"] = True
            return result
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def create_webhook(self, owner: str, repo: str,
                      config: Dict[str, str],
                      events: List[str],
                      active: bool = True) -> Dict:
        """
        Create a repository webhook
        
        Args:
            owner: Repository owner
            repo: Repository name
            config: {"url": "...", "content_type": "json", "secret": "..."}
            events: List of events to subscribe to (push, pull_request, etc.)
            active: Whether webhook is active
        """
        if not self.token:
            return {"error": "Authentication required", "success": False}
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/hooks"
            data = {
                "config": config,
                "events": events,
                "active": active
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            result["success"] = True
            return result
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def get_commit_history(self, owner: str, repo: str,
                          sha: Optional[str] = None,
                          path: Optional[str] = None,
                          author: Optional[str] = None,
                          since: Optional[str] = None,
                          until: Optional[str] = None,
                          per_page: int = 30) -> List[Dict]:
        """Get commit history for a repository"""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/commits"
            params = {"per_page": per_page}
            
            if sha:
                params["sha"] = sha
            if path:
                params["path"] = path
            if author:
                params["author"] = author
            if since:
                params["since"] = since
            if until:
                params["until"] = until
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_rate_limit(self) -> Dict:
        """Get current rate limit status"""
        try:
            url = f"{self.base_url}/rate_limit"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def search_repositories(self, query: str,
                           sort: str = "stars",
                           order: str = "desc",
                           per_page: int = 30) -> Dict:
        """Search for repositories on GitHub"""
        try:
            url = f"{self.base_url}/search/repositories"
            params = {
                "q": query,
                "sort": sort,
                "order": order,
                "per_page": per_page
            }
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def fork_repository(self, owner: str, repo: str,
                       organization: Optional[str] = None,
                       name: Optional[str] = None,
                       default_branch_only: bool = False) -> Dict:
        """Fork a repository"""
        if not self.token:
            return {"error": "Authentication required", "success": False}
        
        try:
            if organization:
                url = f"{self.base_url}/repos/{owner}/{repo}/forks"
                data = {"organization": organization}
            else:
                url = f"{self.base_url}/repos/{owner}/{repo}/forks"
                data = {}
            
            if name:
                data["name"] = name
            if default_branch_only:
                data["default_branch_only"] = True
            
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            result["success"] = True
            return result
        except Exception as e:
            return {"error": str(e), "success": False}


# Global instance
github_integration = GitHubIntegration()


def get_github_status() -> Dict[str, Any]:
    """Get current GitHub integration status"""
    is_auth = github_integration.is_authenticated()
    
    status = {
        "connected": is_auth,
        "authenticated": is_auth,
        "api_version": "v3",
        "features": [
            "repository_management",
            "file_operations",
            "pull_requests",
            "webhooks",
            "commit_history"
        ] if is_auth else [],
        "rate_limit": None
    }
    
    if is_auth:
        rate_limit = github_integration.get_rate_limit()
        if "resources" in rate_limit:
            core = rate_limit["resources"].get("core", {})
            status["rate_limit"] = {
                "limit": core.get("limit"),
                "remaining": core.get("remaining"),
                "reset": core.get("reset"),
                "used": core.get("used")
            }
    
    return status


def deploy_website_to_github(owner: str, repo: str, 
                             website_files: Dict[str, str],
                             branch: str = "main",
                             commit_message: str = "Deploy website") -> Dict:
    """
    Deploy generated website files to GitHub repository
    
    Args:
        owner: GitHub username or organization
        repo: Repository name
        website_files: Dict mapping file paths to content
        branch: Branch to deploy to
        commit_message: Commit message
    
    Returns:
        Deployment status and URLs
    """
    if not github_integration.is_authenticated():
        return {
            "success": False,
            "error": "GitHub authentication required. Set GITHUB_TOKEN environment variable.",
            "setup_instructions": [
                "1. Create a GitHub personal access token at https://github.com/settings/tokens",
                "2. Set GITHUB_TOKEN environment variable",
                "3. Restart the application"
            ]
        }
    
    results = {
        "success": True,
        "files_deployed": [],
        "files_updated": [],
        "errors": []
    }
    
    for file_path, content in website_files.items():
        # Check if file exists to get SHA for update
        existing = github_integration.get_file_contents(owner, repo, file_path, ref=branch)
        sha = existing.get("sha") if "sha" in existing else None
        
        result = github_integration.create_or_update_file(
            owner=owner,
            repo=repo,
            path=file_path,
            message=f"{commit_message}: {file_path}",
            content=content,
            branch=branch,
            sha=sha
        )
        
        if result.get("success"):
            if sha:
                results["files_updated"].append(file_path)
            else:
                results["files_deployed"].append(file_path)
        else:
            results["errors"].append({"file": file_path, "error": result.get("error")})
    
    # Check if any files failed
    if results["errors"] and not (results["files_deployed"] or results["files_updated"]):
        results["success"] = False
    
    # Add GitHub Pages URL if repository exists
    repo_info = github_integration.get_repository(owner, repo)
    if "html_url" in repo_info:
        results["repository_url"] = repo_info["html_url"]
        # GitHub Pages URL (if enabled)
        results["github_pages_url"] = f"https://{owner}.github.io/{repo}"
    
    return results


# Example usage and testing
if __name__ == "__main__":
    # Test authentication
    print("Testing GitHub Integration...")
    print(f"Authenticated: {github_integration.is_authenticated()}")
    
    if github_integration.is_authenticated():
        user = github_integration.get_user()
        print(f"User: {user.get('login')}")
        print(f"Rate Limit: {github_integration.get_rate_limit()}")
