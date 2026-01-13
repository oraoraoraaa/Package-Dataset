#!/usr/bin/env python3
"""
Script to identify cross-ecosystem packages across Maven, NPM, PyPI, Crates, Go, PHP, and Ruby.
Identifies packages that exist in multiple ecosystems based on matching GitHub repository URLs (normalized).

Results are categorized by ecosystem count (2 ecosystems, 3 ecosystems, etc.)
and a summary file is generated.
"""

import pandas as pd
import re
from pathlib import Path
from tqdm import tqdm
from itertools import combinations


def normalize_github_url(url):
    """
    Normalize GitHub repository URLs to a standard format for comparison.
    Returns None if URL is invalid, empty, or not a GitHub URL.
    """
    if pd.isna(url) or not url or url.strip() == "":
        return None

    url = str(url).strip().lower()

    # Check if it's a GitHub URL
    if "github.com" not in url:
        return None

    # Remove common suffixes and prefixes
    url = re.sub(r"\.git$", "", url)
    url = re.sub(r"/$", "", url)
    
    # Remove git protocol prefixes
    url = url.replace('git+https://', 'https://')
    url = url.replace('git+ssh://', 'ssh://')
    url = url.replace('git://', 'https://')

    # Extract path from URL
    try:
        # Handle various GitHub URL formats (https, ssh, git@)
        match = re.search(r"github\.com[:/]([^/]+/[^/\s]+)", url)
        if match:
            repo_path = match.group(1)
            # Remove trailing content after repository name
            repo_path = re.split(r"[\s#?]", repo_path)[0]
            # Remove .git suffix if still present in the extracted path
            repo_path = re.sub(r"\.git$", "", repo_path)
            # Remove trailing slash
            repo_path = repo_path.rstrip('/')
            return f"github.com/{repo_path}"
    except:
        pass

    return None


def normalize_github_url_with_fallback(repo_url, homepage_url):
    """
    Normalize GitHub URL with Homepage URL as fallback.
    First tries Repository URL, if that fails, tries Homepage URL.
    Returns None if neither contains a valid GitHub URL.
    """
    # Try Repository URL first
    normalized = normalize_github_url(repo_url)
    if normalized:
        return normalized
    
    # Fallback to Homepage URL
    normalized = normalize_github_url(homepage_url)
    return normalized


