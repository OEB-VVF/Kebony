#!/usr/bin/env python3
"""
Sync Kebony Obsidian knowledge base → Odoo Knowledge module.

Usage:
    python3 sync_to_odoo.py --env test --user your@email.com --api-key YOUR_API_KEY
    python3 sync_to_odoo.py --env production --user your@email.com --api-key YOUR_API_KEY
    python3 sync_to_odoo.py --env test --user your@email.com --api-key YOUR_API_KEY --dry-run
    python3 sync_to_odoo.py --env test --user your@email.com --api-key YOUR_API_KEY --slides-only

API key: Odoo → Settings → Users → select user → Preferences → API Keys → New
"""

import argparse
import base64
import os
import re
import subprocess
import sys
import tempfile
import xmlrpc.client
from pathlib import Path
from typing import Optional

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

SLIDE_DECKS_DIR = "06 - Slide Decks"

# Files/folders to skip
SKIP = {".git", ".gitignore", ".obsidian", ".DS_Store", "sync_to_odoo.py", "tools"}

# Chrome path for headless PDF generation (macOS default)
CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]


# ── Markdown → HTML ────────────────────────────────────────────────────────

def md_to_html(md_text: str) -> str:
    """Convert markdown to Odoo-friendly HTML."""
    return markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "toc", "nl2br"],
    )


# ── Slide Deck Helpers ────────────────────────────────────────────────────

def find_chrome() -> Optional[str]:
    """Find a Chrome/Chromium binary on the system."""
    for path in CHROME_PATHS:
        if os.path.isfile(path):
            return path
    return None


