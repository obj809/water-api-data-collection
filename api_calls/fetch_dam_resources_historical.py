# api_calls/fetch_dam_resources_historical.py

import os
import json
from datetime import datetime
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.onegov.nsw.gov.au"
DAMS_ENDPOINT = f"{BASE_URL}/waternsw-waterinsights/v1/dams"
TOKEN_FILE = "oauth_token.json"
OUTPUT_DIR = "data/dam_resources_historical"

# Date range
START_DATE = "2015-01-01"

if not API_KEY:
    raise RuntimeError("API_KEY not set in .env file")


def load_token(filename=TOKEN_FILE):
    """Load the OAuth token from the saved JSON file."""
    if not os.path.exists(filename):
        raise RuntimeError(f"Token file '{filename}' not found. Run fetch_token.py first.")

    with open(filename, "r", encoding="utf-8") as f:
        token_data = json.load(f)

    access_token = token_data.get("access_token")
    if not access_token:
        raise RuntimeError(f"No 'access_token' found in {filename}")

    if "expires_at" in token_data:
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        if datetime.now() >= expires_at:
            raise RuntimeError(f"Token expired at {expires_at}. Run fetch_token.py to refresh.")

    print(f"Token loaded from {filename}")
    return access_token


def fetch_dams(access_token):
    """Fetch the list of all dams."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "apikey": API_KEY
    }

    print(f"Fetching dams list from {DAMS_ENDPOINT}...")
    response = requests.get(DAMS_ENDPOINT, headers=headers, timeout=15)

    if response.status_code == 200:
        data = response.json()
        dams = data.get("dams", data) if isinstance(data, dict) else data
        print(f"Found {len(dams)} dams")
        return dams
    else:
        raise RuntimeError(f"HTTP {response.status_code}: {response.text[:200]}")


def fetch_dam_resources(access_token, dam_id, start_date, end_date):
    """
    Fetch resources for a specific dam within a date range.

    Returns:
        list: Resource records, or empty list if none found
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "apikey": API_KEY
    }

    endpoint = f"{DAMS_ENDPOINT}/{dam_id}/resources"
    params = {
        "from": start_date,
        "to": end_date
    }

    response = requests.get(endpoint, headers=headers, params=params, timeout=60)

    if response.status_code == 200:
        data = response.json()
        # API returns: {"dams": [{"dam_id": ..., "resources": [...]}]}
        if isinstance(data, dict) and "dams" in data:
            dams = data.get("dams", [])
            if dams and isinstance(dams, list) and len(dams) > 0:
                return dams[0].get("resources", [])
        return []
    else:
        raise RuntimeError(f"HTTP {response.status_code}")


def fetch_all_dam_resources(access_token, dams_list, start_date, end_date):
    """Fetch resources for all dams in the list."""
    # Filter out aggregate dams that don't support the resources endpoint
    SKIP_DAMS = ["BlueMountainsTotal"]
    dams_list = [d for d in dams_list if d.get("dam_id") not in SKIP_DAMS]

    results = {}
    total = len(dams_list)

    print(f"\nFetching resources for {total} dams ({start_date} to {end_date})...\n")

    for i, dam in enumerate(dams_list, 1):
        dam_id = dam.get("dam_id")
        dam_name = dam.get("dam_name", "Unknown")

        if not dam_id:
            continue

        print(f"[{i}/{total}] {dam_name} ({dam_id})...", end=" ")

        try:
            resources = fetch_dam_resources(access_token, dam_id, start_date, end_date)
            results[dam_id] = {
                "dam_id": dam_id,
                "dam_name": dam_name,
                "start_date": start_date,
                "end_date": end_date,
                "record_count": len(resources),
                "resources": resources
            }
            print(f"{len(resources)} records")
        except RuntimeError as e:
            print(f"Error: {e}")
            results[dam_id] = {
                "dam_id": dam_id,
                "dam_name": dam_name,
                "start_date": start_date,
                "end_date": end_date,
                "record_count": 0,
                "resources": [],
                "error": str(e)
            }

    print(f"\nFetched resources for {len(results)} dams")
    return results


def save_dam_resources(resources_dict, output_dir=OUTPUT_DIR):
    """Save each dam's resources to a separate JSON file."""
    os.makedirs(output_dir, exist_ok=True)

    for dam_id, data in resources_dict.items():
        filename = os.path.join(output_dir, f"{dam_id}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(resources_dict)} files to {output_dir}/")


def main():
    """Main execution function."""
    print("=" * 60)
    print("WaterInsights API - Fetch Historical Dam Resources")
    print("=" * 60)

    end_date = datetime.now().strftime("%Y-%m-%d")

    try:
        access_token = load_token()
        dams = fetch_dams(access_token)
        resources = fetch_all_dam_resources(access_token, dams, START_DATE, end_date)
        save_dam_resources(resources)

        # Print summary
        total_records = sum(r["record_count"] for r in resources.values())
        print(f"\nTotal records collected: {total_records}")

        print("=" * 60)
        print("COMPLETE")
        print("=" * 60)

    except RuntimeError as e:
        print(f"\nERROR: {e}\n")
        exit(1)


if __name__ == "__main__":
    main()
