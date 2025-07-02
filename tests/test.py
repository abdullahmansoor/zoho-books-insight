# tests/test_smoke_api.py
import os, time, requests
import sys
sys.path.append("/Users/abdullahmansoor/Documents/ML101/zoho-app/src")  # Add src to the path for imports
from zoho_app.utils.env import load_project_env
load_project_env()

import os

TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token"
def _new_access_token() -> str:
    rsp = requests.post(
        TOKEN_URL,
        params={
            "refresh_token": os.environ["REFRESH_TOKEN"],
            "client_id":     os.environ["CLIENT_ID"],
            "client_secret": os.environ["CLIENT_SECRET"],
            "grant_type":    "refresh_token",
        },
        timeout=10,
    )
    rsp.raise_for_status()
    data = rsp.json()
    assert "access_token" in data, data      # quick sanity
    return data["access_token"]

def test_token_and_ping():
    token = _new_access_token()
    print(token)
    org_id = os.environ["ORGANISATION_ID"]
    rsp = requests.get(
        "https://books.zoho.com/api/v3/organizations",
        headers={"Authorization": f"Zoho-oauthtoken {token}"},
        timeout=10,
    )
    rsp.raise_for_status()
    j = rsp.json()
    assert j["code"] == 0
    matching_org = next(
        (org for org in j["organizations"] if str(org["organization_id"]) == org_id),
        None,
    )
    assert matching_org is not None, f"Org ID {org_id} not found in token scope"
    print("✅  organisation =", matching_org["name"])

def _debug_org_list(token):
    url = "https://books.zoho.com/api/v3/organizations"
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    rsp = requests.get(url, headers=headers, timeout=10)
    print("→ Status:", rsp.status_code)
    print("→ Body:", rsp.text)


if __name__ == "__main__":
    # Run the test directly if this script is executed
    try:
        #token = _new_access_token()
        #_debug_org_list(token)

        test_token_and_ping()
        print("✅  Test passed successfully.")
    except Exception as e:
        print(f"❌  Test failed: {e}")
        sys.exit(1)  # Exit with an error code if the test fails