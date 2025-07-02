## README — Zoho Books “Safe-Card-Removal” Toolkit

*A rock-solid, auditable workflow for auditing and cleansing stored cards on recurring-invoice profiles.*



 

---

### 1 . Problem statement

Before you can disconnect an **old Stripe account** and wire up a new one, every recurring-invoice profile that auto-charges a customer’s card must first have that **card detached** (and, optionally, Stripe removed from its gateway list). Doing this by hand is error-prone and risky; we want an **automated, fully-auditable process** with multiple checkpoints.

---

### 2 . Solution overview

```
safe-card-removal/
├── auth/                 # OAuth helpers (token swap, refresh, revocation)
│   └── token_manager.py
├── api/                  # Thin, typed wrapper around Zoho Books REST
│   ├── zoho_client.py
│   └── models.py
├── core/                 # Business logic, expressed as Commands
│   ├── scan_profiles.py
│   └── scrub_cards.py
├── io/                   # Pure side-effect adapters
│   ├── csv_writer.py
│   ├── email_notifier.py
│   └── logger.py
├── runners/              # CLI entry points (click / Typer)
│   ├── discover.py       # “Report-only” mode
│   └── apply.py          # Two-phase mutate-and-verify
├── tests/                # pytest unit & integration tests
└── README.md
```

Key design patterns

| Pattern               | Where used                                     | Why                                              |
| --------------------- | ---------------------------------------------- | ------------------------------------------------ |
| **Facade**            | `ZohoClient`                                   | One clean interface hides HTTP guts              |
| **Command**           | `core/scan_profiles.py`, `core/scrub_cards.py` | Uniform “execute + undo + dry-run” contract      |
| **Repository**        | `api/models.py`                                | Turn JSON into typed dataclasses; easier testing |
| **Strategy**          | `io/csv_writer` vs `io/email_notifier`         | Pluggable output sinks                           |
| **Decorator (Retry)** | `io/logger.retry`                              | Exponential back-off for HTTP 429                |

---

### 3 . Safety-first execution flow

```
┌──────────────┐      ┌──────────┐      ┌────────────┐
│  discover.py │─dry─▶│ CSV file │─OK─▶ │  apply.py  │
└──────────────┘      └──────────┘      └────────────┘
        ▲                                 │
        │ verify counts & diffs           │
        └────────────rollback on mismatch─┘
```

