# zoho_app/core/scrub_cards.py

from typing import Dict

def scrub_card_from_profile(profile: Dict) -> Dict:
    invoice_id = profile.get("recurring_invoice_id")
    if not invoice_id:
        raise ValueError("Missing 'recurring_invoice_id'")
    card = profile.get("card", {})
    if not card.get("card_id"):
        raise ValueError(f"No card_id found in profile {invoice_id}")
    return {
        "recurring_invoice_id": invoice_id,
        "card_id": "",  # Required at top-level for Zoho to detach card
        "is_autobill_enabled": False
    }

