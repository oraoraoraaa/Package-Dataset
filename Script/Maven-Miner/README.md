# Maven Central Package Miner

This tool mines Maven Central Repository to collect information about all Maven artifacts.

## Features

- Fetches complete list of Maven artifacts from Maven Central Search API
- Retrieves artifact metadata by parsing POM (Project Object Model) files
- Parallel processing with 30 workers for efficient POM file parsing
- Extracts homepage and repository URLs from POM XML
- Progress tracking with visual feedback
- Outputs to CSV format compatible with cross-ecosystem analysis

## Setup

### Run the setup script

```bash
chmod +x setup.sh
./setup.sh
```

This will:

- Create a virtual environment
- Install required dependencies (requests, tqdm)

### Manual Setup (Alternative)

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
source .venv/bin/activate
python mine_maven.py
```

The script will:

1. Query Maven Central Search API to get total artifact count
2. Download all artifact metadata in batches of 1000
3. Fetch and parse POM files for each artifact to extract URLs
4. Save results to `../../../Resource/Package/Package-List/Maven.csv`

## Output Format

CSV file with columns:

- `ID`: Sequential artifact identifier
- `Platform`: "Maven"
- `Name`: Artifact identifier in format `groupId:artifactId`
- `Homepage URL`: Project URL (from POM `<url>` element)
- `Repository URL`: Source code repository URL (from POM `<scm><url>` element)

## Data Source

- **Search API**: https://search.maven.org/solrsearch/select
- **Repository**: https://repo1.maven.org/maven2/
- **POM files**: Retrieved from Maven Central Repository

## POM Parsing

The script parses POM XML files to extract:

- `<url>` element for homepage URL
- `<scm><url>` element for repository URL

Both namespaced and non-namespaced XML elements are handled.

## Performance

- Expected runtime: 20-40 hours for millions of artifacts
- Batch size: 1000 artifacts per API request
- 30 parallel workers for POM file fetching
- Small delays between API requests to avoid overwhelming the server
- Network-dependent (typically limited by POM file availability and network speed)

## Notes

- Maven Central contains millions of artifacts (3M+)
- Not all artifacts have POM files with URL information
- Repository URLs are validated to start with http/https
- Missing or invalid URLs are marked as "nan"
- The script handles API errors and malformed POM files gracefully
- Progress is saved incrementally to avoid data loss on interruption
