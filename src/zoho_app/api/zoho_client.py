# zoho_app/api/zoho_client.py

import os
import time
import requests
from typing import Any, Dict, Optional
import json

from zoho_app.auth.token_manager import get_access_token

class ZohoClient:
    def __init__(self):
        self.base_url = "https://www.zohoapis.com/books/v3"
        self.org_id = os.environ["ORGANISATION_ID"]

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{path}"
        headers = {
            "Authorization": f"Zoho-oauthtoken {get_access_token()}"
        }

        # Ensure organization_id is always passed as a query param
        all_params = params.copy() if params else {}
        all_params["organization_id"] = self.org_id

        attempt = 0
        while True:
            attempt += 1
            try:
                response = requests.get(url, headers=headers, params=all_params, timeout=10)
                if response.status_code == 429:
                    wait = min(60, 2 ** attempt)
                    print(f"⚠️  Rate limited, backing off for {wait}s...")
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                if attempt >= 2:
                    print(f"❌ Failed after {attempt} attempts: {e}")
                    raise
                print(f"⚠️  Attempt {attempt} failed: {e}, retrying...")
                time.sleep(2 ** attempt)

    def put(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/{path}"
        headers = {
            "Authorization": f"Zoho-oauthtoken {get_access_token()}",
            "Content-Type": "application/json"
        }

        params = {
            "organization_id": self.org_id
        }

        attempt = 0
        while True:
            attempt += 1
            try:
                response = requests.put(url, headers=headers, params=params, json=data, timeout=10)
                try:
                    payload = response.json()
                    print(f"Zoho PUT response JSON:\n{json.dumps(payload, indent=2)}")
                except ValueError:
                    print("❌ Response is not JSON:")
                    print(response.text)

                if response.status_code == 429:
                    wait = min(60, 2 ** attempt)
                    print(f"⚠️  Rate limited, backing off for {wait}s...")
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                if attempt >= 2:
                    print(f"❌ PUT failed after {attempt} attempts: {e}")
                    raise
                print(f"⚠️  PUT attempt {attempt} failed: {e}, retrying...")
                time.sleep(2 ** attempt)


    def delete_card(self, profile_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/recurringinvoices/{profile_id}/card"
        headers = {
            "Authorization": f"Zoho-oauthtoken {get_access_token()}",
        }
        params = {
            "organization_id": self.org_id
        }

        attempt = 0
        while True:
            attempt += 1
            try:
                response = requests.delete(url, headers=headers, params=params, timeout=10)
                try:
                    payload = response.json()
                    print(f"Zoho PUT response JSON:\n{json.dumps(payload, indent=2)}")
                except ValueError:
                    print("❌ Response is not JSON:")
                    print(response.text)
                print(f"← DELETE {url} → {response.status_code}")
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                print(f"❌ DELETE card failed: {e}")
                if attempt >= 2:
                    raise
                time.sleep(2 ** attempt)
