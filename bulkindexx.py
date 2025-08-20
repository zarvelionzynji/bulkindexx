import os
import sys
import subprocess
import importlib
import argparse
import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

# Function to check, install, or upgrade a library
def install_or_upgrade(pypi_name, import_name, min_version):
    try:
        pkg = importlib.import_module(import_name)
        from packaging import version
        current_version = pkg.__version__
        if version.parse(current_version) < version.parse(min_version):
            print(f"Upgrading {pypi_name} from {current_version} to minimum {min_version}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", f"{pypi_name}>={min_version}", "--upgrade"])
        # else:
            # print(f"{pypi_name} version {current_version} meets the requirement.")
    except ImportError:
        print(f"Installing {pypi_name} minimum version {min_version}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", f"{pypi_name}>={min_version}"])

# Ensure required libraries are installed and meet minimum versions
install_or_upgrade("google-auth", "google.auth", "2.0.0")
install_or_upgrade("requests", "requests", "2.20.0")

# Configuration
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/indexing"]
GOOGLE_KEY_FILE = "service_account.json"
INDEXNOW_API_KEY = "xxx"
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
LOG_FILE = "bulk_index.log"

# Status code explanations
STATUS_EXPLANATION = {
    200: "OK, accepted and processed immediately",
    202: "Accepted, received and queued for processing",
    400: "Bad Request, invalid data or format",
    403: "Forbidden, incorrect or unauthorized API key",
    404: "Not Found, endpoint or keyLocation not found",
    429: "Too Many Requests, temporarily blocked",
    500: "Internal Server Error on server side",
    503: "Service Unavailable, server busy or maintenance"
}

# Load URLs from file
def load_urls(file_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return []
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]

# Submit URLs to Google Indexing API
def google_indexing_api(urls):
    credentials = service_account.Credentials.from_service_account_file(
        GOOGLE_KEY_FILE, scopes=GOOGLE_SCOPES
    )
    authed_session = AuthorizedSession(credentials)

    for url in urls:
        payload = {"url": url, "type": "URL_UPDATED"}
        resp = authed_session.post(
            "https://indexing.googleapis.com/v3/urlNotifications:publish",
            json=payload
        )
        log_result("Google", url, resp.status_code, resp.text)

# Submit URLs to IndexNow
def indexnow_api(urls, blogger_mode=False):
    for url in urls:
        payload = {
            "host": url.split("/")[2],
            "key": INDEXNOW_API_KEY,
            "urlList": [url]
        }
        
        if not blogger_mode:
            payload["keyLocation"] = f"https://{url.split('/')[2]}/{INDEXNOW_API_KEY}.txt"
            
        resp = requests.post(INDEXNOW_ENDPOINT, json=payload)
        log_result("IndexNow", url, resp.status_code, resp.text)

# Logging with status code explanation
def log_result(api_name, url, status, text):
    status_desc = STATUS_EXPLANATION.get(status, "Unknown status")
    log_line = f"{api_name}: {url} → {status} ({status_desc}) | Response: {text}\n"
    print(log_line.strip())
    with open(LOG_FILE, "a") as log:
        log.write(log_line)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage:\n")
        print("  python bulkindexx.py --url urls.txt")
        print("  python bulkindexx.py --url https://example.com --only google")
        print("  python bulkindexx.py --url urls.txt --blogger\n")
        print("Use --help for more information.\n")
        sys.exit(0)

    parser = argparse.ArgumentParser(description="Bulk submit URLs to Google Indexing API and IndexNow")
    parser.add_argument("--url", required=True, help="Single URL or path to a file containing list of URLs")
    parser.add_argument("--only", choices=["google", "indexnow"], help="Send requests only to Google or IndexNow")
    parser.add_argument("--blogger", action="store_true", help="Blogger mode: exclude keyLocation from IndexNow payload")
    args = parser.parse_args()

    if os.path.isfile(args.url):
        urls = load_urls(args.url)
    else:
        urls = [args.url]

    if not urls:
        print("No URLs to process.")
        sys.exit(1)

    if args.only == "google":
        print("Sending to Google Indexing API...")
        google_indexing_api(urls)
    elif args.only == "indexnow":
        print("Sending to IndexNow...")
        indexnow_api(urls, blogger_mode=args.blogger)
    else:
        print("Sending to Google Indexing API...")
        google_indexing_api(urls)
        print("\nSending to IndexNow...")
        indexnow_api(urls, blogger_mode=args.blogger)

    print(f"\nDone. Log saved to {LOG_FILE}")