def load_package_data(base_path):
    """Load all package CSV files and create normalized lookup structures."""

    packages = {}

    # Define file paths
    files = {
        "Maven": [base_path / "Maven.csv"],
        "NPM": [base_path / "NPM.csv"],
        "PyPI": [base_path / "PyPI.csv"],
        "Crates": [base_path / "Crates.csv"],
        "Go": [base_path / f"Go.csv"],
        "PHP": [base_path / "PHP.csv"],
        "Ruby": [base_path / "Ruby.csv"],
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
        # Use Homepage URL as fallback when Repository URL is missing
        tqdm.pandas(desc=f"    Normalizing {ecosystem} repos", leave=False)
        df["normalized_repo"] = df.progress_apply(
            lambda row: normalize_github_url_with_fallback(
                row["Repository URL"], row["Homepage URL"]
            ),
            axis=1
        )

        packages[ecosystem] = df
        print(f"    Loaded {len(df)} packages")

    return packages


def build_lookup_index(df, ecosystem_name):
    """
    Build efficient lookup indices for a package DataFrame.
    Returns a dictionary mapping normalized repo URLs to package data.
    """
    lookup = {}

    for _, row in tqdm(
        df.iterrows(), total=len(df), desc=f"    Indexing {ecosystem_name}", leave=False
    ):
        repo = row["normalized_repo"]

        # Only index packages with valid repo
        if repo:
            # Store package data with repo as key
            lookup[repo] = {
                "ID": row["ID"],
                "Name": row["Name"],
                "Homepage": row["Homepage URL"],
                "Repo": row["Repository URL"],
            }

    return lookup


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
    primary_repo_col = f"{ecosystems[0]}_Repo"

    if primary_repo_col not in df.columns:
        return df

    # Track number of rows before deduplication
    original_count = len(df)

    # Remove duplicates based on the primary repository URL
    # Keep the first occurrence of each unique repository
    df_deduplicated = df.drop_duplicates(subset=[primary_repo_col], keep="first")

    removed_count = original_count - len(df_deduplicated)

    if removed_count > 0:
        print(
            f"    Removed {removed_count} duplicate repositories (kept first occurrence)"
        )

    return df_deduplicated


def find_matches(packages, lookups, ecosystems):
    """
    Find packages that match across specified ecosystems using hash-based lookups.

    Args:
        packages: Dictionary of DataFrames by ecosystem
        lookups: Dictionary of lookup indices by ecosystem
        ecosystems: List of ecosystem names to check

    Returns:
        DataFrame of matching packages (deduplicated by repository)
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
        repo = key

        # Check if this package exists in all other ecosystems
        match_found = True
        match_data = {
            f"{base_ecosystem}_ID": base_data["ID"],
            f"{base_ecosystem}_Name": base_data["Name"],
            f"{base_ecosystem}_Homepage": base_data["Homepage"],
            f"{base_ecosystem}_Repo": base_data["Repo"],
        }

        for other_ecosystem in ecosystems[1:]:
            other_lookup = lookups[other_ecosystem]

            # Fast hash-based lookup
            if key in other_lookup:
                other_data = other_lookup[key]
                match_data[f"{other_ecosystem}_ID"] = other_data["ID"]
                match_data[f"{other_ecosystem}_Name"] = other_data["Name"]
                match_data[f"{other_ecosystem}_Homepage"] = other_data["Homepage"]
                match_data[f"{other_ecosystem}_Repo"] = other_data["Repo"]
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
            filename = "_".join(combo_list) + ".csv"
            all_combinations.append((combo_list, filename))

    return all_combinations


def deduplicate_across_ecosystem_counts(results_path, combinations_by_count):
    """
    Remove packages from lower ecosystem count files if they appear in higher ecosystem count files.
    This ensures each package only appears in the file with the highest ecosystem count.

    Args:
        results_path: Path to results directory
        combinations_by_count: Dictionary mapping ecosystem count to list of (ecosystems_list, filename) tuples
    """
    print("\n" + "=" * 80)
    print("Deduplicating across ecosystem counts...")
    print("=" * 80)
    print(
        "Removing packages from lower ecosystem counts if they exist in higher counts"
    )

    # Build a set of all package identifiers from higher ecosystem counts
    # Package identifier: normalized_repo
    packages_in_higher_counts = {}  # maps count -> set of repo strings

    # Process from highest to lowest ecosystem count
    for count in sorted(combinations_by_count.keys(), reverse=True):
        packages_in_higher_counts[count] = set()
        subfolder = results_path / f"{count}_ecosystems"

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
            # Use the first ecosystem's repo for identification
            first_ecosystem = ecosystems_list[0]
            repo_col = f"{first_ecosystem}_Repo"

            if repo_col in df.columns:
                for _, row in df.iterrows():
                    repo = normalize_github_url(row[repo_col])
                    if repo:
                        packages_in_higher_counts[count].add(repo)

    # Now remove packages from lower counts if they exist in higher counts
    total_removed = 0

    for count in sorted(combinations_by_count.keys()):
        subfolder = results_path / f"{count}_ecosystems"

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
        print(
            f"  Checking against {len(higher_packages)} packages from higher ecosystem counts"
        )

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
            repo_col = f"{first_ecosystem}_Repo"

            if repo_col not in df.columns:
                continue

            # Create a mask for rows to keep
            def should_keep_row(row):
                repo = normalize_github_url(row[repo_col])
                if repo:
                    return repo not in higher_packages
                return True

            df_filtered = df[df.apply(should_keep_row, axis=1)]

            removed = original_count - len(df_filtered)

            if removed > 0:
                print(
                    f"  {output_file}: Removed {removed} packages (found in higher counts)"
                )
                total_removed += removed

                if df_filtered.empty:
                    print(f"  {output_file} is now empty. Deleting file.")
                    file_path.unlink()
                else:
                    # Save the filtered DataFrame
                    df_filtered.to_csv(file_path, index=False)

    print(f"\n{'='*80}")
    print(f"Total packages removed from lower ecosystem counts: {total_removed}")
    print(f"{'='*80}")


def main():
    """Main execution function."""

    # Set up paths
    base_path = (
        Path(__file__).parent.parent.parent.parent
        / "Resource"
        / "Package"
        / "Package-List"
    )
    results_path = Path(__file__).parent / "results"
    results_path.mkdir(exist_ok=True)

    print("=" * 80)
    print("Cross-Ecosystem Package Analysis")
    print("=" * 80)

    # Load all package data
    packages = load_package_data(base_path)

    # Calculate input statistics
    total_input_packages = 0
    all_valid_repos = set()
    for df in packages.values():
        total_input_packages += len(df)
        # valid repos only
        repos = df["normalized_repo"].dropna()
        all_valid_repos.update(repos)
    
    valid_packages_count = len(all_valid_repos)

    # Get list of available ecosystems
    ecosystems = sorted(packages.keys())
    print(f"\nAvailable ecosystems: {', '.join(ecosystems)}")

    # Build lookup indices for efficient matching
    print("\n" + "=" * 80)
    print("Building lookup indices...")
    print("=" * 80)
    lookups = {}
    for ecosystem, df in packages.items():
        print(f"  Building index for {ecosystem}...")
        lookups[ecosystem] = build_lookup_index(df, ecosystem)
        print(f"    Indexed {len(lookups[ecosystem])} packages with valid repo")

    # Generate all combinations dynamically
    all_combinations = generate_combinations(ecosystems)
    print(f"\n  Total combinations to process: {len(all_combinations)}")

    print("\n" + "=" * 80)
    print("Finding cross-ecosystem packages...")
    print("=" * 80)

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
        subfolder = results_path / f"{count}_ecosystems"
        subfolder.mkdir(exist_ok=True)

        for ecosystems_list, output_file in tqdm(
            combinations_by_count[count],
            desc=f"{count}-ecosystem combinations",
            unit="combination",
        ):
            print(f"\n{' + '.join(ecosystems_list)}:")
            print("-" * 40)

            # Find matches (both name AND repo must match)
            matches_df = find_matches(packages, lookups, ecosystems_list)

            package_count = len(matches_df)
            print(f"  Found {package_count} packages")

            # Only save CSV if matches were found
            if package_count > 0:
                output_path = subfolder / output_file
                matches_df.to_csv(output_path, index=False)
                print(f"  Saved to: {output_path}")

                results_summary.append(
                    {
                        "Ecosystem Count": count,
                        "Ecosystems": " + ".join(ecosystems_list),
                        "Package Count": package_count,
                        "Output File": f"{count}_ecosystems/{output_file}",
                    }
                )
            else:
                print(f"  Skipped saving (no matches found)")

    # Deduplicate across ecosystem counts (remove from lower counts if in higher counts)
    deduplicate_across_ecosystem_counts(results_path, combinations_by_count)

    # Regenerate summary after deduplication
    print("\n" + "=" * 80)
    print("Regenerating summary after deduplication...")
    print("=" * 80)

    results_summary = []
    for count in sorted(combinations_by_count.keys()):
        subfolder = results_path / f"{count}_ecosystems"
        if not subfolder.exists():
            continue

        for ecosystems_list, output_file in combinations_by_count[count]:
            file_path = subfolder / output_file
            if file_path.exists():
                df = pd.read_csv(file_path)
                package_count = len(df)
                if package_count > 0:
                    results_summary.append(
                        {
                            "Ecosystem Count": count,
                            "Ecosystems": " + ".join(ecosystems_list),
                            "Package Count": package_count,
                            "Output File": f"{count}_ecosystems/{output_file}",
                        }
                    )

    # Create summary DataFrame
    summary_df = pd.DataFrame(results_summary)

    # Calculate total cross-ecosystem packages
    total_cross_ecosystem = summary_df["Package Count"].sum() if not summary_df.empty else 0
    cross_ecosystem_percentage = (total_cross_ecosystem / valid_packages_count * 100) if valid_packages_count > 0 else 0

    # Calculate per-ecosystem cross-ecosystem statistics
    print("\n" + "=" * 80)
    print("Calculating per-ecosystem statistics...")
    print("=" * 80)
    
    ecosystem_stats = {}
    
    for ecosystem in ecosystems:
        # Get total packages loaded for this ecosystem
        total_packages_loaded = len(packages[ecosystem])
        
        # Get all packages from this ecosystem that have valid repos
        ecosystem_lookup = lookups[ecosystem]
        total_packages_with_repo = len(ecosystem_lookup)
        
        # Find all cross-ecosystem packages from this ecosystem
        cross_ecosystem_repos = set()
        
        for count in sorted(combinations_by_count.keys()):
            subfolder = results_path / f"{count}_ecosystems"
            if not subfolder.exists():
                continue
            
            for ecosystems_list, output_file in combinations_by_count[count]:
                # Only process combinations that include this ecosystem
                if ecosystem not in ecosystems_list:
                    continue
                
                file_path = subfolder / output_file
                if not file_path.exists():
                    continue
                
                df = pd.read_csv(file_path)
                if df.empty:
                    continue
                
                # Get the repo column for this ecosystem
                repo_col = f"{ecosystem}_Repo"
                if repo_col not in df.columns:
                    continue
                
                # Add all repos from this ecosystem to the set
                for _, row in df.iterrows():
                    repo = normalize_github_url(row[repo_col])
                    if repo:
                        cross_ecosystem_repos.add(repo)
        
        cross_ecosystem_count = len(cross_ecosystem_repos)
        percentage = (cross_ecosystem_count / total_packages_with_repo * 100) if total_packages_with_repo > 0 else 0
        
        ecosystem_stats[ecosystem] = {
            "Total Packages": total_packages_loaded,
            "Valid Indexed Repos": total_packages_with_repo,
            "Cross-Ecosystem Packages": cross_ecosystem_count,
            "Percentage": percentage
        }
        
        print(f"  {ecosystem}: {cross_ecosystem_count}/{total_packages_with_repo} ({percentage:.2f}%)")
    
    # Create ecosystem statistics DataFrame
    ecosystem_stats_df = pd.DataFrame.from_dict(ecosystem_stats, orient='index')
    ecosystem_stats_df.index.name = 'Ecosystem'
    ecosystem_stats_df = ecosystem_stats_df.reset_index()
    ecosystem_stats_df = ecosystem_stats_df.sort_values('Cross-Ecosystem Packages', ascending=False)

    # Save summary to CSV
    summary_path = results_path / "summary.csv"
    summary_df.to_csv(summary_path, index=False)

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(summary_df.to_string(index=False))

    # Print statistics by ecosystem count
    print("\n" + "=" * 80)
    print("STATISTICS BY ECOSYSTEM COUNT")
    print("=" * 80)
    stats_df = (
        summary_df.groupby("Ecosystem Count")
        .agg({"Package Count": ["sum", "mean", "max", "min", "count"]})
        .round(2)
    )
    stats_df.columns = [
        "Total Packages",
        "Avg Packages",
        "Max Packages",
        "Min Packages",
        "Combinations",
    ]
    print(stats_df.to_string())

    # Save summary tables to text file
    summary_txt_path = results_path / "summary.txt"
    with open(summary_txt_path, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("CROSS-ECOSYSTEM PACKAGE ANALYSIS SUMMARY\n")
        f.write("=" * 80 + "\n\n")

        f.write("INPUT STATISTICS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total Packages Inputted: {total_input_packages:,}\n")
        f.write(f"Total Valid Repositories (The count of unique normalized GitHub repository URLs across all input packages): {valid_packages_count:,}\n")
        f.write(f"Total Cross-Ecosystem Packages: {total_cross_ecosystem:,}\n")
        f.write(f"Percentage of Cross-Ecosystem Packages: {cross_ecosystem_percentage:.2f}%\n\n")

        f.write("PER-ECOSYSTEM STATISTICS\n")
        f.write("=" * 80 + "\n")
        f.write(ecosystem_stats_df.to_string(index=False) + "\n\n")

        f.write("SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(summary_df.to_string(index=False) + "\n\n")

        f.write("=" * 80 + "\n")
        f.write("STATISTICS BY ECOSYSTEM COUNT\n")
        f.write("=" * 80 + "\n")
        f.write(stats_df.to_string() + "\n\n")

        f.write("=" * 80 + "\n")
        f.write(f"All results saved to: {results_path}\n")
        f.write(f"Summary CSV saved to: {summary_path}\n")
        f.write(f"Summary TXT saved to: {summary_txt_path}\n")
        f.write("=" * 80 + "\n")

    print("\n" + "=" * 80)
    print("PER-ECOSYSTEM STATISTICS")
    print("=" * 80)
    print(ecosystem_stats_df.to_string(index=False))

    print("\n" + "=" * 80)
    print(f"All results saved to: {results_path}")
    print(f"Summary saved to: {summary_path}")
    print(f"Summary tables saved to: {summary_txt_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
