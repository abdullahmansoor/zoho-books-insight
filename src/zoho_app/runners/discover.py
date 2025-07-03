 # zoho_app/runners/discover.py
import sys
import typer
from pathlib import Path
from typing import Optional

sys.path.append(str(Path(__file__).resolve().parents[3] / "src"))

from zoho_app.utils.env import load_project_env
from zoho_app.core.scan_profiles import fetch_recurring_profiles
from zoho_app.io.csv_writer import write_profile_csv

app = typer.Typer()

@app.command()
def main(
    out: Optional[str] = typer.Option("recurring_card_report.csv", help="Output CSV file name"),
    dry: bool = typer.Option(True, help="Dry-run mode (prints summary only)"),
    limit: Optional[int] = typer.Option(2, help="Limit number of profiles for testing")
):
    """Discover recurring-invoice profiles and report stored card/gateway status."""
    try:
        load_project_env()
        print("🔍 Fetching recurring invoice profiles from Zoho...")
        profiles = fetch_recurring_profiles(limit=limit)

        if dry:
            print(f"✅ Retrieved {len(profiles)} profiles (dry-run mode)")
            for p in profiles[:5]:
                print("-", p)
        else:
            out_path = Path(out)
            write_profile_csv(out_path, profiles)
            print(f"✅ Wrote {len(profiles)} profiles to {out_path}")

    except Exception as e:
        print(f"❌ Error during discovery: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
