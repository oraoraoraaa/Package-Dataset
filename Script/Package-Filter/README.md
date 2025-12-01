# Cross-Ecosystem Package Finder

This tool identifies packages that are developed across multiple package ecosystems (Maven, NPM, PyPI, Crates, Go, PHP, and Ruby) by analyzing package metadata and GitHub repository URLs.

## Features

- Identifies packages published across multiple ecosystems (Maven, NPM, PyPI, Crates, Go, PHP, Ruby)
- Repository-based matching: identifies packages by matching GitHub repository URLs
- Automatic repository deduplication to avoid duplicate entries within same ecosystem combination
- **NEW**: Cross-ecosystem-count deduplication - packages appearing in higher ecosystem counts are removed from lower counts
- **NEW**: Automatic categorization of results by ecosystem count (2 ecosystems, 3 ecosystems, etc.)
- **NEW**: Summary file generation with statistics
- Generates CSV files for all possible ecosystem combinations
- Fast hash-based lookup algorithm for efficient processing
- GitHub URL normalization for consistent matching
- Progress tracking with visual feedback
- Handles split package lists (e.g., Go split into 6 parts)

## Setup

### Run the setup script

```bash
chmod +x setup.sh
./setup.sh
```

This will:

- Create a virtual environment
- Install required dependencies (pandas, tqdm)
- Create the results directory

### Manual Setup (Alternative)

If you prefer to set up manually:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Important**: Virtual environments contain hardcoded paths and **cannot be moved** after creation. If you need to relocate this script:

1. Delete the `.venv` folder
2. Recreate it in the new location
3. Reinstall the packages

## Usage

Process all input CSV files and generate cross-ecosystem package lists:

```bash
source .venv/bin/activate
python find_cross_ecosystem_packages.py
```

Or run directly without activating:

```bash
.venv/bin/python find_cross_ecosystem_packages.py
```

The script will:

1. Load package data from input CSV files
2. Normalize package names and GitHub URLs
3. Find matches across ecosystem combinations
4. Deduplicate repositories within each ecosystem combination
5. Remove packages from lower ecosystem counts if they exist in higher counts
6. Generate output CSV files in the `results/` directory organized by ecosystem count

## Input Format

The script expects CSV files in the `../../Resource/Package/Package-List/` directory with the following columns:

- `ID`: Unique package identifier
- `Platform`: Ecosystem name (Maven, NPM, PyPI, Crates, Go, Packagist, RubyGems)
- `Name`: Package name
- `Homepage URL`: Package homepage URL
- `Repository URL`: Source code repository URL (must be GitHub)

### Expected Input Files

- `Maven.csv`
- `NPM.csv`
- `PyPI.csv`
- `Crates.csv`
- `Go_part_1.csv` through `Go_part_6.csv` (automatically combined)
- `PHP.csv`
- `Ruby.csv`

Example:

```csv
ID,Platform,Name,Homepage URL,Repository URL
388554,Maven,tinkerforge,http://...,https://github.com/Tinkerforge/generators
53668,PyPI,tinkerforge,https://...,https://github.com/Tinkerforge/generators
```

**Note**: Only packages with valid GitHub repository URLs are considered for matching.

## Output Format

The script generates CSV files organized by ecosystem count in the `results/` directory.

### Directory Structure

```
results/
├── summary.csv                    # Summary of all combinations
├── 2_ecosystems/                  # All 2-ecosystem combinations
│   ├── Crates_Go.csv
│   ├── Crates_Maven.csv
│   ├── Crates_NPM.csv
│   ├── ...
├── 3_ecosystems/                  # All 3-ecosystem combinations
│   ├── Crates_Go_Maven.csv
│   ├── Crates_Go_NPM.csv
│   ├── ...
├── 4_ecosystems/                  # All 4-ecosystem combinations
│   ├── Crates_Go_Maven_NPM.csv
│   ├── ...
├── 5_ecosystems/                  # All 5-ecosystem combinations
│   ├── Crates_Go_Maven_NPM_PHP.csv
│   ├── ...
├── 6_ecosystems/                  # All 6-ecosystem combinations
│   └── ...
└── 7_ecosystems/                  # All 7 ecosystems
    └── Crates_Go_Maven_NPM_PHP_PyPI_Ruby.csv
```

### Summary File

The `summary.csv` file contains:

- `Ecosystem Count`: Number of ecosystems in the combination
- `Ecosystems`: Names of ecosystems (e.g., "Maven + NPM + PyPI")
- `Package Count`: Number of common packages found
- `Output File`: Relative path to the result file

Example:

```csv
Ecosystem Count,Ecosystems,Package Count,Output File
2,Crates + Go,45,2_ecosystems/Crates_Go.csv
2,Crates + Maven,23,2_ecosystems/Crates_Maven.csv
3,Crates + Maven + NPM,12,3_ecosystems/Crates_Maven_NPM.csv
```

### CSV Structure

Each output CSV contains columns for each ecosystem involved:

- `{ECOSYSTEM}_ID`: Original package ID
- `{ECOSYSTEM}_Name`: Package name
- `{ECOSYSTEM}_Homepage`: Homepage URL
- `{ECOSYSTEM}_Repo`: Repository URL

Example for `Maven_PyPI.csv`:

```csv
Maven_ID,Maven_Name,Maven_Homepage,Maven_Repo,PyPI_ID,PyPI_Name,PyPI_Homepage,PyPI_Repo
388554,tinkerforge,http://...,https://github.com/Tinkerforge/generators,53668,tinkerforge,https://...,https://github.com/Tinkerforge/generators
```

## Matching Criteria

A package is considered to exist in multiple ecosystems if it has the **same GitHub repository URL** (normalized for comparison).

This repository-based approach identifies packages that are truly the same project across ecosystems by matching their source repositories, regardless of package naming conventions which may vary across ecosystems.

### GitHub URL Normalization

The script normalizes GitHub URLs by:

- Converting to lowercase
- Removing `.git` suffixes
- Removing trailing slashes
- Extracting the `owner/repo` format
- Standardizing to `github.com/owner/repo` format

This ensures that URLs like:

