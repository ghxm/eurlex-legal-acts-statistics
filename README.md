
# EUR-Lex Legal Acts Statistics

This project parses [legal acts statistics from EUR-Lex](https://eur-lex.europa.eu/statistics/legislative-acts-statistics.html)[^1] and provides monthly updated CSV files with visualized statistics pages.

[^1]: The statistics are already compiled by EUR-Lex just not provided in a format that is easily digestible.

> [!NOTE]
> While this project also has a useful purpose, it is mainly used to explore the automated data collection and processing. The project is not affiliated with EUR-Lex or the European Union.


## Setup

### Parse data

Run the CLI script to parse raw data:

```bash
python parse_legal_acts_statistics.py --input "<input_csv>" --output "cache/<output_csv>"
```

#### Making Datasets Citeable with DOIs

You can optionally generate a DOI (Digital Object Identifier) for each dataset using Zenodo:

```bash
python parse_legal_acts_statistics.py --input "<input_csv>" --output "cache/<output_csv>" --generate-doi --zenodo-token "YOUR_ZENODO_TOKEN"
```

CLI arguments for DOI generation:
- `--generate-doi`: Enable DOI generation via Zenodo
- `--zenodo-token`: Your Zenodo API token (can also be set via ZENODO_TOKEN environment variable)
- `--production`: Use Zenodo production environment instead of sandbox (default is sandbox for testing)

#### Creating GitHub Releases for Datasets

You can create GitHub releases for each dataset:

```bash
python parse_legal_acts_statistics.py --input "<input_csv>" --output "cache/<output_csv>" --create-github-release --github-token "YOUR_GITHUB_TOKEN"
```

CLI arguments for GitHub releases:
- `--create-github-release`: Enable creating a GitHub release
- `--github-token`: Your GitHub API token (can also be set via GITHUB_TOKEN environment variable)
- `--github-repo-owner`: GitHub repository owner (automatically detected in GitHub Actions)
- `--github-repo-name`: GitHub repository name (automatically detected in GitHub Actions)

#### Customizing Metadata

You can customize the metadata associated with your dataset (used for both DOIs and GitHub releases):

```bash
python parse_legal_acts_statistics.py --input "<input_csv>" --output "cache/<output_csv>" --generate-doi --zenodo-token "YOUR_ZENODO_TOKEN" --create-github-release --github-token "YOUR_GITHUB_TOKEN" --authors "Jane Doe, John Smith" --title "My Custom Dataset Title" --description "A detailed description of this dataset"
```

Available metadata options:
- `--authors`: Comma-separated list of dataset authors/creators
- `--title`: Custom title for the dataset
- `--description`: Custom description of the dataset
- `--keywords`: Comma-separated keywords (default: "EU, legislation, statistics, legal acts, EurLex")
- `--license`: Dataset license (default: cc-by)

When a DOI is generated, a metadata file with citation information is created alongside the CSV file.

### Generate statistics pages

Generate HTML pages with visualized statistics:

```bash
python generate_stats_pages.py --input "cache" --output "stats_pages"
```

CLI arguments:
- `--input` or `-i`: Directory containing CSV files (default: cache)
- `--output` or `-o`: Directory for generated statistics pages (default: stats_pages)

If a dataset has a DOI, the statistics page will include citation information in various formats (APA, MLA, BibTeX).

## Automated updates

Updates are automated monthly via GitHub Actions:
- Raw data is parsed and stored in the `cache` folder
- Statistics pages are generated in the `stats_pages` folder
- The main webpage is updated to display the latest statistics
- If ZENODO_TOKEN is configured as a repository secret, DOIs will be generated automatically
- GitHub releases are created for each dataset automatically

## Webpage

Access the statistics in two ways:
1. View and download raw data files from the `cache` folder
2. Browse interactive statistics pages that show summaries by year, category, and more

Open `index.html` in your browser to view the latest statistics.
