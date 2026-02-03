# api_call.py

# api_call.py

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
OUTPUT_FILE = "response.json"

# Validate API_KEY is set
if not API_KEY:
    raise RuntimeError("API_KEY not set in .env file")


def load_token_from_file(filename=TOKEN_FILE):
    """
    Load the OAuth token from the saved JSON file.
    
    Args:
        filename (str): The token file to read from
        
    Returns:
        str: The access token
        
    Raises:
        RuntimeError: If token file doesn't exist or is invalid
    """
    if not os.path.exists(filename):
        raise RuntimeError(
            f"Token file '{filename}' not found. "
            f"Please run 'python fetch_token.py' first to obtain a token."
        )
    
    try:
        with open(filename, "r", encoding="utf-8") as f:
            token_data = json.load(f)
        
        access_token = token_data.get("access_token")
        if not access_token:
            raise RuntimeError(f"No 'access_token' found in {filename}")
        
        # Check if token has expired
        if "expires_at" in token_data:
            expires_at = datetime.fromisoformat(token_data["expires_at"])
            if datetime.now() >= expires_at:
                raise RuntimeError(
                    f"Token has expired at {expires_at.strftime('%Y-%m-%d %H:%M:%S')}. "
                    f"Please run 'python fetch_token.py' to get a new token."
                )
        
        print(f"✓ Token loaded from {filename}")
        if "expires_at" in token_data:
            expires_at = datetime.fromisoformat(token_data["expires_at"])
            print(f"  Token expires at: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return access_token
        
    except json.JSONDecodeError:
        raise RuntimeError(f"Invalid JSON in {filename}")
    except IOError as e:
        raise RuntimeError(f"Failed to read {filename}: {e}")


def fetch_dams_data(access_token):
    """
    Fetch the list of all dams from the WaterInsights API.
    
    Args:
        access_token (str): The OAuth access token
        
    Returns:
        dict or list: The API response data
        
    Raises:
        RuntimeError: If the API request fails
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "apikey": API_KEY
    }
    
    print(f"\nFetching dams data from API...")
    print(f"Endpoint: {DAMS_ENDPOINT}")
    print(f"Headers: Authorization (Bearer) + apikey")
    
    try:
        response = requests.get(DAMS_ENDPOINT, headers=headers, timeout=15)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Data retrieved successfully")
            
            try:
                data = response.json()
                return data
            except json.JSONDecodeError:
                raise RuntimeError("API returned invalid JSON")
                
        elif response.status_code == 401:
            raise RuntimeError(
                "Authentication failed (401 Unauthorized). "
                "Your token may have expired. Run 'python fetch_token.py' to get a new token."
            )
            
        elif response.status_code == 403:
            raise RuntimeError(
                "Access forbidden (403). Your app may not have access to this API endpoint."
            )
            
        elif response.status_code == 429:
            raise RuntimeError(
                "Rate limit exceeded (429). Please wait before retrying."
            )
            
        else:
            raise RuntimeError(
                f"API request failed with HTTP {response.status_code}: {response.text[:200]}"
            )
            
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Connection error: {e}")


def save_response(data, filename=OUTPUT_FILE):
    """
    Save the API response to a JSON file.
    
    Args:
        data (dict or list): The data to save
        filename (str): The output filename
    """
    try:
        # Add metadata about when the data was retrieved
        output = {
            "retrieved_at": datetime.now().isoformat(),
            "endpoint": DAMS_ENDPOINT,
            "data": data
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Response saved to {filename}")
        
    except IOError as e:
        raise RuntimeError(f"Failed to save response: {e}")


def main():
    """Main execution function."""
    print("=" * 80)
    print("WaterInsights API - Fetch Dams Data")
    print("=" * 80)
    print()
    
    try:
        # Step 1: Load the OAuth token
        access_token = load_token_from_file()
        
        # Step 2: Fetch dams data
        dams_data = fetch_dams_data(access_token)
        
        # Step 3: Display summary
        print()
        print("=" * 80)
        print("DATA SUMMARY")
        print("=" * 80)
        
        if isinstance(dams_data, list):
            print(f"Total dams: {len(dams_data)}")
            if len(dams_data) > 0:
                print("\nFirst few dams:")
                for dam in dams_data[:3]:
                    if isinstance(dam, dict):
                        dam_id = dam.get('dam_id', 'N/A')
                        dam_name = dam.get('dam_name', 'N/A')
                        print(f"  - {dam_name} (ID: {dam_id})")
        elif isinstance(dams_data, dict):
            print(f"Response contains {len(dams_data)} keys")
            print(f"Keys: {list(dams_data.keys())}")
        
        # Step 4: Save to file
        save_response(dams_data)
        
        print()
        print("=" * 80)
        print("✓ OPERATION COMPLETE")
        print("=" * 80)
        print(f"\nDams data has been saved to '{OUTPUT_FILE}'")
        print()
        
    except RuntimeError as e:
        print()
        print("=" * 80)
        print("✗ ERROR")
        print("=" * 80)
        print(f"\n{e}\n")
        exit(1)
    except Exception as e:
        print()
        print("=" * 80)
        print("✗ UNEXPECTED ERROR")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        exit(1)


if __name__ == "__main__":
    main()