- `https://github.com/owner/repo`
- `https://github.com/owner/repo.git`
- `http://github.com/owner/repo/`
- `git://github.com/owner/repo`

Are all recognized as the same repository.

## Deduplication Strategy

The script implements a two-level deduplication strategy to ensure clean, non-redundant results.

### 1. Within-Combination Repository Deduplication

The script automatically deduplicates packages by repository URL within each ecosystem combination. When multiple packages from the same ecosystem(s) share the same repository, only the **first occurrence** is included in the output.

Some repositories host multiple packages for different ecosystems. For example, `googleapis/googleapis` contains many protocol buffer packages like:

- `proto-google-cloud-logging-v2`
- `proto-google-cloud-spanner-v1`
- `proto-google-cloud-speech-v1`
- etc.

Without deduplication, the output CSV would contain one row for each package, even though they all point to the same repository. This creates unnecessary duplication when mining directory structures or analyzing repository characteristics.

**Behavior**:

- **Scope**: Applied after matching across ecosystems but before writing to CSV
- **Key**: Uses the first ecosystem's repository URL as the deduplication key
- **Strategy**: Keeps the first occurrence, removes subsequent duplicates
- **Reporting**: The script reports how many duplicate repositories were removed

### 2. Cross-Ecosystem-Count Deduplication

After generating all combination files, the script performs a second deduplication pass to remove packages from lower ecosystem count files if they appear in higher ecosystem count files. This ensures each package only appears in the file with the **highest** number of ecosystems.

**Example**: The package `sivchain` exists in 4 ecosystems (Crates, NPM, PyPI, Ruby). Without cross-count deduplication, it would appear in:

- `2_ecosystems/Crates_NPM.csv`
- `2_ecosystems/Crates_PyPI.csv`
- `2_ecosystems/Crates_Ruby.csv`
- `2_ecosystems/NPM_PyPI.csv`
- `2_ecosystems/NPM_Ruby.csv`
- `2_ecosystems/PyPI_Ruby.csv`
- `3_ecosystems/Crates_NPM_PyPI.csv`
- `3_ecosystems/Crates_NPM_Ruby.csv`
- `3_ecosystems/Crates_PyPI_Ruby.csv`
- `3_ecosystems/NPM_PyPI_Ruby.csv`
- `4_ecosystems/Crates_NPM_PyPI_Ruby.csv` ← **Only kept here**

With cross-count deduplication, `sivchain` only appears in `4_ecosystems/Crates_NPM_PyPI_Ruby.csv`, providing a cleaner representation of the maximum ecosystem reach for each package.

**Behavior**:

- **Scope**: Applied after all combinations are generated
- **Key**: Uses normalized package name and repository URL for identification
- **Strategy**: Processes from highest to lowest ecosystem count, removing packages from lower counts if found in higher counts
- **Reporting**: The script reports the total number of packages removed from lower ecosystem counts

## Processing Algorithm

The script uses an optimized multi-stage approach for efficient processing:

### Stage 1: Data Loading and Indexing

1. **Load Data**: Read package information from input CSV files
2. **Build Indices**: Create hash-based lookup indices (name, repo) → package data for each ecosystem

### Stage 2: Cross-Ecosystem Matching

3. **Iterate & Match**: For each package in the first ecosystem, use fast hash lookups to check if its repository exists in all other specified ecosystems
4. **Validate Match**: A match requires the normalized GitHub repository URL to match across ecosystems
5. **Within-Combination Deduplication**: Remove duplicate entries that share the same repository within each combination, keeping only the first occurrence
6. **Export Results**: Write matched packages to CSV files organized by ecosystem count

### Stage 3: Cross-Ecosystem-Count Deduplication

7. **Build Higher-Count Package Index**: Create a set of all packages appearing in higher ecosystem counts
8. **Filter Lower Counts**: For each ecosystem count level (starting from 2), remove packages that exist in any higher ecosystem count
9. **Update Files**: Overwrite lower-count CSV files with filtered data
10. **Regenerate Summary**: Update the summary file with final package counts after deduplication

This multi-stage approach ensures clean, non-redundant results while providing significant performance improvements over traditional DataFrame filtering, especially for large datasets.

## Files

- `find_cross_ecosystem_packages.py`: Main script
- `requirements.txt`: Python dependencies (pandas, tqdm)
- `setup.sh`: Automated setup script
- `results/`: Output directory (created automatically)
  - `*.csv`: Cross-ecosystem package lists

## Troubleshooting

### "No such file or directory" when loading input CSVs

Check that:

- Input CSV files exist in `../../Resource/Package/Package-List/`
- The CSV files have the correct names: `Maven.csv`, `NPM.csv`, `PyPI.csv`, `Crates.csv`, `Go_part_1.csv` through `Go_part_6.csv`, `PHP.csv`, `Ruby.csv`
- You're running the script from the correct directory

### "KeyError: 'Repository URL'" or similar column errors

Ensure that all input CSV files have the required columns:

- `ID`
- `Platform`
- `Name`
- `Homepage URL`
- `Repository URL`

### No matches found for certain combinations

This is normal if:

- Few or no packages are truly cross-published across those specific ecosystems
- Packages use different names in different ecosystems
- Packages have different repository URLs in different ecosystems

### Virtual environment issues

If you encounter errors related to the virtual environment:

1. Delete the `.venv` folder: `rm -rf .venv`
2. Re-run the setup script: `./setup.sh`
3. Virtual environments cannot be moved after creation - recreate if you move the directory

### Memory issues with large datasets

If you encounter memory errors:

- The script is optimized for large datasets using hash-based lookups
- Consider increasing available system memory
- Process smaller subsets of data if necessary

---

## Code Explanation

### 1. Import Statements

```python
import pandas as pd
import re
from pathlib import Path
from tqdm import tqdm
from itertools import combinations
```

- **pandas**: Used for reading CSV files and creating DataFrames for result output
- **re**: Regular expressions for URL parsing and normalization
- **pathlib.Path**: Modern, cross-platform file path handling
- **tqdm**: Progress bar library for visual feedback during long-running operations
- **itertools.combinations**: Generates all possible ecosystem combinations dynamically

