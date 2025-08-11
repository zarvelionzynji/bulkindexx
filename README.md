# Bulk URL Indexing Script

This Python script submits URLs to Google Indexing API and IndexNow for faster indexing. It supports bulk submission from a file or a single URL. The script automatically installs or upgrades required libraries and provides clear logging with HTTP status explanations.

## Features

* Submit one or many URLs to Google Indexing API and IndexNow.
* Automatic installation or upgrade of required Python libraries.
* Supports reading URLs from a file or accepting a single URL.
* Option to submit only to Google or only to IndexNow.
* Detailed logging with HTTP status code explanations.
* Displays usage instructions when run without arguments.

## Requirements

* Python 3.6 or higher
* Google service account JSON key file (`service_account.json`) with indexing API access
* IndexNow API key

## Setup

1. Place your Google service account JSON file as `service_account.json` in the script directory and add email in the JSON file to Google Search Console as Owner.
2. Replace `INDEXNOW_API_KEY = "xxx"` in the script with your actual IndexNow API key.
3. Prepare your URLs:

   * For multiple URLs, create a text file (`urls.txt`) with one URL per line.
   * For single URL submission, use the URL directly as argument.

## Usage

Run the script with Python:

```bash
python bulkindexx.py --url urls.txt
```

Or for a single URL:

```bash
python bulkindexx.py --url https://blog.zynji.my.id
```

Submit only to Google:

```bash
python bulkindexx.py --url https://blog.zynji.my.id --only google
```

Submit only to IndexNow:

```bash
python bulkindexx.py --url https://blog.zynji.my.id --only indexnow
```

Run without arguments to see usage instructions:

```bash
python bulkindexx.py
```

## Logging

* Logs are saved in `bulk_index.log`.
* Each entry includes API name, URL, HTTP status code with explanation, and response text.

## Notes

* Make sure your environment can install Python packages if needed.
* Google service account must have permission for the Indexing API.
* IndexNow requires the API key file placed on your site at the specified location.

## Learn More

Read detailed tutorials and guides on my blog:
* [Bulk Indexing with Google and IndexNow](https://blog.zynji.my.id/posts/bulkindexx-script-otomatisasi-submit-url-ke-google-indexing-api-dan-indexnow/)

## License

MIT License

---

