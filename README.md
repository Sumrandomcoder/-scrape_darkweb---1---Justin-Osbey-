# Dark Web Scraper

Python script for scraping .onion sites with Tor anonymity.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Tor:
```bash
python tor_setup.py
```

3. Test installation:
```bash
python test.py
```

4. Run scraper:
```bash
python scraper.py
```

## Configuration

Edit `config.py` to modify:
- Target sites
- Data types to extract
- Content filters
- Tor ports

## Output

Generates:
- `scraped_data_TIMESTAMP.json` - Complete data
- `scraped_data_TIMESTAMP_emails.txt` - Emails only
- `scraped_data_TIMESTAMP_usernames.txt` - Usernames only
- `scraped_data_TIMESTAMP_phone_numbers.txt` - Phone numbers only

## Features

- Tor anonymity
- Anti-detection measures
- Content filtering
- Data extraction (emails, usernames, phone numbers)
- Multiple output formats

## Legal Notice

For educational/research purposes only. Ensure compliance with local laws.
