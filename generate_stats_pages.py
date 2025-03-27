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
    
    # Extract filename without extension
    filename = os.path.basename(csv_path)
    base_name = os.path.splitext(filename)[0]
    
    # Check if metadata file exists
    metadata_path = csv_path.replace('.csv', '_metadata.json')
    doi_info = None
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            doi_info = json.load(f)
    
    # Extract date from filename (assuming format like 'eurlex_legal_acts_statistics_2023_05.csv')
    date_match = re.search(r'(\d{4})_(\d{2})', base_name)
    if date_match:
        year, month = date_match.groups()
        title = f"Legislative Acts Statistics - {datetime(int(year), int(month), 1).strftime('%B %Y')}"
        period = f"{datetime(int(year), int(month), 1).strftime('%B %Y')}"
    else:
        title = f"Legislative Acts Statistics - {base_name}"
        period = base_name
    
    # Calculate summary statistics
    total_acts = df['count'].sum()
    basic_acts = df[df['type'] == 'basic']['count'].sum()
    amending_acts = df[df['type'] == 'amending']['count'].sum()
    
    # Calculate yearly statistics
    yearly_stats = {}
    for year in df['year'].unique():
        year_df = df[df['year'] == year]
        yearly_stats[year] = {
            'basic': year_df[year_df['type'] == 'basic']['count'].sum(),
            'amending': year_df[year_df['type'] == 'amending']['count'].sum(),
            'total': year_df['count'].sum()
        }
    
    # Calculate category statistics
    category_stats = {}
    for category in df['category'].unique():
        cat_df = df[df['category'] == category]
        category_stats[category] = {
            'basic': cat_df[cat_df['type'] == 'basic']['count'].sum(),
            'amending': cat_df[cat_df['type'] == 'amending']['count'].sum(),
            'total': cat_df['count'].sum()
        }
    
    # Calculate detailed statistics
    detailed_stats = {}
    for category in df['category'].unique():
        detailed_stats[category] = {}
        cat_df = df[df['category'] == category]
        for act_type in cat_df['act_type'].unique():
            act_df = cat_df[cat_df['act_type'] == act_type]
            detailed_stats[category][act_type] = {
                'basic': act_df[act_df['type'] == 'basic']['count'].sum(),
                'amending': act_df[act_df['type'] == 'amending']['count'].sum(),
                'total': act_df['count'].sum()
            }
    
    # Load and render the template
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'stats_page.html')
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    template = Template(template_content)
    html = template.render(
        title=title,
        period=period,
        total_acts=total_acts,
        basic_acts=basic_acts,
        amending_acts=amending_acts,
        yearly_stats=yearly_stats,
        category_stats=category_stats,
        detailed_stats=detailed_stats,
        doi_info=doi_info,
        csv_filename=filename  # Pass the CSV filename to the template
    )
    
    # Write to HTML file
    output_filename = os.path.join(output_dir, f"{base_name}.html")
    with open(output_filename, 'w') as f:
        f.write(html)
    
    return {
        'id': base_name,
        'title': title,
        'path': f"{base_name}.html",
        'date': date_match.groups() if date_match else None,
        'doi': doi_info['doi'] if doi_info else None,
        'csv_filename': filename  # Include the CSV filename in the returned data
    }

# Rest of the file remains unchanged
