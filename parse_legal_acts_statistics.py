import pandas as pd
import argparse
import os
import requests
import json
from io import StringIO
from datetime import datetime

def parse_csv(input_path, output_path, generate_doi=False, zenodo_token=None, sandbox=True, metadata=None, 
             create_github_release=False, github_token=None, github_repo_owner=None, github_repo_name=None):
    # Record parsing timestamp
    parsing_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    parsing_date_compact = datetime.now().strftime('%Y%m%d')
    
    # Modify output path to include parsing date if not already included
    if '_parsed_' not in output_path:
        output_path = output_path.replace('.csv', f'_parsed_{parsing_date_compact}.csv')
    
    if input_path.startswith('http://') or input_path.startswith('https://'):
        response = requests.get(input_path)
        response.raise_for_status()
        df_raw = pd.read_csv(StringIO(response.text), header=None)
    else:
        df_raw = pd.read_csv(input_path, header=None)

    # ... existing code ...

    # Add parsing timestamp to the dataframe
    df_final['parsing_date'] = parsing_timestamp
    
    df_final.to_csv(output_path, index=False)
    
    # Generate DOI if requested
    doi_info = None
    if generate_doi:
        try:
            from zenodo_publisher import ZenodoPublisher
            
            # Extract date from filename
            filename = os.path.basename(output_path)
            date_match = filename.replace('eurlex_legal_acts_statistics_', '').split('_parsed_')[0]
            
            # Format date for display
            try:
                year, month = date_match.split('_')
                formatted_date = datetime(int(year), int(month), 1).strftime('%B %Y')
            except:
                formatted_date = date_match
            
            # Include parsing timestamp in metadata
            if metadata is None:
                metadata = {}
            
            # Add parsing timestamp to title and description
            if 'title' not in metadata:
                metadata['title'] = f"EU Legislative Acts Statistics - {formatted_date} (Parsed: {parsing_timestamp})"
            elif 'Parsed:' not in metadata['title']:
                metadata['title'] += f" (Parsed: {parsing_timestamp})"
                
            if 'description' not in metadata:
                metadata['description'] = f"Monthly statistics of EU legislative acts for {formatted_date}. Parsed on {parsing_timestamp}."
            elif 'Parsed on' not in metadata['description']:
                metadata['description'] += f" Parsed on {parsing_timestamp}."
            
            # Create publisher and publish dataset
            publisher = ZenodoPublisher(token=zenodo_token, sandbox=sandbox)
            doi = publisher.create_or_update_deposit(
                csv_path=output_path,
                dataset_date=date_match,
                metadata=metadata,
                parsing_timestamp=parsing_timestamp
            )
            
            # Generate citation information
            doi_info = publisher.generate_citation(doi)
            
            # Save DOI info to metadata file alongside the CSV
            metadata_path = output_path.replace('.csv', '_metadata.json')
            
            # Add parsing timestamp to the metadata file
            doi_info['parsing_timestamp'] = parsing_timestamp
            
            with open(metadata_path, 'w') as f:
                json.dump(doi_info, f, indent=2)
                
            print(f"DOI generated: {doi}")
            print(f"Citation metadata saved to: {metadata_path}")
        except Exception as e:
            print(f"Error generating DOI: {e}")
    
    # Create GitHub Release if requested
    if create_github_release:
        try:
            from github_publisher import GitHubPublisher
            
            # Extract date from filename
            filename = os.path.basename(output_path)
            date_parts = filename.replace('eurlex_legal_acts_statistics_', '').split('_parsed_')
            dataset_date = date_parts[0]
            parsing_date = date_parts[1].replace('.csv', '') if len(date_parts) > 1 else parsing_date_compact
            
            # Format date for display
            try:
                year, month = dataset_date.split('_')
                formatted_date = datetime(int(year), int(month), 1).strftime('%B %Y')
            except:
                formatted_date = dataset_date
            
            # Create tag name and release title that include parsing date
            tag_name = f"dataset-{dataset_date}-parsed-{parsing_date}"
            title = metadata.get('title') if metadata else f"EU Legislative Acts Statistics - {formatted_date} (Parsed: {parsing_timestamp})"
            
            # Create release body with description
            description = metadata.get('description') if metadata else f"Monthly statistics of EU legislative acts for {formatted_date}. Parsed on {parsing_timestamp}."
            body = f"{description}\n\nThis dataset contains legislative acts statistics from EUR-Lex for {formatted_date}. The data was parsed on {parsing_timestamp}."
            
            # Create publisher and publish release
            publisher = GitHubPublisher(
                token=github_token,
                repo_owner=github_repo_owner,
                repo_name=github_repo_name
            )
            
            # Create the GitHub release (including DOI if available)
            release_data = publisher.create_release(
                tag_name=tag_name,
                csv_path=output_path,
                title=title,
                body=body,
                doi=doi_info['doi'] if doi_info else None
            )
            
            print(f"GitHub Release created: {release_data['html_url']}")
        except Exception as e:
            print(f"Error creating GitHub Release: {e}")
    
    # Return both DOI info and parsing timestamp
    return doi_info, parsing_timestamp

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse legislative acts CSV file from local file or URL.')
    # ... existing code ...

    args = parser.parse_args()

    # Get current datetime for filename
    current_datetime = datetime.now().strftime('%Y%m%d')
    
    # Update output path to include parsing date if not specified
    if args.output and '_parsed_' not in args.output:
        args.output = args.output.replace('.csv', f'_parsed_{current_datetime}.csv')

    # Prepare metadata dictionary
    # ... existing code ...

    doi_info, parsing_timestamp = parse_csv(
        args.input, 
        args.output,
        generate_doi=args.generate_doi,
        zenodo_token=args.zenodo_token,
        sandbox=not args.production,
        metadata=metadata if metadata else None,
        create_github_release=args.create_github_release,
        github_token=args.github_token,
        github_repo_owner=args.github_repo_owner,
        github_repo_name=args.github_repo_name
    )
    print(f"Parsed data from {args.input} and saved to {args.output}")
    print(f"Parsing timestamp: {parsing_timestamp}")
