# zoho_app/core/scan_profiles.py


from dataclasses import dataclass
from typing import List, Optional
from tqdm import tqdm

from zoho_app.api.zoho_client import ZohoClient

@dataclass
class RecurringProfile:
    profile_id: str
    customer_name: str
    card_id_present: bool
    stripe_gateway_present: bool

def fetch_recurring_profiles(limit: Optional[int] = None) -> List[RecurringProfile]:
    client = ZohoClient()
    profiles: List[RecurringProfile] = []

    page = 1
    per_page = 200
    seen = 0

    pbar = tqdm(total=limit if limit else 1000, desc="🔄 Fetching profiles", unit="profiles")

    while True:
        resp = client.get("recurringinvoices", params={"page": page, "per_page": per_page})
        items = resp.get("recurring_invoices", [])
        if not items:
            break

        for item in items:
            autobill = item.get("is_autobill_enabled", False)
            if not autobill:
                # Skip if autobill is off — no card will be attached
                profile = RecurringProfile(
                    profile_id=item["recurring_invoice_id"],
                    customer_name=item["customer_name"],
                    card_id_present=False,
                    stripe_gateway_present=False,
                )
                #profiles.append(profile)
                seen += 1
                if limit and seen >= limit:
                    return profiles
                continue

            # Only then fetch full details (expensive)
            detailed = client.get(
                f"recurringinvoices/{item['recurring_invoice_id']}",
                params={"include_card_details": "true"}
            )
            full = detailed.get("recurring_invoice", {})
            #if not full.get("card_id"):
            #    print(f"\n❌ No card_id for profile {full.get('recurring_invoice_id')}")
            #    print("Full JSON:", full)

            card_data = full.get("card", {})
            card_id_present = bool(card_data.get("card_id"))

            # Stripe check can now pull from either legacy or nested payment section
            gateways = full.get("payment_options", {}).get("payment_gateways", [])
            stripe_gateway_present = any(
                g.get("gateway_name", "").lower() == "stripe"
                for g in gateways
            )
            profile = RecurringProfile(
                profile_id=full["recurring_invoice_id"],
                customer_name=full["customer_name"],
                card_id_present=card_id_present,
                stripe_gateway_present=stripe_gateway_present,
            )
            profiles.append(profile)
            seen += 1
            pbar.update(1)
            if limit and seen >= limit:
                pbar.close()
                return profiles

        page += 1

    pbar.close()
    return profiles
