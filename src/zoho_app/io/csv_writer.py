# zoho_app/io/csv_writer.py

import csv
from pathlib import Path
from typing import List
from zoho_app.core.scan_profiles import RecurringProfile

def write_profile_csv(out_path: Path, profiles: List[RecurringProfile]) -> None:
    """Write recurring profile data to CSV with card and gateway status."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open(mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["profile_id", "customer_name", "card_id_present", "stripe_gateway_present"])

        for profile in profiles:
            writer.writerow([
                profile.profile_id,
                profile.customer_name,
                "Yes" if profile.card_id_present else "No",
                "Yes" if profile.stripe_gateway_present else "No",
            ])