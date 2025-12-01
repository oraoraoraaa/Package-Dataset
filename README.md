# Package-Dataset
This repo contains registry lists, cross-ecosystem lists, and directory structure of packages from Crates, Maven, PyPI, PHP, Go, NPM, and Ruby.

The original scripts used to mine or analyze the lists are also uploaded in this repository. You can navigate the the corresponding script and run it locally for latest results.

![general-map](https://github.com/user-attachments/assets/fd768faf-5d73-4eae-b180-6138d1db0598)

# How to Use
Download the dataset you are interested in directly from the repo.

# Folders
## Package-Lists
Contains the whole lists of packages in the corresponding ecosystem.
- File Type: `.csv`
- Columns: ID,Platform,Name,Homepage URL,Repository URL

### Crates
- Source: https://static.crates.io/db-dump.tar.gz
- Description: Crates provides us with the whole database dump file. We can get the necessary information directly from it.

### Go
- Source: https://index.golang.org/index (module path), https://proxy.golang.org/{module_path}/@v/list (latest version), https://proxy.golang.org/{module_path}/@v/{latest_version}.info (metadata), https://proxy.golang.org/{module_path}/@v/{latest_version}.mod (repo URL)
- Description:
  1. Fetch index file only for module path, the index contains ALL versions of modules, so we deduplicate by module path.
  2. Use the Go proxy API to get the latest version info.
  3. Fetch the .info file which contains metadata.
  4. The info file doesn't have repo URL, so fetch go.mod.
- Additional Notes:
  1. Domain name `gopkg.in` redirects to GitHub. So it's converted to a github link.
  2. Custom domain names are preserved.
 
### Maven
- Source: https://search.maven.org/solrsearch/select (artifacts metadata), https://repo1.maven.org/maven2/{group_path}/{artifact_id}/{version}/{artifact_id}-{version}.pom (repo URL)
- Description:
  1. Use the `search` api to get the total number of packages as well as metadata of them.
  2. Construct the url to `POM` file and fetch it. Extract information from the `POM` file.

### NPM
- Source: https://replicate.npmjs.com/_all_docs (package name), https://registry.npmjs.org/{package_name} (repo URL)
- Description: `npm` provides an all-docs endpoint that returns all package names. Use the names we can fetch information for `npm` packages using API.

### PHP
- Source: https://packagist.org/packages/list.json (package name), https://packagist.org/packages/{package_name}.json (repo URL)
- Description: Mines Packagist.org to get the whole list of `PHP` packages, and then fetch information for the packages.

### PyPI
- Source: https://pypi.org/simple/ (package name), https://pypi.org/pypi/{package_name}/json (repo URL)
- Description: PyPI simple API provides a list of all packages. Using the names we can fetch information for PyPI packages.

### Ruby
- Source: http://rubygems.org/names (gem name), https://rubygems.org/api/v1/gems/{gem_name}.json (repo URL)
- Description: Fetch gem names from RubyGems API and fetch information for gems.

## Common-Packages
Contains the filtered packages which appear in multiple package lists. There are in total 120 possible combinations, while eventually 71 combinations hold matched results.
- File Type: `.csv`
- Matching Criteria: Same repo URL

## Directory-Structures
Contains the directory structures of packages inside each common packages lists. The directory structure is mined using the [REST API endpoint of git tree](https://docs.github.com/en/rest/git/trees). Some of the packages cannot be mined because the repo is either deleted or non-accessible.
- File Type: `.txt`

## Scripts
Contains the scripts of getting the dataset. Clone what you are interested and run it locally to get latest information.

There are detailed documentation under the folder of each script.
