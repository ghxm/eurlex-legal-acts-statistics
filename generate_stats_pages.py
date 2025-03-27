import os
import pandas as pd
import glob
import re
import json
import argparse
from datetime import datetime
from jinja2 import Template

# HTML Template for individual stats pages
STATS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }} - Legislative Acts Statistics</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        .container { max-width: 1200px; margin: 0 auto; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        h1, h2, h3 { color: #333; }
        .summary { background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .back-link { margin-bottom: 20px; }
        .citation { background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-top: 20px; }
        .citation pre { overflow-x: auto; background: #eee; padding: 10px; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="back-link">
            <a href="../index.html">← Back to main page</a>
        </div>
        
        <h1>{{ title }}</h1>
        <p>Data for: {{ period }}</p>
        
        {% if doi_info %}
        <div class="citation">
            <h2>Citation Information</h2>
            <p><strong>DOI:</strong> <a href="https://doi.org/{{ doi_info.doi }}" target="_blank">{{ doi_info.doi }}</a></p>
            
            <h3>APA Format</h3>
            <p>{{ doi_info.apa }}</p>
            
            <h3>MLA Format</h3>
            <p>{{ doi_info.mla }}</p>
            
            <h3>BibTeX</h3>
            <pre>{{ doi_info.bibtex }}</pre>
        </div>
        {% endif %}
        
        <div class="summary">
            <h2>Summary Statistics</h2>
            <p>Total number of acts: {{ total_acts }}</p>
            <p>Basic acts: {{ basic_acts }}</p>
            <p>Amending acts: {{ amending_acts }}</p>
        </div>
        
        <h2>Statistics by Year</h2>
        <table>
            <tr>
                <th>Year</th>
                <th>Basic Acts</th>
                <th>Amending Acts</th>
                <th>Total</th>
            </tr>
            {% for year, data in yearly_stats.items() %}
            <tr>
                <td>{{ year }}</td>
                <td>{{ data['basic'] }}</td>
                <td>{{ data['amending'] }}</td>
                <td>{{ data['total'] }}</td>
            </tr>
            {% endfor %}
        </table>
        
        <h2>Statistics by Category</h2>
        <table>
            <tr>
                <th>Category</th>
                <th>Basic Acts</th>
                <th>Amending Acts</th>
                <th>Total</th>
            </tr>
            {% for category, data in category_stats.items() %}
            <tr>
                <td>{{ category }}</td>
                <td>{{ data['basic'] }}</td>
                <td>{{ data['amending'] }}</td>
                <td>{{ data['total'] }}</td>
            </tr>
            {% endfor %}
        </table>
        
        <h2>Detailed Statistics</h2>
        <table>
            <tr>
                <th>Category</th>
                <th>Act Type</th>
                <th>Basic</th>
                <th>Amending</th>
                <th>Total</th>
            </tr>
            {% for category, types in detailed_stats.items() %}
                {% for act_type, counts in types.items() %}
                <tr>
                    <td>{{ category }}</td>
                    <td>{{ act_type }}</td>
                    <td>{{ counts['basic'] }}</td>
                    <td>{{ counts['amending'] }}</td>
                    <td>{{ counts['total'] }}</td>
                </tr>
                {% endfor %}
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

# HTML Template for the index page
INDEX_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Legislative Acts Data</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; line-height: 1.6; }
        .container { display: flex; height: 100vh; }
        .sidebar { width: 250px; background-color: #f8f9fa; padding: 20px; overflow-y: auto; }
        .main-content { flex-grow: 1; padding: 20px; overflow-y: auto; }
        .sidebar h2 { margin-top: 0; }
        .sidebar ul { padding-left: 0; list-style-type: none; }
        .sidebar li { margin-bottom: 8px; }
        .sidebar a { text-decoration: none; color: #007bff; }
        .sidebar a:hover { text-decoration: underline; }
        .current { font-weight: bold; }
        iframe { width: 100%; height: 100%; border: none; }
        .doi-link { font-size: 0.9em; margin-left: 5px; text-decoration: none; color: #0366d6; }
        .doi-link:hover { text-decoration: underline; }
        .doi-badge { display: inline-block; font-size: 0.8em; background: #f1f8ff; padding: 1px 6px; 
                    border-radius: 3px; border: 1px solid #c8e1ff; color: #0366d6; margin-left: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <h2>Legislative Acts Statistics</h2>
            <p>Monthly statistics of EU legislative acts.</p>
            <h3>Available Reports</h3>
            <ul id="stats-list">
                {% for file in stats_files %}
                <li>
                    <a href="#{{ file.id }}" class="stats-link" data-src="{{ file.path }}">{{ file.title }}</a>
                    {% if file.doi %}
                    <span class="doi-badge">DOI</span>
                    {% endif %}
                </li>
                {% endfor %}
            </ul>
            <p><a href="https://github.com/maxhaag/eurlex-legal-acts-statistics" target="_blank">GitHub Repository</a></p>
        </div>
        <div class="main-content">
            <iframe id="stats-frame" src="" style="display:none;"></iframe>
            <div id="no-selection" class="loading">
                <h2>EU Legislative Acts Statistics</h2>
                <p>Select a report from the sidebar to view detailed statistics.</p>
                {% if latest_file %}
                <p>Latest report: <a href="#{{ latest_file.id }}" class="stats-link" data-src="{{ latest_file.path }}">{{ latest_file.title }}</a></p>
                {% endif %}
            </div>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const frame = document.getElementById('stats-frame');
            const noSelection = document.getElementById('no-selection');
            const links = document.querySelectorAll('.stats-link');
            
            // Handle link clicks
            links.forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    const src = this.getAttribute('data-src');
                    frame.src = src;
                    frame.style.display = 'block';
                    noSelection.style.display = 'none';
                    
                    // Update URL hash
                    window.location.hash = this.getAttribute('href');
                    
                    // Mark current as active
                    links.forEach(l => l.classList.remove('current'));
                    this.classList.add('current');
                });
            });
            
            // Handle URL hash on load
            function handleHash() {
                const hash = window.location.hash;
                if(hash && hash.length > 1) {
                    const targetLink = document.querySelector(`a[href="${hash}"]`);
                    if(targetLink) {
                        targetLink.click();
                    }
                } else if(links.length > 0) {
                    // Load first report by default
                    links[0].click();
                }
            }
            
            handleHash();
            window.addEventListener('hashchange', handleHash);
        });
    </script>
</body>
</html>
"""

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
    
    # Render the template
    template = Template(STATS_TEMPLATE)
    html = template.render(
        title=title,
        period=period,
        total_acts=total_acts,
        basic_acts=basic_acts,
        amending_acts=amending_acts,
        yearly_stats=yearly_stats,
        category_stats=category_stats,
        detailed_stats=detailed_stats,
        doi_info=doi_info
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
        'doi': doi_info['doi'] if doi_info else None
    }

def generate_index_page(stats_files, output_dir):
    """Generate an index page for all statistics files."""
    # Sort stats files by date (newest first)
    stats_files.sort(key=lambda x: x['date'] if x['date'] else ('0000', '00'), reverse=True)
    
    # Get latest file
    latest_file = stats_files[0] if stats_files else None
    
    # Render the template
    template = Template(INDEX_TEMPLATE)
    html = template.render(stats_files=stats_files, latest_file=latest_file)
    
    # Write to HTML file
    with open(os.path.join(output_dir, 'index.html'), 'w') as f:
        f.write(html)

def main():
    """Main function to generate statistics pages."""
    parser = argparse.ArgumentParser(description='Generate HTML statistics pages from CSV files.')
    parser.add_argument('--input', '-i', default='cache', help='Directory containing CSV files')
    parser.add_argument('--output', '-o', default='stats_pages', help='Directory for generated statistics pages')
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Find all CSV files
    csv_files = glob.glob(os.path.join(args.input, '*.csv'))
    csv_files = [f for f in csv_files if not f.endswith('_metadata.csv')]
    
    if not csv_files:
        print(f"No CSV files found in {args.input}")
        return
    
    stats_files = []
    for csv_file in csv_files:
        try:
            stats_file = generate_stats_page(csv_file, args.output)
            stats_files.append(stats_file)
            print(f"Generated statistics page for {csv_file}")
        except Exception as e:
            print(f"Error generating statistics page for {csv_file}: {e}")
    
    # Generate index page
    generate_index_page(stats_files, args.output)
    print(f"Generated index page at {os.path.join(args.output, 'index.html')}")
    
    # Copy/update main index.html in root directory
    with open(os.path.join(args.output, 'index.html'), 'r') as src:
        with open('index.html', 'w') as dst:
            dst.write(src.read())
    print("Updated main index.html")

if __name__ == "__main__":
    main()
