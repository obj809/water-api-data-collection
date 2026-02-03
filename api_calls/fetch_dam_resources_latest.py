# api_calls/fetch_dam_resources_latest.py

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
OUTPUT_FILE = "data/dams_resources_latest.json"

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


def fetch_dam_resources_latest(access_token, dam_id):
    """
    Fetch the latest resources for a specific dam.

    Returns:
        dict: The latest dam resources data
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "apikey": API_KEY
    }

    endpoint = f"{DAMS_ENDPOINT}/{dam_id}/resources/latest"
    response = requests.get(endpoint, headers=headers, timeout=15)

    if response.status_code == 200:
        return response.json()
    else:
        raise RuntimeError(f"HTTP {response.status_code}")


def fetch_all_dam_resources_latest(access_token, dams_list):
    """
    Fetch latest resources for all dams in the list.

    Returns:
        list: List of latest resources for each dam
    """
    results = []
    total = len(dams_list)

    print(f"\nFetching latest resources for {total} dams...")

    for i, dam in enumerate(dams_list, 1):
        dam_id = dam.get("dam_id")
        dam_name = dam.get("dam_name", "Unknown")

        if not dam_id:
            continue

        print(f"  [{i}/{total}] {dam_name} ({dam_id})...", end=" ")

        try:
            data = fetch_dam_resources_latest(access_token, dam_id)
            # Extract the dam data from the response
            dams_data = data.get("dams", [])
            if dams_data:
                results.append(dams_data[0])
            print("✓")
        except RuntimeError as e:
            print(f"✗ {e}")

    print(f"\n✓ Fetched latest resources for {len(results)}/{total} dams")
    return results


def save_json(data, filename):
    """Save data to a JSON file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved to {filename}")


def main():
    """Main execution function."""
    print("=" * 60)
    print("WaterInsights API - Fetch Latest Dam Resources")
    print("=" * 60)

    try:
        access_token = load_token()
        dams = fetch_dams(access_token)
        latest_resources = fetch_all_dam_resources_latest(access_token, dams)
        save_json(latest_resources, OUTPUT_FILE)

        print("=" * 60)
        print("✓ COMPLETE")
        print("=" * 60)

    except RuntimeError as e:
        print(f"\n✗ ERROR: {e}\n")
        exit(1)


if __name__ == "__main__":
    main()
