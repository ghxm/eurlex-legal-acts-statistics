import os
import pandas as pd
import glob
import re
import json
import argparse
from datetime import datetime
from jinja2 import Template, FileSystemLoader, Environment

def generate_stats_page(csv_path, output_dir):
    """Generate an HTML statistics page for a CSV file."""
    df = pd.read_csv(csv_path)
    
    # Extract parsing timestamp if available
    parsing_timestamp = None
    if 'parsing_date' in df.columns:
        parsing_timestamp = df['parsing_date'].iloc[0]
    
    # Extract filename without extension
    filename = os.path.basename(csv_path)
    base_name = os.path.splitext(filename)[0]
    
    # Check if metadata file exists
    metadata_path = csv_path.replace('.csv', '_metadata.json')
    doi_info = None
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            doi_info = json.load(f)
            # Get parsing timestamp from metadata if not in dataframe
            if not parsing_timestamp and 'parsing_timestamp' in doi_info:
                parsing_timestamp = doi_info['parsing_timestamp']
    
    # Extract date from filename (new format with parsing date)
    # Handle format: eurlex_legal_acts_statistics_YYYY_MM_parsed_YYYYMMDD.csv
    parts = base_name.split('_parsed_')
    stats_date_part = parts[0]
    parsing_date_part = parts[1] if len(parts) > 1 else None
    
    # Extract the year and month
    date_match = re.search(r'(\d{4})_(\d{2})', stats_date_part)
    if date_match:
        year, month = date_match.groups()
        period = f"{datetime(int(year), int(month), 1).strftime('%B %Y')}"
        
        if parsing_date_part:
            # Try to format the parsing date if possible
            try:
                parsing_date = datetime.strptime(parsing_date_part, '%Y%m%d')
                parsing_date_formatted = parsing_date.strftime('%Y-%m-%d')
                title = f"Legislative Acts Statistics - {period} (Parsed: {parsing_date_formatted})"
            except:
                title = f"Legislative Acts Statistics - {period} (Parsed: {parsing_date_part})"
        else:
            title = f"Legislative Acts Statistics - {period}"
            if parsing_timestamp:
                title += f" (Parsed: {parsing_timestamp})"
    else:
        title = f"Legislative Acts Statistics - {base_name}"
        period = base_name
    
    # Calculate summary statistics
    # ... existing code ...
    
    # Load and render the template with better template path handling
    # ... existing code ...
    
    return {
        'id': base_name,
        'title': title,
        'path': f"{base_name}.html",
        'date': date_match.groups() if date_match else None,
        'parsing_date': parsing_date_part or (parsing_timestamp if parsing_timestamp else None),
        'doi': doi_info['doi'] if doi_info else None,
        'csv_filename': filename,
        'parsing_timestamp': parsing_timestamp
    }

def generate_index_page(stats_files, output_dir):
    """Generate the main index.html page with links to all stats pages."""
    # Sort files by date (most recent first) and then by parsing date if available
    sorted_files = sorted(
        stats_files, 
        key=lambda x: (
            x['date'] is None, 
            x['date'] or (0, 0), 
            x['parsing_date'] or '0'
        ),
        reverse=True
    )
    
    # ... existing code ...
