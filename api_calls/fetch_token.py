# api_calls/fetch_token.py

import os
import base64
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BASE_URL = "https://api.onegov.nsw.gov.au"
TOKEN_ENDPOINT = f"{BASE_URL}/oauth/client_credential/accesstoken"
TOKEN_FILE = "oauth_token.json"

# Validate required environment variables
if not API_KEY:
    raise RuntimeError("API_KEY not set in .env file")
if not API_SECRET:
    raise RuntimeError("API_SECRET not set in .env file")


def get_access_token():
    """
    Authenticate with the API and obtain an access token.

    Returns:
        dict: The full token response from the API

    Raises:
        RuntimeError: If authentication fails
    """
    credentials = f"{API_KEY}:{API_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    params = {"grant_type": "client_credentials"}
    headers = {"Authorization": f"Basic {encoded_credentials}"}

    print("Authenticating with WaterInsights API...")
    print(f"Endpoint: {TOKEN_ENDPOINT}")

    try:
        response = requests.get(TOKEN_ENDPOINT, headers=headers, params=params, timeout=15)
        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            token_data = response.json()
            if "access_token" not in token_data:
                raise RuntimeError("Response missing 'access_token' field")
            print("✓ Authentication successful!")
            return token_data

        elif response.status_code == 401:
            error_detail = ""
            try:
                error_data = response.json()
                error_detail = f"\nError: {error_data.get('Error', 'Unknown error')}"
            except:
                error_detail = f"\nResponse: {response.text}"
            raise RuntimeError(f"Authentication failed (401 Unauthorized){error_detail}")

        else:
            raise RuntimeError(f"Unexpected HTTP {response.status_code}: {response.text[:200]}")

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Connection error: {e}")
    except json.JSONDecodeError:
        raise RuntimeError(f"Invalid JSON response: {response.text[:200]}")


def save_token(token_data, filename=TOKEN_FILE):
    """
    Save the OAuth token to a JSON file with metadata.

    Args:
        token_data (dict): The token response from the API
        filename (str): The output filename
    """
    token_info = {
        "retrieved_at": datetime.now().isoformat(),
        "access_token": token_data.get("access_token"),
        "token_type": token_data.get("token_type"),
        "expires_in": token_data.get("expires_in"),
        "status": token_data.get("status"),
    }

    if "expires_in" in token_data and token_data["expires_in"]:
        try:
            expiry_seconds = int(token_data["expires_in"])
            expiry_time = datetime.now() + timedelta(seconds=expiry_seconds)
            token_info["expires_at"] = expiry_time.isoformat()
        except (ValueError, TypeError):
            pass

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(token_info, f, indent=2, ensure_ascii=False)

    print(f"✓ Token saved to {filename}")


def main():
    """Main execution function."""
    print("=" * 60)
    print("WaterInsights API - Fetch Token")
    print("=" * 60)

    try:
        token_response = get_access_token()

        if "expires_in" in token_response:
            expiry_seconds = int(token_response["expires_in"])
            expiry_time = datetime.now() + timedelta(seconds=expiry_seconds)
            print(f"Token expires at: {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}")

        save_token(token_response)

        print("=" * 60)
        print("✓ COMPLETE")
        print("=" * 60)

    except RuntimeError as e:
        print(f"\n✗ ERROR: {e}\n")
        exit(1)


if __name__ == "__main__":
    main()
