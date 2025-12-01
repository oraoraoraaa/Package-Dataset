import requests
import csv
import os
import time
import xml.etree.ElementTree as ET
import re
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

def get_pom_info(group_id, artifact_id, version):
    """
    Fetches the POM file from Maven Central and extracts Homepage and SCM URL.
    """
    homepage_url = "nan"
    repo_url = "nan"
    
    if not version:
        return homepage_url, repo_url

    group_path = group_id.replace('.', '/')
    pom_url = f"https://repo1.maven.org/maven2/{group_path}/{artifact_id}/{version}/{artifact_id}-{version}.pom"
    
    try:
        response = requests.get(pom_url, timeout=5)
        if response.status_code == 200:
            try:
                content = response.text
                # Remove xmlns to simplify parsing
                content = re.sub(r' xmlns="[^"]+"', '', content, count=1)
                
                root = ET.fromstring(content)
                
                # Find Homepage URL
                url_elem = root.find('url')
                if url_elem is not None and url_elem.text:
                    homepage_url = url_elem.text.strip()
                
                # Find SCM URL
                scm_url_elem = root.find('scm/url')
                if scm_url_elem is not None and scm_url_elem.text:
                    repo_url = scm_url_elem.text.strip()

            except ET.ParseError:
                pass
    except Exception:
        pass
        
    return homepage_url, repo_url

def mine_maven_packages():
    # Output path
    output_file = os.path.abspath(os.path.dirname(__file__))
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    base_url = "https://search.maven.org/solrsearch/select"
    batch_size = 200
    start = 0
    
    print("Starting Maven package mining...")
    
    # Get total count
    try:
        initial_resp = requests.get(base_url, params={'q': '*:*', 'rows': 0, 'wt': 'json'}, timeout=30).json()
        total_found = initial_resp['response']['numFound']
        print(f"Total artifacts to mine: {total_found}")
    except Exception as e:
        print(f"Failed to get total count: {e}")
        return

    # Open CSV file
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Platform', 'Name', 'Homepage URL', 'Repository URL'])
        
        current_id = 1
        pbar = tqdm(total=total_found, unit='pkg')
        
        while True:
            params = {
                'q': '*:*',
                'rows': batch_size,
                'start': start,
                'wt': 'json'
            }
            
            try:
                response = requests.get(base_url, params=params, timeout=30)
                if response.status_code != 200:
                    print(f"Error fetching batch: {response.status_code}")
                    time.sleep(5)
                    continue
                    
                data = response.json()
                docs = data.get('response', {}).get('docs', [])
                
                if not docs:
                    break
                
                # Prepare tasks
                tasks = []
                for doc in docs:
                    tasks.append((doc.get('g'), doc.get('a'), doc.get('latestVersion')))
                
                # Execute in parallel
                results = []
                with ThreadPoolExecutor(max_workers=50) as executor:
                    futures = [executor.submit(get_pom_info, g, a, v) for g, a, v in tasks]
                    for future in futures:
                        results.append(future.result())
                
                # Write results
                for i, doc in enumerate(docs):
                    g = doc.get('g')
                    a = doc.get('a')
                    name = f"{g}:{a}"
                    homepage, repo = results[i]
                    
                    # Validation
                    if not homepage or not homepage.startswith('http'): homepage = "nan"
                    if not repo or not repo.startswith('http'): repo = "nan"
                    
                    writer.writerow([current_id, "Maven", name, homepage, repo])
                    current_id += 1
                
                f.flush()
                pbar.update(len(docs))
                
                start += len(docs)
                
                # If we got fewer docs than requested, we are done
                if len(docs) < batch_size:
                    break
                
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(5)
                continue
                
        pbar.close()
    print(f"Mining completed. Results saved to {output_file}")

if __name__ == "__main__":
    mine_maven_packages()