def html_to_pdf(html_path: Path, pdf_path: Path) -> bool:
    """Convert HTML to PDF using Chrome headless. Returns True on success."""
    chrome = find_chrome()
    if not chrome:
        print("  ✗ Chrome not found — skipping PDF generation")
        return False
    try:
        subprocess.run(
            [
                chrome,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                f"--print-to-pdf={pdf_path}",
                "--no-pdf-header-footer",
                f"file://{html_path.resolve()}",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return pdf_path.exists() and pdf_path.stat().st_size > 0
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        print(f"  ✗ PDF generation failed: {exc}")
        return False


def extract_html_body(html_text: str) -> str:
    """Extract <style> + <body> content from a full HTML document.

    Returns an HTML fragment suitable for Odoo Knowledge article body.
    The slides are wrapped in a scrollable container so they don't
    overflow the Odoo article panel.
    """
    # Extract all <style> blocks
    styles = re.findall(r"<style[^>]*>(.*?)</style>", html_text, re.DOTALL)

    # Extract <body> content
    body_match = re.search(r"<body[^>]*>(.*?)</body>", html_text, re.DOTALL)
    body = body_match.group(1).strip() if body_match else html_text

    # Build self-contained fragment with scoped wrapper
    parts = []
    if styles:
        # Scope all CSS under .kebony-deck so it doesn't leak into Odoo UI
        combined_css = "\n".join(styles)
        # Replace bare 'body' selector with the wrapper class
        combined_css = re.sub(
            r"(^|\s|,)body\s*\{",
            r"\1.kebony-deck {",
            combined_css,
        )
        parts.append(f"<style>{combined_css}</style>")

    parts.append('<div class="kebony-deck" style="overflow-x:auto;">')
    parts.append(body)
    parts.append("</div>")

    return "\n".join(parts)


UPPERCASE_WORDS = {"vvf", "it", "cogs", "us", "erp", "ax", "opex", "capex", "bol"}

def deck_display_name(filename: str) -> str:
    """Convert filename to a human-readable deck title.

    'costing_architecture' → 'Costing Architecture'
    'vvf_it_opex'          → 'VVF IT OPEX'
    """
    words = filename.replace("_", " ").replace("-", " ").split()
    return " ".join(
        w.upper() if w.lower() in UPPERCASE_WORDS else w.capitalize()
        for w in words
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

    def upsert_attachment(
        self, name: str, data: bytes, res_model: str = None,
        res_id: int = None, public: bool = False,
    ) -> int:
        """Upload a binary file as ir.attachment. Returns attachment ID."""
        b64_data = base64.b64encode(data).decode("ascii")

        # Search for existing attachment with same name on same record
        domain = [["name", "=", name]]
        if res_model:
            domain.append(["res_model", "=", res_model])
        if res_id:
            domain.append(["res_id", "=", res_id])

        existing = self._execute("ir.attachment", "search", [domain], {"limit": 1})

        if existing:
            if self.dry_run:
                print(f"  [DRY RUN] Would UPDATE attachment: {name} (id={existing[0]})")
                return existing[0]
            write_vals = {"datas": b64_data}
            if public:
                write_vals["public"] = True
            self._execute(
                "ir.attachment", "write",
                [existing, write_vals],
            )
            print(f"  ✓ Updated attachment: {name} (id={existing[0]})")
            return existing[0]
        else:
            vals = {
                "name": name,
                "datas": b64_data,
                "type": "binary",
            }
            if res_model:
                vals["res_model"] = res_model
            if res_id:
                vals["res_id"] = res_id
            if public:
                vals["public"] = True
            if self.dry_run:
                print(f"  [DRY RUN] Would CREATE attachment: {name}")
                return -1
            att_id = self._execute("ir.attachment", "create", [vals])
            print(f"  ✓ Created attachment: {name} (id={att_id})")
            return att_id


# ── Sync logic ──────────────────────────────────────────────────────────────

def sync_articles(odoo: OdooKnowledge, base_path: Path) -> int:
    """Push markdown articles to Odoo. Returns root article ID."""

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

    return root_id


def sync_slide_decks(odoo: OdooKnowledge, base_path: Path, root_id: int):
    """Generate PDFs from HTML decks and push to Odoo Knowledge."""

    slide_path = base_path / SLIDE_DECKS_DIR
    if not slide_path.is_dir():
        print(f"\n  ⊘ Slide decks directory not found: {SLIDE_DECKS_DIR}")
        return

    html_files = sorted(slide_path.glob("*.html"))
    if not html_files:
        print(f"\n  ⊘ No HTML files in {SLIDE_DECKS_DIR}")
        return

    print("\n── Slide Decks ──")
    section_id = odoo.upsert_article(
        SLIDE_DECKS_DIR,
        "<p>Presentation decks — auto-synced with PDF downloads.</p>",
        parent_id=root_id,
        sequence=20,
    )

    for seq, html_file in enumerate(html_files, start=1):
        deck_name = deck_display_name(html_file.stem)
        print(f"\n  ── {deck_name} ──")

        # ── Generate PDF ────────────────────────────────────────────
        pdf_path = None
        pdf_ok = False
        try:
            fd, tmp = tempfile.mkstemp(suffix=".pdf")
            os.close(fd)
            pdf_path = Path(tmp)
            pdf_ok = html_to_pdf(html_file, pdf_path)
            if pdf_ok:
                size_kb = pdf_path.stat().st_size / 1024
                print(f"  ✓ PDF generated: {size_kb:.0f} KB")
        except Exception as exc:
            print(f"  ✗ PDF error: {exc}")

        # ── Create article (placeholder body first) ─────────────────
        placeholder = f"<p>Loading {deck_name}…</p>"
        article_id = odoo.upsert_article(
            deck_name, placeholder,
            parent_id=section_id, sequence=seq,
        )

        # ── Upload PDF attachment (public so link works) ─────────────
        att_id = None
        if pdf_ok and article_id and article_id > 0:
            pdf_data = pdf_path.read_bytes()
            att_id = odoo.upsert_attachment(
                f"{html_file.stem}.pdf",
                pdf_data,
                res_model="knowledge.article",
                res_id=article_id,
                public=True,
            )

        # ── Build article body: download link ─────────────────────
        # Odoo's html_sanitize strips <iframe> and may mangle relative
        # URLs / heavy inline styles.  Keep it simple: a plain <a> with
        # an absolute URL and target=_blank.
        if att_id and att_id > 0:
            abs_url = f"{odoo.url}/web/content/{att_id}?download=true"
            final_body = (
                f'<p><a href="{abs_url}" target="_blank">'
                f"📄 Download PDF — {deck_name}"
                f"</a></p>"
            )
        else:
            final_body = "<p>PDF not available — re-run sync.</p>"

        # Update article with final body
        if article_id and article_id > 0 and not odoo.dry_run:
            odoo._execute(
                "knowledge.article", "write",
                [[article_id], {"body": final_body}],
            )
            print(f"  ✓ Article body updated with download link")

        # ── Also save PDF locally ───────────────────────────────────
        if pdf_ok:
            local_pdf = slide_path / f"{html_file.stem}.pdf"
            local_pdf.write_bytes(pdf_path.read_bytes())
            print(f"  ✓ Local PDF saved: {local_pdf.name}")

        # Cleanup temp
        if pdf_path and pdf_path.exists():
            pdf_path.unlink()


def sync(odoo: OdooKnowledge, base_path: Path, slides_only: bool = False):
    """Push the full knowledge base to Odoo."""

    if slides_only:
        # Still need root article for parenting
        print("\n── Finding root article ──")
        root_id = odoo.find_article("Kebony Knowledge Base", None)
        if not root_id:
            root_id = odoo.upsert_article(
                "Kebony Knowledge Base",
                "<p>Kebony ERP implementation knowledge base — synced from Obsidian.</p>",
                parent_id=None,
                sequence=1,
            )
    else:
        root_id = sync_articles(odoo, base_path)

    # 4. Slide Decks (always)
    sync_slide_decks(odoo, base_path, root_id)

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
    parser.add_argument(
        "--slides-only",
        action="store_true",
        help="Only sync slide decks (skip markdown articles)",
    )

    args = parser.parse_args()

    base_path = Path(args.path)
    if not (base_path / "00 - Index.md").exists():
        print(f"✗ Not a valid knowledge base: {base_path}")
        sys.exit(1)

    odoo = OdooKnowledge(args.env, args.user, args.api_key, dry_run=args.dry_run)
    odoo.connect()
    sync(odoo, base_path, slides_only=args.slides_only)


if __name__ == "__main__":
    main()
