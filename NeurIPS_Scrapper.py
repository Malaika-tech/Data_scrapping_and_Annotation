import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

BASE_URL = "https://papers.nips.cc/paper_files/paper/2019"
OUTPUT_DIR = "nips_papers_2019"
CSV_FILE = "neurips_2019_papers.csv"
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_paper_links():
    """Fetch all paper titles and links from the NeurIPS 2019 page."""
    response = requests.get(BASE_URL, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"Failed to access {BASE_URL} (Status Code: {response.status_code})")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    papers = []

    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.endswith("-Abstract.html"):  
            paper_id = href.split("/")[-1].replace("-Abstract.html", "")
            abstract_url = f"{BASE_URL}/hash/{paper_id}-Abstract.html"
            pdf_url = f"{BASE_URL}/file/{paper_id}-Paper.pdf"
            title = link.text.strip()

            papers.append({"title": title, "abstract_url": abstract_url, "pdf_url": pdf_url})

    return papers

def download_paper(pdf_url):
    """Downloads the paper PDF."""
    pdf_name = pdf_url.split("/")[-1]
    pdf_path = os.path.join(OUTPUT_DIR, pdf_name)

    if os.path.exists(pdf_path):
        print(f"{pdf_name} already exists. Skipping...")
        return

    response = requests.get(pdf_url, headers=HEADERS, stream=True)
    if response.status_code != 200:
        print(f"Failed to download: {pdf_url} (Status Code: {response.status_code})")
        return

    total_size = int(response.headers.get("content-length", 0))

    with open(pdf_path, "wb") as file, tqdm(
        desc=pdf_name, total=total_size, unit="B", unit_scale=True
    ) as bar:
        for chunk in response.iter_content(chunk_size=1024):
            file.write(chunk)
            bar.update(len(chunk))

print(f"\nFetching papers from {BASE_URL}...")
papers = get_paper_links()

if not papers:
    print("No papers found. Exiting...")
else:
    print(f"Found {len(papers)} papers. Downloading...")

    # Save metadata to CSV
    df = pd.DataFrame(papers)
    df.to_csv(CSV_FILE, index=False)
    print(f"Metadata saved to {CSV_FILE}")

    # Download PDFs
    for paper in papers:
        download_paper(paper["pdf_url"])

print("\nAll papers downloaded successfully!")
