# Package-Dataset

This repo contains registry lists, cross-ecosystem lists, and directory structure of packages from Crates, Maven, PyPI, PHP, Go, NPM, and Ruby.

The original scripts used to mine or analyze the lists are also uploaded in this repository. You can navigate the the corresponding script and run it locally for latest results.

![general-map](https://github.com/user-attachments/assets/20b73733-fdea-43f9-88db-7c6b6bf7d572)

# How to Use

Download the dataset you are interested in directly from the repo.

> **ATTENTION**
>
> Since some of the files are very large in size, `git lfs` is used in this repo. Before you clone this repo, make sure `git lfs` has been installed on your machine. See [git lfs](https://git-lfs.com/) for more information.
>
> After cloning the repo, you will need to set up `git lfs` in the repo to view all the files properly. Run the following code in the repository folder:
>
> ```bash
> git lfs install
> git lfs pull
> ```
>
> Then you should see the actual contents from the files properly.

# Folder

## Package-List

Contains the whole lists of packages in the corresponding ecosystem.

- File Type: `.csv`
- Columns: ID,Platform,Name,Homepage URL,Repository URL

### Crates

- Source: https://static.crates.io/db-dump.tar.gz
- Description: Crates provides us with the whole database dump file. We can get the necessary information directly from it.
- Mine Date: 2025-01-15
- Total: 217,726
- Valid: 111,799

### Go

- Source: https://index.golang.org/index (module path), https://proxy.golang.org/{module_path}/@v/list (latest version), https://proxy.golang.org/{module_path}/@v/{latest_version}.info (metadata), https://proxy.golang.org/{module_path}/@v/{latest_version}.mod (repo URL)
- Description:
  1. Fetch index file only for module path, the index contains ALL versions of modules, so we deduplicate by module path.
  2. Use the Go proxy API to get the latest version info.
  3. Fetch the .info file which contains metadata.
  4. The info file doesn't have repo URL, so fetch go.mod.
- Mine Date: 2025-12-15
- Total: 2,164,784
- Valid: 518,795

### Maven

- Source: https://repo1.maven.org/maven2/.index/
- Description:
  1. Maven provides a pre-built complete package name set.
- Mine Date: 2025-01-15
- Total: 762,368
- Valid: 134,994

### NPM

- Source: https://replicate.npmjs.com/_all_docs (package name), https://registry.npmjs.org/{package_name} (repo URL)
- Description: `npm` provides an all-docs endpoint that returns all package names. Use the names we can fetch information for `npm` packages using API.
- Mine Date: 2025-11-30
- Total: 3,706,504
- Valid: 1,363,719

### PHP

- Source: https://packagist.org/packages/list.json (package name), https://packagist.org/packages/{package_name}.json (repo URL)
- Description: Mines Packagist.org to get the whole list of `PHP` packages, and then fetch information for the packages.
- Mine Date: 2025-12-1
- Total: 431,457
- Valid: 403,564

### PyPI

- Source: https://pypi.org/simple/ (package name), https://pypi.org/pypi/{package_name}/json (repo URL)
- Description: PyPI simple API provides a list of all packages. Using the names we can fetch information for PyPI packages.
- Mine Date: 2025-11-30
- Total: 705,908
- Valid: 338,601

### Ruby

- Source: http://rubygems.org/names (gem name), https://rubygems.org/api/v1/gems/{gem_name}.json (repo URL)
- Description: Fetch gem names from RubyGems API and fetch information for gems.
- Mine Date: 2025-12-1
- Total: 188,991
- Valid: 129,934

## Common-Package

Contains the filtered packages which appear in multiple package lists. There are in total 120 possible combinations, while eventually 84 combinations hold matched results.

- File Type: `.csv`
- Matching Criteria: Same repo URL

## Directory-Structure

Contains the directory structures of packages inside each common packages lists. The directory structure is mined using the [REST API endpoint of git tree](https://docs.github.com/en/rest/git/trees). Some of the packages cannot be mined because the repo is either deleted or non-accessible.

- File Type: `.txt`

## Script

Contains the scripts of getting the dataset. Clone what you are interested and run it locally to get latest information.

There are detailed documentation under the folder of each script.

> The input and output path has been modified to match the current file layout.
