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
    
    if input_path.startswith('http://') or input_path.startswith('https://'):
        response = requests.get(input_path)
        response.raise_for_status()
        df_raw = pd.read_csv(StringIO(response.text), header=None)
    else:
        df_raw = pd.read_csv(input_path, header=None)

    data = []
    current_year = None
    current_month = None
    current_category = None
    type_continues = False

    for idx, row in df_raw.iterrows():
        if pd.notna(row[0]) and "Statistics for" in row[0]:
            current_year = row[1]
            current_month = row[2]
            current_category = None
            type_continues = False
            continue

        if pd.notna(row[0]) and pd.isna(row[1]) and pd.isna(row[2]) and "Total" not in row[0]:
            if type_continues:
                current_category += " - " + row[0]
            else:
                current_category = row[0]
            type_continues = True
            continue

        if pd.isna(row[0]) and pd.isna(row[1]) and pd.isna(row[2]):
            current_category = None
            type_continues = False
            continue

        if pd.notna(row[1]) and "Total" in row[1]:
            continue

        if current_year and current_month and current_category and pd.notna(row[0]) and pd.notna(row[1]) and pd.notna(row[2]):
            act_type = row[0]
            basic_count = pd.to_numeric(row[1], errors='coerce')
            amending_count = pd.to_numeric(row[2], errors='coerce') if len(row) > 2 else 0

            data.append({'year': current_year, 'month': current_month, 'category': current_category,
                         'act_type': act_type, 'type': 'basic', 'count': basic_count})
            data.append({'year': current_year, 'month': current_month, 'category': current_category,
                         'act_type': act_type, 'type': 'amending', 'count': amending_count})

            type_continues = False

    df_final = pd.DataFrame(data)
    df_final = df_final[df_final['act_type'] != 'Total'].reset_index(drop=True)
    
    # Add parsing timestamp to the dataframe
    df_final['parsing_date'] = parsing_timestamp
    
    df_final.to_csv(output_path, index=False)
    
    # Generate DOI if requested
    doi_info = None
    if generate_doi:
        try:
            from zenodo_publisher import ZenodoPublisher
            
            # Extract date from filename (assuming format like 'legislative_acts_2023_05.csv')
            filename = os.path.basename(output_path)
            date_match = filename.replace('eurlex_legal_acts_statistics_', '').replace('.csv', '')
            
            # Format date for display
            try:
                year, month = date_match.split('_')
                formatted_date = datetime(int(year), int(month), 1).strftime('%B %Y')
            except:
                formatted_date = date_match
            
            # Include parsing timestamp in metadata
            if metadata is None:
                metadata = {}
            
            # Add parsing timestamp to description if not explicitly provided
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
            date_match = filename.replace('eurlex_legal_acts_statistics_', '').replace('.csv', '')
            
            # Format date for display
            try:
                year, month = date_match.split('_')
                formatted_date = datetime(int(year), int(month), 1).strftime('%B %Y')
            except:
                formatted_date = date_match
            
            # Create tag name and release title
            tag_name = f"dataset-{date_match}"
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
    parser.add_argument('--input', required=True, help='Input CSV file path or URL')
    parser.add_argument('--output', required=True, help='Output CSV file path')
    parser.add_argument('--generate-doi', action='store_true', help='Generate a DOI for the dataset using Zenodo')
    parser.add_argument('--zenodo-token', help='Zenodo API token (or set ZENODO_TOKEN env variable)')
    parser.add_argument('--production', action='store_true', help='Use Zenodo production instead of sandbox')
    
    # GitHub Release arguments
    parser.add_argument('--create-github-release', action='store_true', help='Create a GitHub release for the dataset')
    parser.add_argument('--github-token', help='GitHub API token (or set GITHUB_TOKEN env variable)')
    parser.add_argument('--github-repo-owner', help='GitHub repository owner (automatically detected in GitHub Actions)')
    parser.add_argument('--github-repo-name', help='GitHub repository name (automatically detected in GitHub Actions)')
    
    # Metadata arguments
    parser.add_argument('--authors', help='Authors/creators of the dataset (comma-separated)')
    parser.add_argument('--title', help='Custom title for the dataset')
    parser.add_argument('--description', help='Custom description for the dataset')
    parser.add_argument('--keywords', help='Keywords for the dataset (comma-separated)')
    parser.add_argument('--license', help='License for the dataset (default: cc-by)')
    
    args = parser.parse_args()

    # Prepare metadata dictionary
    metadata = {}
    if args.authors:
        metadata['creators'] = [{"name": name.strip()} for name in args.authors.split(',')]
    if args.title:
        metadata['title'] = args.title
    if args.description:
        metadata['description'] = args.description
    if args.keywords:
        metadata['keywords'] = [keyword.strip() for keyword in args.keywords.split(',')]
    if args.license:
        metadata['license'] = args.license

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

