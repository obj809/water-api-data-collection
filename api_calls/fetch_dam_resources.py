# api_calls/fetch_dam_resources.py

import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.onegov.nsw.gov.au"
DAMS_ENDPOINT = f"{BASE_URL}/waternsw-waterinsights/v1/dams"
TOKEN_FILE = "oauth_token.json"
OUTPUT_DIR = "data/dam_resources"

if not API_KEY:
    raise RuntimeError("API_KEY not set in .env file")


def load_token(filename=TOKEN_FILE):
    """
    Load the OAuth token from the saved JSON file.

    Returns:
        str: The access token
    """
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

    print(f"✓ Token loaded from {filename}")
    return access_token


def fetch_dams(access_token):
    """
    Fetch the list of all dams from the WaterInsights API.

    Returns:
        list: The dams data
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "apikey": API_KEY
    }

    print(f"Fetching dams list from {DAMS_ENDPOINT}...")

    response = requests.get(DAMS_ENDPOINT, headers=headers, timeout=15)

    if response.status_code == 200:
        data = response.json()
        dams = data.get("dams", data) if isinstance(data, dict) else data
        print(f"✓ Retrieved {len(dams)} dams")
        return dams

    elif response.status_code == 401:
        raise RuntimeError("Authentication failed (401). Run fetch_token.py to refresh.")

    else:
        raise RuntimeError(f"HTTP {response.status_code}: {response.text[:200]}")


def fetch_dam_resources(access_token, dam_id, start_date, end_date):
    """
    Fetch resources for a specific dam within a date range.

    Returns:
        dict: The dam resources data
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

    response = requests.get(endpoint, headers=headers, params=params, timeout=30)

    if response.status_code == 200:
        return response.json()
    else:
        raise RuntimeError(f"HTTP {response.status_code}")


def fetch_all_dam_resources(access_token, dams_list, start_date, end_date):
    """
    Fetch resources for all dams in the list.

    Returns:
        dict: Mapping of dam_id to resources data
    """
    results = {}
    total = len(dams_list)

    print(f"\nFetching resources for {total} dams ({start_date} to {end_date})...")

    for i, dam in enumerate(dams_list, 1):
        dam_id = dam.get("dam_id")
        dam_name = dam.get("dam_name", "Unknown")

        if not dam_id:
            continue

        print(f"  [{i}/{total}] {dam_name} ({dam_id})...", end=" ")

        try:
            resources = fetch_dam_resources(access_token, dam_id, start_date, end_date)
            results[dam_id] = {
                "dam_id": dam_id,
                "dam_name": dam_name,
                "start_date": start_date,
                "end_date": end_date,
                "resources": resources
            }
            print("✓")
        except RuntimeError as e:
            print(f"✗ {e}")

    print(f"\n✓ Fetched resources for {len(results)}/{total} dams")
    return results


def save_dam_resources(resources_dict, output_dir=OUTPUT_DIR):
    """Save each dam's resources to a separate JSON file."""
    os.makedirs(output_dir, exist_ok=True)

    for dam_id, data in resources_dict.items():
        filename = os.path.join(output_dir, f"{dam_id}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved {len(resources_dict)} files to {output_dir}/")


def main():
    """Main execution function."""
    print("=" * 60)
    print("WaterInsights API - Fetch Dam Resources (Last Year)")
    print("=" * 60)

    # Calculate date range for last year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    try:
        access_token = load_token()
        dams = fetch_dams(access_token)
        resources = fetch_all_dam_resources(access_token, dams, start_str, end_str)
        save_dam_resources(resources)

        print("=" * 60)
        print("✓ COMPLETE")
        print("=" * 60)

    except RuntimeError as e:
        print(f"\n✗ ERROR: {e}\n")
        exit(1)


if __name__ == "__main__":
    main()
