import os
import json
import requests
import time
from datetime import datetime

class ZenodoPublisher:
    """Class to handle publishing datasets to Zenodo and obtaining DOIs."""
    
    def __init__(self, token=None, sandbox=True):
        """
        Initialize the Zenodo publisher.
        
        Args:
            token (str): Zenodo API token
            sandbox (bool): Whether to use Zenodo Sandbox (testing) environment
        """
        self.token = token or os.environ.get('ZENODO_TOKEN')
        if not self.token:
            raise ValueError("Zenodo API token is required. Set via constructor or ZENODO_TOKEN env variable.")
        
        self.base_url = "https://sandbox.zenodo.org/api" if sandbox else "https://zenodo.org/api"
        self.headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"}
    
    def create_or_update_deposit(self, csv_path, dataset_date, metadata=None,
                                 parsing_timestamp=None, code_path=None, raw_csv_path=None):
        """
        Create a new deposit or update an existing one on Zenodo.
        
        Args:
            csv_path (str): Path to the CSV file to upload
            dataset_date (str): Date string in YYYY_MM format
            metadata (dict): Additional metadata for the deposit
            parsing_timestamp (str): Timestamp when the data was parsed
            code_path (str): Path to the code file to upload
            raw_csv_path (str): Path to the raw CSV file to upload

        Returns:
            str: DOI for the deposit
        """
        # Format date for display
        try:
            year, month = dataset_date.split('_')
            formatted_date = datetime(int(year), int(month), 1).strftime('%B %Y')
        except:
            formatted_date = dataset_date
            
        # Default metadata
        default_metadata = {
            "title": f"EU Legislative Acts Statistics - {formatted_date}" + (f" (Parsed: {parsing_timestamp})" if parsing_timestamp else ""),
            "description": f"Monthly statistics of EU legislative acts for {formatted_date}." + (f" Parsed on {parsing_timestamp}." if parsing_timestamp else ""),
            "upload_type": "dataset",
            "creators": [{"name": "EurLex Legal Acts Statistics Project"}],
            "access_right": "open",
            "license": "cc-by",
            "keywords": ["EU", "legislation", "statistics", "legal acts", "EurLex"],
            "publication_date": datetime.now().strftime('%Y-%m-%d')
        }
        
        # Merge with user-provided metadata if any
        deposit_metadata = {**default_metadata, **(metadata or {})}
        
        # Create a new deposit
        r = requests.post(
            f"{self.base_url}/deposit/depositions",
            headers=self.headers,
            json={"metadata": deposit_metadata}
        )
        r.raise_for_status()
        
        deposit_data = r.json()
        deposit_id = deposit_data["id"]
        bucket_url = deposit_data["links"]["bucket"]
        
        # Upload the CSV file
        with open(csv_path, "rb") as file:
            filename = os.path.basename(csv_path)
            r = requests.put(
                f"{bucket_url}/{filename}",
                headers={"Authorization": f"Bearer {self.token}"},
                data=file
            )
            r.raise_for_status()
        
        # Upload the parsing code if provided
        if code_path and os.path.exists(code_path):
            with open(code_path, "rb") as file:
                filename = os.path.basename(code_path)
                r = requests.put(
                    f"{bucket_url}/{filename}",
                    headers={"Authorization": f"Bearer {self.token}"},
                    data=file
                )
                r.raise_for_status()

        # Upload the raw CSV file if provided
        if raw_csv_path and os.path.exists(raw_csv_path):
            with open(raw_csv_path, "rb") as file:
                filename = os.path.basename(raw_csv_path)
                r = requests.put(
                    f"{bucket_url}/{filename}",
                    headers={"Authorization": f'Bearer {self.token}'},
                    data=file
                )
                r.raise_for_status()

        # Publish the deposit
        r = requests.post(
            f"{self.base_url}/deposit/depositions/{deposit_id}/actions/publish",
            headers=self.headers
        )
        r.raise_for_status()
        
        # Return the DOI
        published_data = r.json()
        return published_data["doi"]
    
    def generate_citation(self, doi, authors=None, title=None, date=None):
        """
        Generate citation text for the dataset with the given DOI.
        
        Args:
            doi (str): DOI of the dataset
            authors (str): Author names, default from metadata
            title (str): Title, default from metadata
            date (str): Date, default from metadata
            
        Returns:
            dict: Citation information in different formats
        """
        # Get metadata from Zenodo if not provided
        if not all([authors, title, date]):
            r = requests.get(f"https://doi.org/{doi}", headers={"Accept": "application/json"})
            if r.ok:
                metadata = r.json()
                authors = authors or ", ".join([c.get("name", "") for c in metadata.get("creators", [])])
                title = title or metadata.get("title", "")
                date = date or metadata.get("publication_date", "")
        
        # Format into different citation styles
        apa = f"{authors}. ({date[:4]}). {title}. DOI: {doi}"
        mla = f"{authors}. \"{title}.\" {date[:4]}. DOI: {doi}"
        chicago = f"{authors}. {date[:4]}. \"{title}.\" DOI: {doi}"
        bibtex = f"""@dataset{{{doi.replace('/', '_')},
            title = {{{title}}},
            author = {{{authors}}},
            year = {{{date[:4]}}},
            publisher = {{Zenodo}},
            doi = {{{doi}}}
        }}"""
        
        return {
            "apa": apa,
            "mla": mla,
            "chicago": chicago,
            "bibtex": bibtex,
            "doi": doi
        }

