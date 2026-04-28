import requests
from bs4 import BeautifulSoup
import re
from bs4 import XMLParsedAsHTMLWarning
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Purpose: downloads the SEC ticker lookup file
# Input: headers (username and email used to search)
# Output: a dictionary of companies containing info like: name, ticker, and CIK
def get_company_tickers(headers):
    url = "https://www.sec.gov/files/company_tickers.json"
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

# Purpose: searches the lookup table for the ticker and returns the CIK
# Input: ticker like "NVDA"
#        full company dataset
# Output: raw CIK like 1045810
def get_cik_from_ticker(ticker, company_data):
    ticker = ticker.upper()
    for value in company_data.values():
        if value["ticker"] == ticker:
            return value["cik_str"]
    return None

# Purpose: converts raw CIK to SEC-ready format with leading zeros
# Input: 1045810
# Output: "0001045810"
def format_cik(cik):
    return str(cik).zfill(10)

# Purpose: gets the full submissions JSON for one company
# Input: formatted CIK
#        headers
# Output: company-specific SEC JSON
def get_submissions_data(formatted_cik, headers):
    url = f"https://data.sec.gov/submissions/CIK{formatted_cik}.json"
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

# Purpose: extracts the recent filings table
# Input: full submission JSON
# Output: just the recent filings section
def get_recent_filings(submissions_data):
    return submissions_data["filings"]["recent"]

# Purpose: finds which rows correspond to 10-K filings
# Input: recent filings table
# Output: list of row indices like [37, 122, 216, ...]
def get_10k_indices(recent_filings):
    indices = []
    
    for i, form in enumerate(recent_filings["form"]):
        if form == "10-K":
            indices.append(i)
            
    return indices

# Purpose: converts those 10-K row positions into clean filing records, pulls the ascession number, filing date, etc from the row.
# Input: recent filings
#        10-K indices
# Output: list of dictionaries, one per 10-K
def get_10k_metadata(recent_filings, ten_k_indices):
    ten_k_list = []

    for i in ten_k_indices:
        filing_info = {
            "filing_date": recent_filings["filingDate"][i],
            "accession_number": recent_filings["accessionNumber"][i],
            "primary_document": recent_filings["primaryDocument"][i],
            "form": recent_filings["form"][i]
        }
        ten_k_list.append(filing_info)

    return ten_k_list

# Purpose: constructs the direct SEC filing URL
# Input: company CIK
#        accession number
#        document name
# Output: direct URL to the filing
def build_filing_url(formatted_cik, accession_number, primary_document):
    accession_no_dash = accession_number.replace("-", "")
    
    filing_url = (
        f"https://www.sec.gov/Archives/edgar/data/"
        f"{formatted_cik}/{accession_no_dash}/{primary_document}"
    )
    
    return filing_url

# Purpose: convert filing HTML into rough plain text
# Input: raw HTML string from SEC filing
# Output: plain text string with line breaks
def html_to_text(html):
    soup = BeautifulSoup(html, "lxml")
    return soup.get_text("\n")

# Purpose: download the full HTML content of a filing
# Input: filing URL, headers
# Output: raw HTML string
def get_filing_html(filing_url, headers):
    response = requests.get(filing_url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text

# Purpose: extract the MD&A section from a 10-K filing
# Input: full filing text (plain text)
# Output: substring containing MD&A section (Item 7 → Item 7A or Item 8)
def extract_mda_section(filing_text):
    text_lower = filing_text.lower()

    item_7_matches = list(re.finditer(r"item\s+7\.", text_lower))
    item_7a_matches = list(re.finditer(r"item\s+7a\.", text_lower))
    item_8_matches = list(re.finditer(r"item\s+8\.", text_lower))

    if len(item_7_matches) < 2:
        return None

    start = item_7_matches[1].start()

    end_candidates = []

    for match in item_7a_matches:
        if match.start() > start:
            end_candidates.append(match.start())

    for match in item_8_matches:
        if match.start() > start:
            end_candidates.append(match.start())

    if not end_candidates:
        return None

    end = min(end_candidates)

    return filing_text[start:end].strip()

# Purpose: save extracted MD&A text to a company-specific folder
# Input: ticker, filing date, MD&A text
# Output: file path where the text was saved
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"

def save_mda_to_file(ticker, filing_date, mda_text):
    ticker = ticker.upper()
    year = filing_date.split("-")[0]

    folder = DATA_DIR / ticker
    folder.mkdir(parents=True, exist_ok=True)

    file_path = folder / f"{ticker}_{year}_MDA.txt"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(mda_text)

    return str(file_path)

def scrape_and_save_mdas(ticker, limit=5):
    HEADERS = {
        "User-Agent": "Seymore seymorebuts67@gmail.com"
    }

    ticker = ticker.upper()

    company_data = get_company_tickers(HEADERS)
    cik = get_cik_from_ticker(ticker, company_data)
    formatted_cik = format_cik(cik)

    submissions_data = get_submissions_data(formatted_cik, HEADERS)
    recent_filings = get_recent_filings(submissions_data)
    ten_k_indices = get_10k_indices(recent_filings)
    ten_k_metadata = get_10k_metadata(recent_filings, ten_k_indices)

    latest_10ks = ten_k_metadata[:limit]
    mda_results = []

    for filing in latest_10ks:
        filing_url = build_filing_url(
            formatted_cik,
            filing["accession_number"],
            filing["primary_document"]
        )

        html = get_filing_html(filing_url, HEADERS)
        filing_text = html_to_text(html)
        mda_text = extract_mda_section(filing_text)

        if mda_text is None:
            continue

        file_path = save_mda_to_file(
            ticker,
            filing["filing_date"],
            mda_text
        )

        filing_record = {
            "ticker": ticker,
            "filing_date": filing["filing_date"],
            "filing_url": filing_url,
            "file_path": file_path
        }

        mda_results.append(filing_record)

    return mda_results