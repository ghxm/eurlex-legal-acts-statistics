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
    
    # Load and render the template with better template path handling
    env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))
    template = env.get_template('stats_page.html')
    
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
        csv_filename=filename,
        parsing_timestamp=parsing_timestamp
    )
    
    # Write to HTML file
    output_filename = os.path.join(output_dir, f"{base_name}.html")
    with open(output_filename, 'w') as f:
        f.write(html)
    
    return {
        'id': base_name,
        'title': title,
        'path': f"stats_pages/{base_name}.html",  # Include the directory in path
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
    
    # Load the template
    env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))
    template = env.get_template('index.html')
    
    # Render the template
    html = template.render(stats_files=sorted_files)
    
    # Write to HTML file
    output_filename = os.path.join(output_dir, 'index.html')
    with open(output_filename, 'w') as f:
        f.write(html)
    
    # Also write to project root for GitHub Pages
    root_index_path = os.path.join(os.path.dirname(__file__), 'index.html')
    with open(root_index_path, 'w') as f:
        f.write(html)
    
    return output_filename

def main():
    """Main function to generate all statistics pages."""
    parser = argparse.ArgumentParser(description='Generate statistics pages from CSV files.')
    parser.add_argument('--input', '-i', default='cache', help='Directory containing CSV files')
    parser.add_argument('--output', '-o', default='stats_pages', help='Directory for output HTML files')
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Find all CSV files
    csv_files = glob.glob(os.path.join(args.input, '*.csv'))
    
    # Filter out metadata files
    csv_files = [f for f in csv_files if not f.endswith('_metadata.csv')]
    
    # Generate a stats page for each CSV file
    stats_files = []
    for csv_file in csv_files:
        try:
            stats_file = generate_stats_page(csv_file, args.output)
            stats_files.append(stats_file)
            print(f"Generated stats page for {csv_file}")
        except Exception as e:
            print(f"Error generating stats page for {csv_file}: {e}")
    
    # Generate the index page
    index_path = generate_index_page(stats_files, args.output)
    print(f"Generated index page at {index_path}")

if __name__ == '__main__':
    main()

