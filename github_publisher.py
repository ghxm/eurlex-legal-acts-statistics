import os
import requests
from datetime import datetime
import base64

class GitHubPublisher:
    """Class to handle publishing datasets as GitHub releases."""
    
    def __init__(self, token=None, repo_owner=None, repo_name=None):
        """
        Initialize the GitHub publisher.
        
        Args:
            token (str): GitHub API token
            repo_owner (str): GitHub repository owner
            repo_name (str): GitHub repository name
        """
        self.token = token or os.environ.get('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token is required. Set via constructor or GITHUB_TOKEN env variable.")
        
        self.repo_owner = repo_owner or os.environ.get('GITHUB_REPOSITORY_OWNER')
        self.repo_name = repo_name or os.environ.get('GITHUB_REPOSITORY', '').split('/')[-1]
        
        if not self.repo_owner or not self.repo_name:
            # Try to extract from environment
            if os.environ.get('GITHUB_REPOSITORY'):
                parts = os.environ.get('GITHUB_REPOSITORY').split('/')
                if len(parts) == 2:
                    self.repo_owner = parts[0]
                    self.repo_name = parts[1]
            
            if not self.repo_owner or not self.repo_name:
                raise ValueError("Repository owner and name are required")
        
        self.base_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    def create_release(self, tag_name, csv_path=None, title=None, body=None, draft=False, prerelease=False, doi=None, additional_files=None):
        """
        Create a new GitHub release for a dataset.
        
        Args:
            tag_name (str): Tag name for the release
            csv_path (str, optional): Path to CSV file to attach to the release
            title (str, optional): Release title
            body (str, optional): Release description
            draft (bool): Whether this is a draft release
            prerelease (bool): Whether this is a pre-release
            doi (str, optional): DOI to include in release notes
            additional_files (list, optional): List of additional file paths to attach to the release
            
        Returns:
            dict: Release data from GitHub API
        """
        # Default release details
        if not title:
            title = f"Dataset Release: {tag_name}"
        
        if not body:
            body = f"Dataset release created on {datetime.now().strftime('%Y-%m-%d')}"
        
        # Add DOI information if available
        if doi:
            body += f"\n\n## Digital Object Identifier\n\nThis dataset is also available with DOI: [{doi}](https://doi.org/{doi})"
        
        # Create the release
        payload = {
            "tag_name": tag_name,
            "name": title,
            "body": body,
            "draft": draft,
            "prerelease": prerelease
        }
        
        response = requests.post(
            f"{self.base_url}/releases",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        release_data = response.json()
        
        # Upload asset if provided
        if csv_path and os.path.exists(csv_path):
            self._upload_asset(release_data["upload_url"], csv_path)
        
        if additional_files:
            for f in additional_files:
                if f and os.path.exists(f):
                    self._upload_asset(release_data["upload_url"], f)
        
        return release_data
    
    def _upload_asset(self, upload_url, file_path):
        """
        Upload an asset to a GitHub release.
        
        Args:
            upload_url (str): GitHub upload URL for the release
            file_path (str): Path to the file to upload
        """
        filename = os.path.basename(file_path)
        # Remove the {?name,label} template parameter
        upload_url = upload_url.split("{")[0] + f"?name={filename}"
        
        with open(file_path, "rb") as file:
            headers = {**self.headers, "Content-Type": "application/octet-stream"}
            response = requests.post(
                upload_url,
                headers=headers,
                data=file
            )
            response.raise_for_status()
        
        return response.json()
