## 🔐 Zoho Books — Safe Card Removal Tool

**Quickly audit and remove stored cards from all active recurring invoice profiles in Zoho Books**  
Use this tool before switching Stripe accounts — to prevent billing failures and API errors.

➡️ *Part of a broader platform for reporting, analytics, and predictive billing insights (coming soon).*

---

### 🚀 What This Tool Does

This tool helps you:

✅ Scan all recurring invoice profiles  
✅ Detect cards stored for auto-charge  
✅ Generate an audit report (CSV)  
✅ Optionally remove those cards safely  
✅ Log all changes in an audit database

> All actions are double-checked and **dry-run by default** — no accidental changes.

---

### 🧰 Prerequisites

| Requirement        | Notes                                 |
|--------------------|----------------------------------------|
| Python 3.9+        | Use `python3 --version` to check       |
| Zoho Books Account | Any paid plan with API access          |
| API Scopes         | `ZohoBooks.fullaccess.all`             |
| Credentials        | See setup below                        |

---

### ⚙️ Setup Steps

```bash
# 1. Clone and install
git clone https://github.com/abdullahmansoor/zoho-books-insight.git
cd zoho-books-insight
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Create .env file
cat > .env <<EOF
ORGANISATION_ID=your_org_id
CLIENT_ID=...
CLIENT_SECRET=...
REFRESH_TOKEN=...
EOF
```

---

### 🔍 Step 1: Run Scan (Read-only)

This finds profiles that still have stored cards:

```bash
python -m runners.discover
```

📄 This creates `recurring_card_report.csv` with:

- Profile ID
- Customer name
- Whether card is stored
- Whether Stripe is attached

---

### 🛡️ Step 2: Remove Cards (Optional)

Only do this **after reviewing the CSV**.

```bash
python -m runners.apply --confirm
```

🔒 Safety features:

- Verifies each profile again before change  
- Confirms `card_id` is actually removed  
- Logs each change into `audit_YYYYMMDD.sqlite`  
- Stops if more than 50 changes are detected at once

To test without changing anything:

```bash
python -m runners.apply  # No --confirm = dry-run
```

---

### 📁 Output Files

| File                         | Description                          |
|-----------------------------|--------------------------------------|
| `recurring_card_report.csv` | Summary of active profiles/cards     |
| `audit_YYYYMMDD.sqlite`     | Log of all verified changes          |

---

### ❓ Troubleshooting

- **No `.env` file** → make sure `.env` exists at project root
- **Invalid token** → regenerate your refresh token
- **Too many profiles** → use `--limit` option:  
  ```bash
  python -m runners.discover --limit 20
  ```

---

### 🙋 FAQ

**Q: Is this safe for production?**  
A: Yes — but always run the discovery step and confirm CSV before using `--confirm`.

**Q: Can I rollback changes?**  
A: Not automatically yet, but all old values are saved in `audit.sqlite`.

**Q: Where do I get Zoho credentials?**  
A: From https://api-console.zoho.com → Add Self Client → use `localhost` redirect URI.

---

### 👩‍💻 Optional: Test the Setup

```bash
pytest tests/test.py
```

This checks token access and validates your Zoho org ID.
