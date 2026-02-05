# api_calls/check_history_depth.py

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

# Date range to check - from this date to today
CHECK_FROM_DATE = "1970-01-01"

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

    response = requests.get(DAMS_ENDPOINT, headers=headers, timeout=15)

    if response.status_code == 200:
        data = response.json()
        dams = data.get("dams", data) if isinstance(data, dict) else data
        return dams
    else:
        raise RuntimeError(f"HTTP {response.status_code}: {response.text[:200]}")


def fetch_resources_for_date_range(access_token, dam_id, start_date, end_date):
    """
    Fetch resources for a dam within a date range.

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

    response = requests.get(endpoint, headers=headers, params=params, timeout=30)

    if response.status_code == 200:
        data = response.json()
        # API returns: {"dams": [{"dam_id": ..., "resources": [...]}]}
        if isinstance(data, dict) and "dams" in data:
            dams = data.get("dams", [])
            if dams and isinstance(dams, list) and len(dams) > 0:
                return dams[0].get("resources", [])
        return []
    else:
        return []


def check_all_dams_history(access_token, dams_list):
    """
    Check history depth for all dams from CHECK_FROM_DATE to today.
    """
    results = []
    total = len(dams_list)
    today = datetime.now().strftime("%Y-%m-%d")

    print(f"\nChecking records from {CHECK_FROM_DATE} to {today} for {total} dams...\n")

    for i, dam in enumerate(dams_list, 1):
        dam_id = dam.get("dam_id")
        dam_name = dam.get("dam_name", "Unknown")

        if not dam_id:
            continue

        print(f"[{i}/{total}] {dam_name} ({dam_id})...", end=" ")

        records = fetch_resources_for_date_range(
            access_token, dam_id, CHECK_FROM_DATE, today
        )

        if records:
            # Find earliest and latest dates in records
            dates = [r.get("date") for r in records if r.get("date")]
            dates.sort()
            earliest = dates[0] if dates else None
            latest = dates[-1] if dates else None

            print(f"{len(records)} records ({earliest} to {latest})")
            results.append({
                "dam_id": dam_id,
                "dam_name": dam_name,
                "record_count": len(records),
                "earliest_date": earliest,
                "latest_date": latest
            })
        else:
            print("No data")
            results.append({
                "dam_id": dam_id,
                "dam_name": dam_name,
                "record_count": 0,
                "earliest_date": None,
                "latest_date": None
            })

    return results


def main():
    """Main execution function."""
    print("=" * 60)
    print("WaterInsights API - Check History Depth")
    print("=" * 60)

    try:
        access_token = load_token()

        print("\nFetching dams list...")
        dams = fetch_dams(access_token)
        print(f"Found {len(dams)} dams")

        results = check_all_dams_history(access_token, dams)

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        dams_with_data = [r for r in results if r["earliest_date"]]

        if dams_with_data:
            # Sort by earliest date
            dams_with_data.sort(key=lambda x: x["earliest_date"])

            print(f"\nDams with data: {len(dams_with_data)}/{len(results)}")
            print(f"\nEarliest records by dam:")
            print("-" * 60)

            for r in dams_with_data:
                print(f"  {r['earliest_date']}  {r['dam_name']} ({r['record_count']} records)")

            print("-" * 60)
            print(f"\nOverall earliest: {dams_with_data[0]['earliest_date']} ({dams_with_data[0]['dam_name']})")
            print(f"Overall latest start: {dams_with_data[-1]['earliest_date']} ({dams_with_data[-1]['dam_name']})")
        else:
            print("\nNo data found for any dams.")

        # Save results
        output_file = "data/history_depth.json"
        os.makedirs("data", exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "checked_at": datetime.now().isoformat(),
                "check_from_date": CHECK_FROM_DATE,
                "dams_checked": len(results),
                "dams_with_data": len(dams_with_data),
                "results": results
            }, f, indent=2)

        print(f"\nResults saved to {output_file}")
        print("=" * 60)

    except RuntimeError as e:
        print(f"\nERROR: {e}\n")
        exit(1)


if __name__ == "__main__":
    main()