### 2. URL Normalization Function

```python
def normalize_github_url(url):
    """
    Normalize GitHub repository URLs to a standard format for comparison.
    Returns None if URL is invalid, empty, or not a GitHub URL.
    """
    if pd.isna(url) or not url or url.strip() == '':
        return None

    url = str(url).strip().lower()

    # Check if it's a GitHub URL
    if 'github.com' not in url:
        return None

    # Remove common suffixes
    url = re.sub(r'\.git$', '', url)
    url = re.sub(r'/$', '', url)

    # Extract path from URL
    try:
        # Handle various GitHub URL formats
        match = re.search(r'github\.com[:/]([^/]+/[^/\s]+)', url)
        if match:
            repo_path = match.group(1)
            # Remove trailing content after repository name
            repo_path = re.split(r'[\s#?]', repo_path)[0]
            return f"github.com/{repo_path}"
    except:
        pass

    return None
```

**Purpose**: Creates a standardized format for GitHub URLs to enable accurate comparison.

**Process**:

1. **Validation**: Checks if URL exists and is not empty using `pd.isna()` for pandas null values
2. **Preprocessing**: Converts to lowercase and strips whitespace for case-insensitive comparison
3. **GitHub Check**: Returns `None` if URL doesn't contain 'github.com'
4. **Suffix Removal**: Uses regex to remove `.git` endings and trailing slashes
5. **Path Extraction**:
   - Uses regex pattern `r'github\.com[:/]([^/]+/[^/\s]+)'` to match:
     - `github\.com` - literal "github.com"
     - `[:/]` - either colon (for git://) or slash (for https://)
     - `([^/]+/[^/\s]+)` - captures "owner/repo" pattern
   - Removes query parameters, fragments, and whitespace using `re.split(r'[\s#?]', ...)[0]`
6. **Output**: Returns standardized format `github.com/owner/repo` or `None` if parsing fails

**Examples of normalization**:

- `https://github.com/owner/repo` → `github.com/owner/repo`
- `https://github.com/owner/repo.git` → `github.com/owner/repo`
- `git://github.com/owner/repo` → `github.com/owner/repo`
- `http://github.com/owner/repo/tree/main` → `github.com/owner/repo`

### 3. Package Name Normalization Function

```python
def normalize_package_name(name):
    """Normalize package name for comparison (lowercase, stripped)."""
    if pd.isna(name) or not name:
        return None
    return str(name).strip().lower()
```

**Purpose**: Standardizes package names for case-insensitive comparison.

**Process**:

1. Validates that name exists (not null/empty)
2. Converts to string (handles numeric or mixed types)
3. Strips leading/trailing whitespace
4. Converts to lowercase for case-insensitive matching

**Examples**:

- `"MyPackage"` → `"mypackage"`
- `"  Package-Name  "` → `"package-name"`
- `"PKG"` → `"pkg"`

### 4. Package Data Loading Function

```python
def load_package_data(base_path):
    """Load all package CSV files and create normalized lookup structures."""

    packages = {}

    # Define file paths
    files = {
        'Maven': [base_path / 'Maven.csv'],
        'NPM': [base_path / 'NPM.csv'],
        'PyPI': [base_path / 'PyPI.csv'],
        'Crates': [base_path / 'Crates.csv'],
        'Go': [base_path / f'Go_part_{i}.csv' for i in range(1, 7)],  # 6 parts
        'PHP': [base_path / 'PHP.csv'],
        'Ruby': [base_path / 'Ruby.csv']
    }

    print("Loading package data...")

    for ecosystem, filepaths in files.items():
        print(f"  Loading {ecosystem}...")

        # Load and combine multiple files if necessary (e.g., Go parts)
        dfs = []
        for filepath in filepaths:
            if filepath.exists():
                df_part = pd.read_csv(filepath, low_memory=False)
                dfs.append(df_part)
            else:
                print(f"    Warning: {filepath} not found, skipping...")

        if not dfs:
            print(f"    Error: No files found for {ecosystem}, skipping...")
            continue

        # Combine all parts into one DataFrame
        df = pd.concat(dfs, ignore_index=True)

        # Add normalized columns with progress bar
        tqdm.pandas(desc=f"    Normalizing {ecosystem} names", leave=False)
        df['normalized_name'] = df['Name'].progress_apply(normalize_package_name)

        tqdm.pandas(desc=f"    Normalizing {ecosystem} repos", leave=False)
        df['normalized_repo'] = df['Repository URL'].progress_apply(normalize_github_url)

        packages[ecosystem] = df
        print(f"    Loaded {len(df)} packages")

    return packages
```

**Purpose**: Loads all package data from CSV files and adds normalized columns. **Now supports multiple file parts per ecosystem.**

**Note**: The script now processes **Maven, NPM, PyPI, Crates, Go, PHP, and Ruby** ecosystems.

**Process**:

1. **Initialization**: Creates empty dictionary to store DataFrames
2. **Path Setup**: Uses pathlib for platform-independent path handling
   - **NEW**: Each ecosystem can have multiple files (e.g., Go split into 6 parts)
3. **Loading Loop**: For each ecosystem:
   - **NEW**: Loads multiple file parts if they exist
   - **NEW**: Checks file existence with `filepath.exists()` to handle missing files gracefully
   - **NEW**: Combines multiple DataFrames with `pd.concat(dfs, ignore_index=True)`
   - Reads CSV with `low_memory=False` to handle mixed data types
   - Uses `tqdm.pandas()` to enable progress bars on apply operations
   - Creates `normalized_name` column by applying normalization to 'Name' column
   - Creates `normalized_repo` column by applying normalization to 'Repository URL' column
   - `progress_apply()` shows a progress bar for each normalization operation
   - `leave=False` ensures progress bars don't clutter the output after completion

**Special Handling for Go**:

- Go packages are split into 6 CSV files (`Go_part_1.csv` through `Go_part_6.csv`)
- The script automatically loads and combines all parts into a single DataFrame
- The combined result is treated as one "Go" ecosystem

**Data Structure**:
Returns a dictionary:

```python
{
    'Maven': DataFrame with columns [ID, Platform, Name, Homepage URL, Repository URL, normalized_name, normalized_repo],
    'NPM': DataFrame with columns [...],
    'PyPI': DataFrame with columns [...],
    'Crates': DataFrame with columns [...],
    'Go': DataFrame with columns [...] (combined from 6 parts),
    'PHP': DataFrame with columns [...],
    'Ruby': DataFrame with columns [...]
}
```

### 5. Lookup Index Building Function

```python
def build_lookup_index(df, ecosystem_name):
    """
    Build efficient lookup indices for a package DataFrame.
    Returns a dictionary mapping (name, repo) tuples to package data.
    """
    lookup = {}

    for _, row in tqdm(df.iterrows(), total=len(df), desc=f"    Indexing {ecosystem_name}", leave=False):
        name = row['normalized_name']
        repo = row['normalized_repo']

        # Only index packages with both valid name and repo
        if name and repo:
            key = (name, repo)
            # Store package data
            lookup[key] = {
                'ID': row['ID'],
                'Name': row['Name'],
                'Homepage': row['Homepage URL'],
                'Repo': row['Repository URL']
            }

    return lookup
```

**Purpose**: Creates a hash-based index for O(1) lookup time instead of O(n) DataFrame filtering.

**Process**:

1. **Iteration**: Loops through each row in the DataFrame with progress tracking
   - `total=len(df)` provides the total count for accurate progress percentage
   - `leave=False` cleans up progress bar after completion
2. **Key Creation**: Uses tuple `(normalized_name, normalized_repo)` as dictionary key
3. **Validation**: Only indexes packages with BOTH valid name AND repo (filters out incomplete data)
4. **Value Storage**: Stores original (non-normalized) package data for output

**Data Structure**:
Returns a dictionary with composite keys:

```python
{
    ('packagename', 'github.com/owner/repo'): {
        'ID': 12345,
        'Name': 'PackageName',
        'Homepage': 'https://...',
        'Repo': 'https://github.com/owner/repo'
    },
    ...
}
```

**Performance Benefit**:

- Dictionary lookup: O(1) average case
- DataFrame filtering: O(n) where n = number of packages
- For NPM with 800K+ packages, this is 800,000x faster per lookup!

> **What is a Hash Table (Dictionary)?**
>
> A Python dictionary uses a data structure called a **hash table**. Think of it like a filing cabinet with numbered drawers:
>
> 1. When you store data with a key, Python runs the key through a **hash function** that converts it into a number (the "drawer number")
> 2. The data is stored in that specific drawer
> 3. When you look up the key, Python runs it through the same hash function to find the exact drawer
> 4. Python opens that one drawer and retrieves the data
>
> **Example Visualization:**
>
> ```
> Traditional Search (DataFrame filtering - O(n)):
> Looking for package 'xgboost' in 800,000 packages...
> Check package 1: 'aaa' ❌
> Check package 2: 'babel' ❌
> Check package 3: 'chai' ❌
> ...
> Check package 750,000: 'xgboost' ✓ FOUND!
> → Had to check 750,000 packages (worst case)
>
> Hash-Based Lookup (Dictionary - O(1)):
> Looking for key ('xgboost', 'github.com/dmlc/xgboost')...
> 1. Hash the key → get number 42857
> 2. Go directly to drawer 42857
> 3. Retrieve data ✓ FOUND!
> → Only checked 1 location
> ```
>
> In the script, we use normalized repository URLs as keys:
>
> ```python
> key = 'github.com/dmlc/xgboost'
> lookup[key] = {...package data...}
> ```
>
> - Strings are **immutable** (can't be changed after creation)
> - Strings are **hashable** (can be converted to a hash number)
> - Using normalized repository URLs ensures uniqueness and consistent matching
>
> **Actual Code:**
>
> ```python
> # Building the index (one-time cost)
> for _, row in df.iterrows():
>     repo = row['normalized_repo']   # e.g., 'github.com/dmlc/xgboost'
>
>     if repo:
>         key = repo  # Use repo as key
>         lookup[key] = {     # Store in hash table
>             'ID': row['ID'],
>             'Name': row['Name'],
>             ...
>         }
>
> # Later, searching (instant lookup)
> if key in other_lookup:  # O(1) - direct hash lookup
>     other_data = other_lookup[key]  # O(1) - direct retrieval
> ```

### 5.5. Repository Deduplication Function

```python
def deduplicate_by_repository(df, ecosystems):
    """
    Remove duplicate entries based on repository URL, keeping only the first occurrence.
    This ensures each unique repository appears only once in the output.

    Args:
        df: DataFrame containing matched packages
        ecosystems: List of ecosystem names involved

    Returns:
        DataFrame with duplicates removed based on repository URL
    """
    if df.empty:
        return df

    # Get the first ecosystem's repository column as the primary repo
    primary_repo_col = f'{ecosystems[0]}_Repo'

    if primary_repo_col not in df.columns:
        return df

    # Track number of rows before deduplication
    original_count = len(df)

    # Remove duplicates based on the primary repository URL
    # Keep the first occurrence of each unique repository
    df_deduplicated = df.drop_duplicates(subset=[primary_repo_col], keep='first')

    removed_count = original_count - len(df_deduplicated)

    if removed_count > 0:
        print(f"    Removed {removed_count} duplicate repositories (kept first occurrence)")

    return df_deduplicated
```

**Purpose**: Removes duplicate repository entries after matching, ensuring each unique repository appears only once in the output.

**Process**:

1. **Validation**: Returns empty DataFrame unchanged
2. **Column Selection**: Uses first ecosystem's repository column as primary deduplication key
   - Example: For `['Maven', 'PyPI']`, uses `Maven_Repo` column
3. **Counting**: Tracks original row count for reporting
4. **Deduplication**:
   - Uses pandas `drop_duplicates()` with `subset=[primary_repo_col]`
   - `keep='first'` preserves the first occurrence of each unique repository
   - All subsequent rows with the same repository URL are removed
5. **Reporting**: Prints count of removed duplicates if any were found
6. **Return**: Returns deduplicated DataFrame

**Why This Matters**:

Some repositories contain multiple packages for different ecosystems. For example:

- `googleapis/googleapis` contains 10+ proto-google-cloud-\* packages
- Without deduplication, directory mining scripts would fetch the same repository structure 10+ times
- With deduplication, each repository is represented once, saving API calls and storage

**Example**:

```python
# Before deduplication (23 rows)
Maven_Repo: https://github.com/googleapis/googleapis (appears 10 times)
Maven_Repo: https://github.com/bartdag/py4j (appears 1 time)
Maven_Repo: https://github.com/hankcs/HanLP (appears 1 time)
...

# After deduplication (14 unique repositories)
Maven_Repo: https://github.com/googleapis/googleapis (kept first occurrence only)
Maven_Repo: https://github.com/bartdag/py4j
Maven_Repo: https://github.com/hankcs/HanLP
...
```

**Performance**:

- Time complexity: O(n) where n = number of matched packages
- Uses pandas' efficient C-optimized deduplication
- Memory efficient - creates new DataFrame but releases original

### 6. Package Matching Function

```python
def find_matches(packages, lookups, ecosystems):
    """
    Find packages that match across specified ecosystems using hash-based lookups.

    Args:
        packages: Dictionary of DataFrames by ecosystem
        lookups: Dictionary of lookup indices by ecosystem
        ecosystems: List of ecosystem names to check

    Returns:
        DataFrame of matching packages
    """
    if len(ecosystems) < 2:
        return pd.DataFrame()

    # Start with first ecosystem
    base_ecosystem = ecosystems[0]
    base_lookup = lookups[base_ecosystem]

    matches = []

    # Iterate through packages in the base ecosystem with progress bar
    desc = f"  Matching {' + '.join(ecosystems)}"
    for key, base_data in tqdm(base_lookup.items(), desc=desc, leave=False):
        name, repo = key

        # Check if this package exists in all other ecosystems
        match_found = True
        match_data = {
            f'{base_ecosystem}_ID': base_data['ID'],
            f'{base_ecosystem}_Name': base_data['Name'],
            f'{base_ecosystem}_Homepage': base_data['Homepage'],
            f'{base_ecosystem}_Repo': base_data['Repo'],
        }

        for other_ecosystem in ecosystems[1:]:
            other_lookup = lookups[other_ecosystem]

            # Fast hash-based lookup
            if key in other_lookup:
                other_data = other_lookup[key]
                match_data[f'{other_ecosystem}_ID'] = other_data['ID']
                match_data[f'{other_ecosystem}_Name'] = other_data['Name']
                match_data[f'{other_ecosystem}_Homepage'] = other_data['Homepage']
                match_data[f'{other_ecosystem}_Repo'] = other_data['Repo']
            else:
                match_found = False
                break

        if match_found:
            matches.append(match_data)

    matches_df = pd.DataFrame(matches)

    # Deduplicate by repository URL
    if not matches_df.empty:
        matches_df = deduplicate_by_repository(matches_df, ecosystems)

    return matches_df
```

**Purpose**: Identifies packages that exist in ALL specified ecosystems using efficient lookups, then deduplicates by repository.

**Algorithm**:

1. **Base Selection**: Uses first ecosystem as the base for iteration
2. **Iteration**: Loops through each package in the base ecosystem
3. **Matching Logic**: For each package:
   - Starts with `match_found = True`
   - Creates initial match data from base ecosystem
   - Checks each other ecosystem:
     - Uses `if key in other_lookup` for O(1) hash lookup
     - If found: adds that ecosystem's data to match_data
     - If not found: sets `match_found = False` and breaks early
   - Only adds to results if found in ALL ecosystems
4. **DataFrame Creation**: Converts list of dictionaries to DataFrame
5. **Deduplication**: Calls `deduplicate_by_repository()` to remove duplicate repositories
6. **Output**: Returns deduplicated DataFrame

**Example Flow** (for Maven + NPM + PyPI):

```
For package 'xgboost' in Maven:
  - Check NPM: key ('xgboost', 'github.com/dmlc/xgboost') in NPM lookup? → Yes
  - Check PyPI: key ('xgboost', 'github.com/dmlc/xgboost') in PyPI lookup? → Yes
  - All found → Add to matches

For package 'fastjson' in Maven:
  - Check NPM: key ('fastjson', 'github.com/alibaba/fastjson') in NPM lookup? → No
  - Not found in NPM → Skip (break early)
```

> **Detailed Step-by-Step Walkthrough**
>
> This is an example of finding packages that exist in both Maven and NPM:
>
> **Step 1: Setup**
>
> ```python
> base_ecosystem = 'Maven'
> base_lookup = lookups['Maven']  # Hash table with Maven packages
> ```
>
> **Step 2: Iterate through Maven packages**
>
> **Iteration 1: Package 'gson'**
>
> ```python
> # Current package from Maven
> key = 'github.com/google/gson'
> base_data = {
>     'ID': 123456,
>     'Name': 'gson',
>     'Homepage': 'https://github.com/google/gson',
>     'Repo': 'https://github.com/google/gson'
> }
>
> # Check if this repo exists in NPM lookup
> if key in lookups['NPM']:  # ← Hash lookup happens here! O(1)
>     # Key NOT found in NPM
>     match_found = False
>     break  # Skip to next Maven package
> ```
>
> 1. Python hashed the string `'github.com/google/gson'`
> 2. Got hash number, e.g., 758392847
> 3. Looked in drawer 758392847 of NPM hash table
> 4. Found nothing there
> 5. Returned False - **Instant decision, no looping.**
>
> **Iteration N: Package 'flatbuffers'**
>
> ```python
> # Current package from Maven
> key = 'github.com/google/flatbuffers'
> base_data = {
>     'ID': 789012,
>     'Name': 'flatbuffers',
>     'Homepage': 'https://github.com/google/flatbuffers',
>     'Repo': 'https://github.com/google/flatbuffers'
> }
>
> # Initialize match data with Maven info
> match_data = {
>     'Maven_ID': 789012,
>     'Maven_Name': 'flatbuffers',
>     'Maven_Homepage': 'https://github.com/google/flatbuffers',
>     'Maven_Repo': 'https://github.com/google/flatbuffers'
> }
>
> # Check NPM
> if key in lookups['NPM']:  # ← Hash lookup - O(1)
>     # Key FOUND in NPM!
>     other_data = lookups['NPM'][key]  # ← Hash retrieval - O(1)
>     # other_data = {
>     #     'ID': 456789,
>     #     'Name': 'flatbuffers',
>     #     'Homepage': 'https://github.com/google/flatbuffers',
>     #     'Repo': 'https://github.com/google/flatbuffers'
>     # }
>
>     # Add NPM data to match
>     match_data['NPM_ID'] = 456789
>     match_data['NPM_Name'] = 'flatbuffers'
>     match_data['NPM_Homepage'] = 'https://github.com/google/flatbuffers'
>     match_data['NPM_Repo'] = 'https://github.com/google/flatbuffers'
>
>     match_found = True  # Found in all ecosystems!
>
> # Add to results
> matches.append(match_data)
> # Result: {
> #     'Maven_ID': 789012,
> #     'Maven_Name': 'flatbuffers',
> #     'Maven_Homepage': 'https://github.com/google/flatbuffers',
> #     'Maven_Repo': 'https://github.com/google/flatbuffers',
> #     'NPM_ID': 456789,
> #     'NPM_Name': 'flatbuffers',
> #     'NPM_Homepage': 'https://github.com/google/flatbuffers',
> #     'NPM_Repo': 'https://github.com/google/flatbuffers'
> # }
> ```
>
> **Output DataFrame Structure**:
>
> ```csv
> Maven_ID,Maven_Name,Maven_Homepage,Maven_Repo,NPM_ID,NPM_Name,NPM_Homepage,NPM_Repo,PyPI_ID,PyPI_Name,PyPI_Homepage,PyPI_Repo,Crates_ID,Crates_Name,Crates_Homepage,Crates_Repo
> ```

### 7. Cross-Ecosystem-Count Deduplication Function

```python
def deduplicate_across_ecosystem_counts(results_path, combinations_by_count):
    """
    Remove packages from lower ecosystem count files if they appear in higher ecosystem count files.
    This ensures each package only appears in the file with the highest ecosystem count.

    Args:
        results_path: Path to results directory
        combinations_by_count: Dictionary mapping ecosystem count to list of (ecosystems_list, filename) tuples
    """
    print("\n" + "="*80)
    print("Deduplicating across ecosystem counts...")
    print("="*80)
    print("Removing packages from lower ecosystem counts if they exist in higher counts")

    # Build a set of all package identifiers from higher ecosystem counts
    # Package identifier: normalized_repo
    packages_in_higher_counts = {}  # maps count -> set of repo URLs

    # Process from highest to lowest ecosystem count
    for count in sorted(combinations_by_count.keys(), reverse=True):
        packages_in_higher_counts[count] = set()
        subfolder = results_path / f'{count}_ecosystems'

        if not subfolder.exists():
            continue

        # Read all files in this ecosystem count
        for ecosystems_list, output_file in combinations_by_count[count]:
            file_path = subfolder / output_file

            if not file_path.exists():
                continue

            df = pd.read_csv(file_path)

            if df.empty:
                continue

            # Extract package identifiers from this file
            # Use the first ecosystem's name and repo for identification
            first_ecosystem = ecosystems_list[0]
            name_col = f'{first_ecosystem}_Name'
            repo_col = f'{first_ecosystem}_Repo'

            if name_col in df.columns and repo_col in df.columns:
                for _, row in df.iterrows():
                    name = normalize_package_name(row[name_col], first_ecosystem)
                    repo = normalize_github_url(row[repo_col])
                    if name and repo:
                        packages_in_higher_counts[count].add((name, repo))

    # Now remove packages from lower counts if they exist in higher counts
    total_removed = 0

    for count in sorted(combinations_by_count.keys()):
        subfolder = results_path / f'{count}_ecosystems'

        if not subfolder.exists():
            continue

        # Get all packages from higher counts
        higher_packages = set()
        for higher_count in range(count + 1, max(combinations_by_count.keys()) + 1):
            if higher_count in packages_in_higher_counts:
                higher_packages.update(packages_in_higher_counts[higher_count])

        if not higher_packages:
            continue

        print(f"\nProcessing {count}-ecosystem files:")
        print(f"  Checking against {len(higher_packages)} packages from higher ecosystem counts")

        # Process each file in this ecosystem count
        for ecosystems_list, output_file in combinations_by_count[count]:
            file_path = subfolder / output_file

            if not file_path.exists():
                continue

            df = pd.read_csv(file_path)
            original_count = len(df)

            if df.empty:
                continue

            # Filter out packages that exist in higher counts
            first_ecosystem = ecosystems_list[0]
            name_col = f'{first_ecosystem}_Name'
            repo_col = f'{first_ecosystem}_Repo'

            if name_col not in df.columns or repo_col not in df.columns:
                continue

            # Create a mask for rows to keep
            def should_keep_row(row):
                name = normalize_package_name(row[name_col], first_ecosystem)
                repo = normalize_github_url(row[repo_col])
                if name and repo:
                    return (name, repo) not in higher_packages
                return True

            df_filtered = df[df.apply(should_keep_row, axis=1)]

            removed = original_count - len(df_filtered)

            if removed > 0:
                print(f"  {output_file}: Removed {removed} packages (found in higher counts)")
                total_removed += removed

                # Save the filtered DataFrame
                df_filtered.to_csv(file_path, index=False)

    print(f"\n{'='*80}")
    print(f"Total packages removed from lower ecosystem counts: {total_removed}")
    print(f"{'='*80}")
```

**Purpose**: Ensures each package only appears in the file representing its maximum ecosystem reach, preventing redundancy across ecosystem count levels.

**Process**:

1. **Build Higher-Count Index (Reverse Iteration)**:

   - Iterates from highest to lowest ecosystem count (7 down to 2)
   - For each count level, reads all CSV files in that folder
   - Extracts package identifiers (normalized repository URLs) from each file
   - Stores in dictionary: `packages_in_higher_counts[count] = set of repo URLs`

2. **Filter Lower Counts (Forward Iteration)**:

   - Iterates from lowest to highest ecosystem count (2 up to 6)
   - For each count level, collects all packages from higher counts
   - Example: When processing 2-ecosystem files, collects packages from 3, 4, 5, 6, 7-ecosystem files
   - Reads each CSV file in current count level
   - Filters out rows where repository URL exists in higher counts
   - Overwrites the CSV file with filtered data

3. **Identification Strategy**:

   - Uses first ecosystem's repository column for consistent identification
   - Applies same normalization function used during matching
   - Ensures consistent comparison across all files

4. **Performance Optimization**:
   - Uses Python sets for O(1) lookup performance
   - Only processes files that exist (handles missing combinations)
   - Skips empty DataFrames to avoid unnecessary operations

**Example Workflow**:

For package `sivchain` appearing in Crates, NPM, PyPI, and Ruby:

1. **Build Index**: Finds `sivchain` in `4_ecosystems/Crates_NPM_PyPI_Ruby.csv`

   - Adds `'github.com/zcred/sivchain'` to `packages_in_higher_counts[4]`

2. **Filter 3-Ecosystem Files**:

   - Collects packages from levels 4-7 (including `sivchain`)
   - Processes `3_ecosystems/Crates_NPM_PyPI.csv`, `Crates_NPM_Ruby.csv`, etc.
   - Removes `sivchain` from any 3-ecosystem file it appears in

3. **Filter 2-Ecosystem Files**:
   - Collects packages from levels 3-7 (including `sivchain`)
   - Processes `2_ecosystems/Crates_NPM.csv`, `Crates_PyPI.csv`, etc.
   - Removes `sivchain` from any 2-ecosystem file it appears in

**Result**: `sivchain` only appears in `4_ecosystems/Crates_NPM_PyPI_Ruby.csv`

### 8. Combination Generation Function

```python
def generate_combinations(ecosystems):
    """
    Generate all possible combinations of ecosystems (2 or more).
    Returns a list of tuples: (ecosystem_list, output_filename)
    """
    all_combinations = []

    # Generate combinations for each size (2, 3, 4, ...)
    for size in range(2, len(ecosystems) + 1):
        for combo in combinations(ecosystems, size):
            combo_list = list(combo)
            filename = '_'.join(combo_list) + '.csv'
            all_combinations.append((combo_list, filename))

    return all_combinations
```

**Purpose**: Dynamically generates all possible ecosystem combinations instead of hardcoding them.

**Process**:

1. **Size Iteration**: Loops from 2 ecosystems to all ecosystems (7)
2. **Combination Generation**: Uses `itertools.combinations()` to generate all unique combinations
   - Example: `combinations(['A', 'B', 'C'], 2)` yields `[('A', 'B'), ('A', 'C'), ('B', 'C')]`
3. **Filename Generation**: Joins ecosystem names with underscores and adds `.csv` extension
   - Example: `['Maven', 'NPM', 'PyPI']` → `'Maven_NPM_PyPI.csv'`
4. **Output**: Returns list of `(ecosystem_list, filename)` tuples

**Mathematical Note**: For 7 ecosystems, this generates:

- C(7,2) = 21 two-way combinations
- C(7,3) = 35 three-way combinations
- C(7,4) = 35 four-way combinations
- C(7,5) = 21 five-way combinations
- C(7,6) = 7 six-way combinations
- C(7,7) = 1 seven-way combination
- **Total: 120 combinations**

### 9. Main Execution Function

```python
def main():
    """Main execution function."""

    # Set up paths
    base_path = Path(__file__).parent.parent.parent.parent / 'Resource' / 'Package' / 'Package-List'
    results_path = Path(__file__).parent / 'results'
    results_path.mkdir(exist_ok=True)

    print("="*80)
    print("Cross-Ecosystem Package Analysis")
    print("="*80)

    # Load all package data
    packages = load_package_data(base_path)

    # Get list of available ecosystems
    ecosystems = sorted(packages.keys())
    print(f"\nAvailable ecosystems: {', '.join(ecosystems)}")

    # Build lookup indices for efficient matching
    print("\n" + "="*80)
    print("Building lookup indices...")
    print("="*80)
    lookups = {}
    for ecosystem, df in packages.items():
        print(f"  Building index for {ecosystem}...")
        lookups[ecosystem] = build_lookup_index(df, ecosystem)
        print(f"    Indexed {len(lookups[ecosystem])} packages with valid name+repo")

    # Generate all combinations dynamically
    all_combinations = generate_combinations(ecosystems)
    print(f"\n  Total combinations to process: {len(all_combinations)}")

    print("\n" + "="*80)
    print("Finding cross-ecosystem packages...")
    print("="*80)

    results_summary = []

    # Group combinations by ecosystem count
    combinations_by_count = {}
    for combo_list, filename in all_combinations:
        count = len(combo_list)
        if count not in combinations_by_count:
            combinations_by_count[count] = []
        combinations_by_count[count].append((combo_list, filename))

    # Process each group and save to corresponding folder
    for count in sorted(combinations_by_count.keys()):
        print(f"\n{'='*80}")
        print(f"Processing {count}-ecosystem combinations")
        print(f"{'='*80}")

        # Create subfolder for this ecosystem count
        subfolder = results_path / f'{count}_ecosystems'
        subfolder.mkdir(exist_ok=True)

        for ecosystems_list, output_file in tqdm(combinations_by_count[count],
                                                   desc=f"{count}-ecosystem combinations",
                                                   unit="combination"):
            print(f"\n{' + '.join(ecosystems_list)}:")
            print("-" * 40)

            # Find matches (both name AND repo must match)
            matches_df = find_matches(packages, lookups, ecosystems_list)

            output_path = subfolder / output_file
            matches_df.to_csv(output_path, index=False)

            print(f"  Found {len(matches_df)} packages")
            print(f"  Saved to: {output_path}")

            results_summary.append({
                'Ecosystem Count': count,
                'Ecosystems': ' + '.join(ecosystems_list),
                'Package Count': len(matches_df),
                'Output File': f'{count}_ecosystems/{output_file}'
            })

    # Deduplicate across ecosystem counts (remove from lower counts if in higher counts)
    deduplicate_across_ecosystem_counts(results_path, combinations_by_count)

    # Regenerate summary after deduplication
    print("\n" + "="*80)
    print("Regenerating summary after deduplication...")
    print("="*80)

    results_summary = []
    for count in sorted(combinations_by_count.keys()):
        subfolder = results_path / f'{count}_ecosystems'
        if not subfolder.exists():
            continue

        for ecosystems_list, output_file in combinations_by_count[count]:
            file_path = subfolder / output_file
            if file_path.exists():
                df = pd.read_csv(file_path)
                package_count = len(df)
                if package_count > 0:
                    results_summary.append({
                        'Ecosystem Count': count,
                        'Ecosystems': ' + '.join(ecosystems_list),
                        'Package Count': package_count,
                        'Output File': f'{count}_ecosystems/{output_file}'
                    })

    # Create summary DataFrame
    summary_df = pd.DataFrame(results_summary)

    # Save summary to CSV
    summary_path = results_path / 'summary.csv'
    summary_df.to_csv(summary_path, index=False)

    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(summary_df.to_string(index=False))

    # Print statistics by ecosystem count
    print("\n" + "="*80)
    print("STATISTICS BY ECOSYSTEM COUNT")
    print("="*80)
    stats_df = summary_df.groupby('Ecosystem Count').agg({
        'Package Count': ['sum', 'mean', 'max', 'min', 'count']
    }).round(2)
    stats_df.columns = ['Total Packages', 'Avg Packages', 'Max Packages', 'Min Packages', 'Combinations']
    print(stats_df.to_string())

    print("\n" + "="*80)
    print(f"All results saved to: {results_path}")
    print(f"Summary saved to: {summary_path}")
    print("="*80)
```

**Purpose**: Orchestrates the entire analysis workflow with automatic categorization and summary generation.

**Note**: The script now **dynamically generates all combinations** across **7 ecosystems** (Maven, NPM, PyPI, Crates, Go, PHP, Ruby).

**Workflow**:

1. **Path Setup**:

   - `Path(__file__).parent` gets the script's directory
   - Navigates up 4 levels to reach workspace root, then to data directory
   - Creates `results/` directory if it doesn't exist (`exist_ok=True` prevents errors)

2. **Data Loading Phase**:

   - Calls `load_package_data()` to read all CSV files (including 6 Go parts)
   - **NEW**: Combines multiple file parts per ecosystem
   - Normalizes names and URLs for each ecosystem
   - Shows progress bars for normalization

3. **Index Building Phase**:

   - Builds hash-based lookup indices for each ecosystem
   - Filters to only packages with valid name+repo
   - Reports count of indexed packages

4. **Combinations Generation**:

   - **NEW**: Dynamically generates all possible combinations using `generate_combinations()`
   - Reports total number of combinations (120 for 7 ecosystems)

5. **Grouping Phase**:

   - **NEW**: Groups combinations by ecosystem count (2, 3, 4, 5, 6, 7)
   - Organizes processing by group for better organization

6. **Matching Phase**:

   - **NEW**: Creates separate subfolders for each ecosystem count
   - Loops through each combination with progress bars per group
   - Calls `find_matches()` for each combination (which includes within-combination deduplication)
   - **NEW**: Saves results to organized subfolders (e.g., `2_ecosystems/Maven_NPM.csv`)
   - Tracks results for summary with ecosystem count

7. **Cross-Ecosystem-Count Deduplication Phase**:

   - **NEW**: Calls `deduplicate_across_ecosystem_counts()` to remove packages from lower counts if they exist in higher counts
   - Processes from highest to lowest ecosystem count
   - Builds index of packages in higher counts
   - Filters lower-count files to remove duplicates
   - Overwrites CSV files with deduplicated data
   - Reports total number of packages removed

8. **Summary Regeneration Phase**:

   - **NEW**: Regenerates summary after deduplication by re-reading all CSV files
   - Collects updated package counts from deduplicated files
   - Ensures summary reflects actual final state of output files

9. **Final Summary Phase**:
   - Creates comprehensive summary DataFrame with ecosystem count
   - Saves summary to `summary.csv` file
   - Displays formatted summary table
   - Displays statistics grouped by ecosystem count (total, average, max, min, count)
   - Shows final output locations

**Progress Bars**:

- Per-group: Number of combinations in each ecosystem count group
- Per-combination: Number of packages in base ecosystem being checked
- Normalization: Per-package normalization operations
- Indexing: Per-package index building

**New Features**:

- Automatic folder organization by ecosystem count
- Cross-ecosystem-count deduplication for cleaner results
- Summary CSV with all results in one place
- Statistical analysis by ecosystem count
- Dynamic combination generation (no hardcoded list)
- Summary regeneration after deduplication for accuracy

### 9. Script Entry Point

```python
if __name__ == '__main__':
    main()
```

**Purpose**: Ensures `main()` only runs when script is executed directly, not when imported as a module.

**Benefit**: Allows the script to be safely imported for testing or reuse without auto-executing.

---

## Performance Optimizations

### 1. Hash-Based Lookups

- **Instead of**: DataFrame filtering with boolean masks (O(n) complexity)
- **Uses**: Dictionary lookups (O(1) average complexity)
- **Impact**: ~800,000x faster for NPM with 800K packages

### 2. Early Breaking

- In `find_matches()`, breaks immediately when a package is not found in an ecosystem
- Avoids unnecessary checks of remaining ecosystems
- Particularly effective for combinations unlikely to have matches (e.g., CRAN + Maven)

### 3. Progress Bars with `leave=False`

- Temporary progress bars don't clutter terminal output
- Only final results and counts remain visible
- Improves user experience with clean output

### 4. Efficient Data Structures

- Stores only necessary fields in lookup dictionaries
- Uses tuples for immutable, hashable keys
- Minimal memory overhead

### 5. Pandas Optimization

- `low_memory=False` handles mixed data types efficiently
- `progress_apply()` instead of iterating and tracking manually
- Direct CSV writing without intermediate formatting
