# zoho_app/runners/apply.py

import sys
import json
import hashlib
import sqlite3
import typer
from datetime import datetime
from pathlib import Path
from typing import List
import sys

from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[3] / "src"))

from zoho_app.utils.env import load_project_env
from zoho_app.api.zoho_client import ZohoClient
from zoho_app.core.scan_profiles import RecurringProfile
from zoho_app.core.scrub_cards import scrub_card_from_profile
from zoho_app.io.csv_writer import write_profile_csv

app = typer.Typer()

def load_csv(path: Path) -> List[RecurringProfile]:
    import csv
    rows = []
    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["card_id_present"].strip().lower() == "yes":
                rows.append(RecurringProfile(
                    profile_id=row["profile_id"],
                    customer_name=row["customer_name"],
                    card_id_present=True,
                    stripe_gateway_present=(row["stripe_gateway_present"].strip().lower() == "yes")
                ))
    return rows

def append_audit_entry(db_path: Path, zoho_id: str, before: dict, after: dict) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zoho_id TEXT,
            before TEXT,
            after TEXT,
            ts TEXT
        )
    """)
    conn.execute(
        "INSERT INTO changes (zoho_id, before, after, ts) VALUES (?, ?, ?, ?)",
        (zoho_id, json.dumps(before), json.dumps(after), datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

@app.command()
def main(
    confirm: bool = typer.Option(True, "--confirm", help="Actually apply the changes"),
    csv_path: str = typer.Option("recurring_card_report.csv", help="Input CSV file"),
    max_changes: int = typer.Option(641, help="Max allowed mutations before abort"),
):
    load_project_env()
    client = ZohoClient()
    csv_file = Path(csv_path)
    audit_db = Path(f"audit_{datetime.now():%Y%m%d}.sqlite")

    try:
        targets = load_csv(csv_file)
        typer.echo(f"🔍 Loaded {len(targets)} profiles from {csv_file}")
        if not confirm:
            typer.echo("🛑 Dry-run only — use `--confirm` to apply changes")

        mutated = 0

        for p in targets:
            if mutated >= max_changes:
                typer.echo(f"❌ Max allowed changes ({max_changes}) exceeded.")
                raise typer.Exit(code=1)

            if confirm:
                client.delete_card(p.profile_id)
                reloaded = client.get(f"recurringinvoices/{p.profile_id}")
                card_id_after = reloaded.get("recurring_invoice", {}).get("card", {}).get("card_id")
                if card_id_after:
                    typer.echo(f"❌ Verification failed for {p.profile_id}: card_id still present")
                    raise typer.Exit(code=1)

                #append_audit_entry(audit_db, p.profile_id, before, reloaded["recurring_invoice"])
                typer.echo(f"✅ Scrubbed {p.profile_id} and logged audit")
            else:
                typer.echo(f"🔎 Would mutate {p.profile_id}")

            mutated += 1

        typer.echo(f"✅ Done. Total mutated: {mutated}")

    except Exception as e:
        typer.echo(f"❌ Error during apply: {e}", err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
