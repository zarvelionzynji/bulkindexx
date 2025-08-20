import os
import sys
import subprocess
import importlib
import argparse
import time


# Function to check, install, or upgrade a library
def install_or_upgrade(pypi_name, import_name, min_version):
    try:
        # Try import module
        pkg = importlib.import_module(import_name)
        
        try:
            from packaging import version
            current_version = pkg.__version__
            if version.parse(current_version) < version.parse(min_version):
                print(f"Upgrading {pypi_name} from {current_version} to minimum {min_version}...")
                self_install(pypi_name, min_version)
        except ImportError:
            pass
            
    except ImportError:
        print(f"Installing {pypi_name} minimum version {min_version}...")
        self_install(pypi_name, min_version)

def self_install(pypi_name, min_version):
    """Try multiple installation methods"""
    methods = [
        # Method 1: Try --user first
        [sys.executable, "-m", "pip", "install", "--user", f"{pypi_name}>={min_version}"],
        # Method 2: Try without --user (for systems that allow it)
        [sys.executable, "-m", "pip", "install", f"{pypi_name}>={min_version}"],
        # Method 3: Try pip3 instead of pip
        [sys.executable, "-m", "pip3", "install", "--user", f"{pypi_name}>={min_version}"],
    ]
    
    for cmd in methods:
        try:
            print(f"Trying: {' '.join(cmd)}")
            subprocess.check_call(cmd, timeout=120)
            print(f"Successfully installed {pypi_name}")
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"Method failed: {e}")
            continue
    
    # If all methods failed
    print(f"\nFailed to install {pypi_name} automatically.")
    print(f"Please install manually using one of these methods:")
    print(f"1. pip install --user {pypi_name}>={min_version}")
    print(f"2. sudo pacman -S python-{pypi_name}  # For Arch Linux")
    print(f"3. sudo apt install python3-{pypi_name}  # For Debian/Ubuntu")
    print(f"4. Use virtual environment: python -m venv venv && source venv/bin/activate && pip install {pypi_name}")
    sys.exit(1)

# Ensure packaging module is available first
try:
    from packaging import version
except ImportError:
    print("Installing packaging module for version comparison...")
    self_install("packaging", "20.0")

# Now install/upgrade required dependencies
install_or_upgrade("google-auth", "google.auth", "2.0.0")
install_or_upgrade("requests", "requests", "2.20.0")

# Now import the modules that might need the installed dependencies
import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
# Configuration
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/indexing"]
GOOGLE_KEY_FILE = "service_account.json"
INDEXNOW_API_KEY = "YOUR_INDEX_API_KEY"
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
LOG_FILE = "bulk_index.log"
GOOGLE_DELAY = 2
INDEXNOW_DELAY = 1

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
    
    total = len(urls)
    delay = GOOGLE_DELAY
    print(f"Starting Google Indexing API for {total} URLs...")
    
    for i, url in enumerate(urls):
        print(f"Processing {i+1}/{total}: {url}")
        
        payload = {"url": url, "type": "URL_UPDATED"}
        resp = authed_session.post(
            "https://indexing.googleapis.com/v3/urlNotifications:publish",
            json=payload
        )
        log_result("Google", url, resp.status_code, resp.text)
        
        # Adding delay
        if i < total - 1:
            time.sleep(delay)
            print(f"Waiting {delay:.1f} seconds... ({i+1}/{total} completed)")

# Submit URLs to IndexNow
def indexnow_api(urls, blogger_mode=False):
    total = len(urls)
    delay = INDEXNOW_DELAY
    print(f"Starting IndexNow for {total} URLs...")

    for i, url in enumerate(urls):
        print(f"Processing {i+1}/{total}: {url}")

        payload = {
            "host": url.split("/")[2],
            "key": INDEXNOW_API_KEY,
            "urlList": [url]
        }
        
        if not blogger_mode:
            payload["keyLocation"] = f"https://{url.split('/')[2]}/{INDEXNOW_API_KEY}.txt"
            
        resp = requests.post(INDEXNOW_ENDPOINT, json=payload)
        log_result("IndexNow", url, resp.status_code, resp.text)
        
        # Dynamic delay based on response
        if resp.status_code == 429:  # Too Many Requests
            delay *= 2  # Double the delay
            print(f"Rate limited! Increasing delay to {delay:.1f} seconds")
        elif resp.status_code == 200:
            delay = max(0.5, delay * 0.9)  # Gradually reduce delay if successful
        
        if i < len(urls) - 1:
            time.sleep(delay)
            print(f"Waiting {delay:.1f} seconds... ({i+1}/{total} completed)")

# Logging with status code explanation
def log_result(api_name, url, status, text):
    status_desc = STATUS_EXPLANATION.get(status, "Unknown status")
    if text.strip():
        log_line = f"{api_name}: {url} → {status} ({status_desc}) | Response: {text}\n"
    else:
        log_line = f"{api_name}: {url} → {status} ({status_desc})\n"
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
