# Kebony — Quick Reference

> Useful links and info for day-to-day work.
> Updated: 2026-03-04

---

## Odoo Environments

| Environment | URL | Notes |
|---|---|---|
| **Production** | [kebonyprod.odoo.com](https://kebonyprod.odoo.com/odoo) | Live — handle with care |
| **Test / Development** | [kebonyprod-development-29047085.dev.odoo.com](https://kebonyprod-development-29047085.dev.odoo.com/odoo) | Safe to experiment — rebuilt from production periodically |

> ⚠️ **Test URL changes** after each rebuild from production (Odoo.sh appends a new sequence number). This page is the single source of truth for the current test URL. If the link doesn't work, ask your admin to update it here.

---

## Sync Knowledge Base to Odoo

This Obsidian vault can be pushed to Odoo's **Knowledge** app using the `sync_to_odoo.py` script in this folder. It converts all markdown files to HTML and creates/updates articles in Odoo, preserving the folder hierarchy.

### Prerequisites

- Python 3 with `markdown` library: `pip3 install markdown`
- Odoo API key stored in `.env` file (gitignored, never committed)

### Commands

```bash
# Navigate to the vault
cd "/Users/oeb/Documents/Manufacturing Kebony"

# Dry run (preview what would happen, no changes made)
python3 sync_to_odoo.py --env production --user admin --api-key YOUR_API_KEY --dry-run

# Push to production
python3 sync_to_odoo.py --env production --user admin --api-key YOUR_API_KEY

# Push to test (when available)
python3 sync_to_odoo.py --env test --user admin --api-key YOUR_API_KEY
```

> Replace `YOUR_API_KEY` with the key from `.env` in this folder.

### How it works

- **Idempotent**: running it again updates existing articles (matched by name + parent), no duplicates
- **Hierarchy**: folders become parent articles, `.md` files become child articles
- **One-way sync**: Obsidian → Odoo only. Edits made in Odoo will be overwritten on next sync

### API Key management

- Stored locally in `.env` (gitignored)
- Generate at: Odoo → My Profile → Account Security → API Keys → New
- Current key user: `admin`

---
