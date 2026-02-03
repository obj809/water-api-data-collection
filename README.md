# water-api-data-collection

Python scripts for collecting water data from the NSW WaterInsights API.

## Setup

1. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API credentials:
   ```
   API_KEY=your_api_key
   API_SECRET=your_api_secret
   ```

   Get credentials by registering at https://api.nsw.gov.au and subscribing to the WaterInsights API.

## Usage

First, fetch an OAuth token (valid for ~12 hours):
```bash
python api_calls/fetch_token.py
```

Then run any of the data collection scripts:
```bash
python api_calls/fetch_dams.py               # List of all dams
python api_calls/fetch_dam_details.py        # Details for each dam
python api_calls/fetch_dam_resources.py      # Historical resources (last year)
python api_calls/fetch_dam_resources_latest.py  # Latest resources
```

## Output Files

| Script | Output |
|--------|--------|
| `fetch_token.py` | `oauth_token.json` |
| `fetch_dams.py` | `data/dams.json` |
| `fetch_dam_details.py` | `data/dams_dam_id.json` |
| `fetch_dam_resources.py` | `data/dam_resources/{dam_id}.json` |
| `fetch_dam_resources_latest.py` | `data/dams_resources_latest.json` |

## API Reference

- Base URL: `https://api.onegov.nsw.gov.au`
- Documentation: https://api.nsw.gov.au/Product/Index/26