1. **Read-only discovery**\
   \*Lists every recurring profile via \**`GET /recurringinvoices`* ([zoho.com](https://www.zoho.com/books/api/v3/recurring-invoices/?utm_source=chatgpt.com))

   - Writes `recurring_card_report.csv` with columns: profile-ID, customer, `card_id` present?, Stripe gateway present?
   - Exit code is non-zero if any API error or schema drift is detected.

2. **Manual review**\
   *Open the CSV, confirm counts match Zoho UI.*\
   *Optional*: run `pytest -k integration` which re-fetches 5 % of rows to prove determinism.

3. **Two-phase mutator** (`apply.py`)\
   *Iterates only over rows marked “Card=Yes”.*

   - **Phase 1 (dry pass):** re-fetch each profile, compare hash with CSV; abort if drift.
   - **Phase 2 (commit):**
     1. `PUT /recurringinvoices/{id}` with `"card_id": ""` + pruned gateway list.
     2. Immediately `GET` same profile; assert `card_id` is empty.
     3. Append to an *audit log* (`audit_YYYYMMDD.sqlite`) with before/after JSON blobs.
   - Failure at any step rolls back the batch (best-effort) and emails ops\@.

Every network call is wrapped in: retry-with-jitter → structured log → typed validation (pydantic).

---

### 4 . Prerequisites

| Requirement     | Version                                                               |
| --------------- | --------------------------------------------------------------------- |
| Python          | 3.9 +                                                                 |
| Zoho Books plan | any that exposes API                                                  |
| Scopes          | `ZohoBooks.fullaccess.all` (you can later trim)                       |
| API creds       | organisation-ID, client-ID, secret, **refresh-token** (see Section 6) |

---

### 5 . Quick-start

```bash
git clone https://github.com/amana-nexus/safe-card-removal.git
cd safe-card-removal
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1⃣  create .env
cat > .env <<EOF
ORGANISATION_ID=123456789
CLIENT_ID=1000.ABC...
CLIENT_SECRET=xxxx
REFRESH_TOKEN=1000.yyyy
EOF

# 2⃣  run discovery
python -m runners.discover

# 3⃣  inspect recurring_card_report.csv
#     when satisfied:
python -m runners.apply --confirm   # will ask again before mutating
```

---

### 6 . Obtaining credentials

1. **Add Client → Self Client** in the Zoho API console.
2. Use homepage/redirect `https://localhost`; scopes `ZohoBooks.fullaccess.all`.
3. Generate grant-code → exchange via\
   `POST /oauth/v2/token?grant_type=authorization_code …`\
   The response contains your **refresh\_token** (long-lived).
4. Grab **organisation\_id** from *Settings → Manage Organisations* or via `GET /organizations`. ([zoho.com](https://www.zoho.com/books/api/v3/introduction/?utm_source=chatgpt.com))

---

### 7 . Module cheat-sheet

| Module               | Responsibilities                                             | Tests                                     |
| -------------------- | ------------------------------------------------------------ | ----------------------------------------- |
| `auth.token_manager` | Swap/refresh tokens; cache in mem; revoke                    | `tests/test_auth.py`                      |
| `api.zoho_client`    | `get`, `put` with automatic query-params & retry             | `tests/test_api_contract.py` (mocks HTTP) |
| `core.scan_profiles` | Pull pages, map to `RecurringInvoice` dataclass, return list | `tests/test_scan_profiles.py`             |
| `core.scrub_cards`   | Idempotent command: verify → mutate → verify                 | `tests/test_scrub_cards.py`               |
| `io.csv_writer`      | Pure function -> writes UTF-8 CSV                            | —                                         |
| `io.logger`          | JSON logs (struct-log) routed to stdout & file               | —                                         |

---

### 8 . Double-verification mechanics

1. **Hash-compare**: SHA-256 of canonicalised JSON before & after.
2. **Post-write GET**: Confirms Zoho accepted the mutation.
3. **Audit DB**: SQLite, schema `changes(id, zoho_id, before, after, ts)`.
4. **Safety valve**: `apply.py --max‐changes 50` aborts if more than N profiles would mutate in one run.

---

### 9 . CI / CD suggestions

- **Pre-commit**: black, isort, flake8, mypy
- **GitHub Actions**: run unit tests + `python -m runners.discover --dry --limit 5` against a sandbox org
- **Secrets**: store CI org creds in *Actions → Secrets & Variables*; use read-only scope.
- **Release tagging**: semantic versioning; build a Docker image (`docker/Dockerfile`) for prod runs.

---

### 10 . Extending / hardening

| Idea                       | Effort | Notes                                                 |
| -------------------------- | ------ | ----------------------------------------------------- |
| Encrypt `.env` with `sops` | ★★☆☆☆  | Decrypt at runtime; key in AWS KMS                    |
| Dry-run HTML diff report   | ★☆☆☆☆  | Highlight JSON diff per profile                       |
| Slack webhook on failure   | ★☆☆☆☆  | `io/slack_notifier.py` as new Strategy                |
| Rollback script            | ★★☆☆☆  | Reads audit DB, re-applies old `card_id`              |
| Replace fullaccess scope   | ★★☆☆☆  | Narrow to `recurringinvoices.READ/UPDATE` once stable |

---

### 11 . References

- Zoho Books API – Recurring Invoices endpoints ([zoho.com](https://www.zoho.com/books/api/v3/recurring-invoices/?utm_source=chatgpt.com))
- Community thread on associating/removing `customer_card_id` (shows presence of `card_id` field) ([help.zoho.com](https://help.zoho.com/portal/en/community/topic/adding-recurring-invoice-via-api-how-to-enter-credit-card-details-for-auto-charge?utm_source=chatgpt.com))

---

### 12 . License & liability

This toolkit is released under the **MIT License**.\
Use at your own risk; always test in a sandbox organisation before touching production data.
