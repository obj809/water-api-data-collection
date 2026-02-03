# api_call.py

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
    # Create Basic Auth credentials: Base64(api_key:api_secret)
    credentials = f"{API_KEY}:{API_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    # Prepare request
    params = {
        "grant_type": "client_credentials"
    }
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}"
    }
    
    print("Authenticating with WaterInsights API...")
    print(f"Endpoint: {TOKEN_ENDPOINT}")
    print(f"API Key: {API_KEY[:15]}...")
    print()
    
    try:
        # Make GET request (as shown in documentation)
        response = requests.get(TOKEN_ENDPOINT, headers=headers, params=params, timeout=15)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            
            if "access_token" not in token_data:
                raise RuntimeError("Response missing 'access_token' field")
            
            print("✓ Authentication successful!\n")
            return token_data
            
        elif response.status_code == 401:
            error_detail = ""
            try:
                error_data = response.json()
                error_detail = f"\nError: {error_data.get('Error', 'Unknown error')}"
                error_detail += f"\nErrorCode: {error_data.get('ErrorCode', 'Unknown')}"
            except:
                error_detail = f"\nResponse: {response.text}"
            
            raise RuntimeError(f"Authentication failed (401 Unauthorized){error_detail}")
            
        else:
            raise RuntimeError(f"Unexpected HTTP {response.status_code}: {response.text[:200]}")
            
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Connection error: {e}")
    except json.JSONDecodeError:
        raise RuntimeError(f"Invalid JSON response: {response.text[:200]}")


def save_token_to_file(token_data, filename=TOKEN_FILE):
    """
    Save the OAuth token to a JSON file with metadata.
    
    Args:
        token_data (dict): The token response from the API
        filename (str): The output filename
    """
    # Add metadata about when the token was retrieved
    token_info = {
        "retrieved_at": datetime.now().isoformat(),
        "access_token": token_data.get("access_token"),
        "token_type": token_data.get("token_type"),
        "expires_in": token_data.get("expires_in"),
        "status": token_data.get("status"),
        "refresh_token_expires_in": token_data.get("refresh_token_expires_in")
    }
    
    # Calculate expiration timestamp if expires_in is provided
    if "expires_in" in token_data and token_data["expires_in"]:
        try:
            expiry_seconds = int(token_data["expires_in"])
            expiry_time = datetime.now() + timedelta(seconds=expiry_seconds)
            token_info["expires_at"] = expiry_time.isoformat()
        except (ValueError, TypeError):
            # If conversion fails, just skip the expires_at calculation
            pass
    
    # Include full original response for reference
    token_info["full_response"] = token_data
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(token_info, f, indent=2, ensure_ascii=False)
        print(f"✓ Token saved to {filename}")
        return True
    except IOError as e:
        raise RuntimeError(f"Failed to save token: {e}")


def main():
    """Main execution function."""
    try:
        # Get the OAuth token
        token_response = get_access_token()
        
        print("=" * 80)
        print("✓ AUTHENTICATION SUCCESSFUL")
        print("=" * 80)
        print()
        
        # Print the access token
        access_token = token_response.get("access_token", "")
        print("ACCESS TOKEN:")
        print("-" * 80)
        print(access_token)
        print("-" * 80)
        print()
        
        # Print token metadata
        print("TOKEN METADATA:")
        print("-" * 80)
        if "token_type" in token_response:
            print(f"Token type: {token_response['token_type']}")
        
        if "expires_in" in token_response:
            try:
                expiry_seconds = int(token_response["expires_in"])
                expiry_hours = expiry_seconds / 3600
                expiry_time = datetime.now() + timedelta(seconds=expiry_seconds)
                print(f"Expires in: {expiry_seconds} seconds (~{expiry_hours:.1f} hours)")
                print(f"Expires at: {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}")
            except (ValueError, TypeError):
                print(f"Expires in: {token_response['expires_in']} (format error)")
        
        if "status" in token_response:
            print(f"Status: {token_response['status']}")
        
        print("-" * 80)
        print()
        
        # Save token to file
        save_token_to_file(token_response)
        
        print()
        print("=" * 80)
        print("✓ TOKEN RETRIEVAL COMPLETE")
        print("=" * 80)
        print(f"\nThe OAuth token has been saved to '{TOKEN_FILE}'")
        print("\nYou can now use this token to make API requests by:")
        print("  1. Reading the token from the file")
        print("  2. Using it in the Authorization header: 'Bearer {access_token}'")
        print()
        
    except RuntimeError as e:
        print()
        print("=" * 80)
        print("✗ AUTHENTICATION FAILED")
        print("=" * 80)
        print(f"\n{e}\n")
        print("Please verify:")
        print("  1. Your API_KEY and API_SECRET are correct")
        print("  2. Your app is approved/subscribed at https://api.nsw.gov.au")
        print("  3. The app has access to the WaterInsights API")
        print()
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