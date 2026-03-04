#!/usr/bin/env python3
"""
Sync Kebony Obsidian knowledge base → Odoo Knowledge module.

Usage:
    python3 sync_to_odoo.py --env test --user your@email.com --api-key YOUR_API_KEY
    python3 sync_to_odoo.py --env production --user your@email.com --api-key YOUR_API_KEY
    python3 sync_to_odoo.py --env test --user your@email.com --api-key YOUR_API_KEY --dry-run

API key: Odoo → Settings → Users → select user → Preferences → API Keys → New
"""

import argparse
import os
import sys
import xmlrpc.client
from pathlib import Path

import markdown

# ── Environments ────────────────────────────────────────────────────────────

ENVIRONMENTS = {
    "test": {
        "url": "https://kebonyprod-development-29047085.dev.odoo.com",
        "db": "kebonyprod-development-29047085",
    },
    "production": {
        "url": "https://kebonyprod.odoo.com",
        "db": "kebonyprod-main-26738590",
    },
}

# ── Folder → Section mapping (sequence order) ──────────────────────────────

SECTIONS = [
    "01 - Terminology",
    "02 - General Topics",
    "03 - Manufacturing",
    "04 - US Specific",
    "05 - Working Plan",
]

ROOT_FILES = [
    "00 - Index.md",
    "00 - Quick Reference.md",
    "00 - Change Log.md",
]

# Files/folders to skip
SKIP = {".git", ".gitignore", ".obsidian", ".DS_Store", "sync_to_odoo.py"}


# ── Markdown → HTML ────────────────────────────────────────────────────────

def md_to_html(md_text: str) -> str:
    """Convert markdown to Odoo-friendly HTML."""
    return markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "toc", "nl2br"],
    )


# ── Odoo connection ────────────────────────────────────────────────────────

class OdooKnowledge:
    def __init__(self, env: str, user: str, api_key: str, dry_run: bool = False):
        cfg = ENVIRONMENTS[env]
        self.url = cfg["url"]
        self.db = cfg["db"]
        self.user = user
        self.api_key = api_key
        self.dry_run = dry_run
        self.uid = None
        self.models = None
        self._cache = {}  # (name, parent_id) → article_id

    def connect(self):
        """Authenticate via XML-RPC."""
        common = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/common", allow_none=True
        )
        self.uid = common.authenticate(self.db, self.user, self.api_key, {})
        if not self.uid:
            print(f"✗ Authentication failed for {self.user} on {self.db}")
            sys.exit(1)
        self.models = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/object", allow_none=True
        )
        print(f"✓ Connected to {self.db} as {self.user} (uid={self.uid})")

    def _execute(self, model, method, *args):
        return self.models.execute_kw(
            self.db, self.uid, self.api_key, model, method, *args
        )

    def find_article(self, name: str, parent_id) -> object:
        """Find article by name + parent. Returns ID or None."""
        cache_key = (name, parent_id)
        if cache_key in self._cache:
            return self._cache[cache_key]

        domain = [["name", "=", name]]
        if parent_id:
            domain.append(["parent_id", "=", parent_id])
        else:
            domain.append(["parent_id", "=", False])

        ids = self._execute("knowledge.article", "search", [domain], {"limit": 1})
        article_id = ids[0] if ids else None
        self._cache[cache_key] = article_id
        return article_id

    def upsert_article(
        self, name: str, body: str, parent_id=None, sequence: int = 10
    ) -> int:
        """Create or update a knowledge article. Returns article ID."""
        existing = self.find_article(name, parent_id)

        vals = {
            "name": name,
            "body": body,
            "sequence": sequence,
        }

        if existing:
            if self.dry_run:
                print(f"  [DRY RUN] Would UPDATE: {name} (id={existing})")
                return existing
            self._execute("knowledge.article", "write", [[existing], vals])
            print(f"  ✓ Updated: {name} (id={existing})")
            return existing
        else:
            vals["parent_id"] = parent_id or False
            vals["category"] = "workspace"
            vals["internal_permission"] = "write"
            if self.dry_run:
                print(f"  [DRY RUN] Would CREATE: {name} (parent={parent_id})")
                return -1
            article_id = self._execute("knowledge.article", "create", [vals])
            self._cache[(name, parent_id)] = article_id
            print(f"  ✓ Created: {name} (id={article_id})")
            return article_id


# ── Sync logic ──────────────────────────────────────────────────────────────

def sync(odoo: OdooKnowledge, base_path: Path):
    """Push the full knowledge base to Odoo."""

    # 1. Root article
    print("\n── Creating root article ──")
    root_id = odoo.upsert_article(
        "Kebony Knowledge Base",
        "<p>Kebony ERP implementation knowledge base — synced from Obsidian.</p>",
        parent_id=None,
        sequence=1,
    )

    # 2. Root-level files (Index, Change Log)
    print("\n── Root documents ──")
    for seq, filename in enumerate(ROOT_FILES, start=1):
        filepath = base_path / filename
        if not filepath.exists():
            continue
        md_text = filepath.read_text(encoding="utf-8")
        html = md_to_html(md_text)
        title = filepath.stem  # "00 - Index"
        odoo.upsert_article(title, html, parent_id=root_id, sequence=seq)

    # 3. Section folders
    print("\n── Sections ──")
    for seq, section_name in enumerate(SECTIONS, start=10):
        section_path = base_path / section_name
        if not section_path.is_dir():
            print(f"  ⊘ Skipped (not found): {section_name}")
            continue

        # Create section article (folder → parent article)
        section_id = odoo.upsert_article(
            section_name,
            f"<p>Section: {section_name}</p>",
            parent_id=root_id,
            sequence=seq,
        )

        # Child articles (each .md file in the folder)
        md_files = sorted(section_path.glob("*.md"))
        for child_seq, md_file in enumerate(md_files, start=1):
            md_text = md_file.read_text(encoding="utf-8")
            html = md_to_html(md_text)
            odoo.upsert_article(
                md_file.stem, html, parent_id=section_id, sequence=child_seq
            )

    print("\n── Sync complete ──")


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Sync Kebony knowledge base to Odoo Knowledge"
    )
    parser.add_argument(
        "--env",
        choices=["test", "production"],
        required=True,
        help="Target environment",
    )
    parser.add_argument("--user", required=True, help="Odoo username (email)")
    parser.add_argument("--api-key", required=True, help="Odoo API key")
    parser.add_argument(
        "--path",
        default=str(Path(__file__).parent),
        help="Path to knowledge base (default: script directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    base_path = Path(args.path)
    if not (base_path / "00 - Index.md").exists():
        print(f"✗ Not a valid knowledge base: {base_path}")
        sys.exit(1)

    odoo = OdooKnowledge(args.env, args.user, args.api_key, dry_run=args.dry_run)
    odoo.connect()
    sync(odoo, base_path)


if __name__ == "__main__":
    main()
