#!/usr/bin/env python3
"""
Kebony Sales Dashboard Audit
=============================
Compares sales orders, invoices, and dashboard report data
to identify discrepancies in the sales & cash pipelines.

Target: Kebony TEST instance (development)
"""

import xmlrpc.client
import ssl
import json
from collections import defaultdict
from datetime import datetime

# ── SSL workaround for dev instances ──────────────────────
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


class SafeTransport(xmlrpc.client.SafeTransport):
    def make_connection(self, host):
        conn = super().make_connection(host)
        conn._http_vsn_str = "HTTP/1.0"
        return conn

    def send_content(self, connection, request_body):
        connection.putheader("Content-Type", "text/xml")
        connection.putheader("Content-Length", str(len(request_body)))
        connection.endheaders(request_body)


# ── Connection ────────────────────────────────────────────
URL = "https://kebonyprod.odoo.com"
DB = "kebonyprod-main-26738590"
USER = "admin"
API_KEY = "86a5f0f4d63bb7a730fbf8df4a7ba93224c98824"

common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, USER, API_KEY, {})
models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")

if not uid:
    print("❌ Authentication failed!")
    exit(1)

print(f"✅ Connected to {URL} as uid={uid}")
print(f"   Database: {DB}")
print()


def search_read(model, domain, fields, limit=0, order=""):
    """Helper: search_read with error handling."""
    kwargs = {"limit": limit}
    if order:
        kwargs["order"] = order
    return models.execute_kw(DB, uid, API_KEY, model, "search_read",
                             [domain], {"fields": fields, **kwargs})


def search_count(model, domain):
    return models.execute_kw(DB, uid, API_KEY, model, "search_count", [domain])


# ══════════════════════════════════════════════════════════
# PART 1: INVENTORY OF DATA
# ══════════════════════════════════════════════════════════
print("=" * 70)
print("PART 1: DATA INVENTORY")
print("=" * 70)

# Companies
companies = search_read("res.company", [], ["name", "x_kebony_entity_type"])
print("\n📌 Companies:")
for c in companies:
    print(f"   [{c['id']}] {c['name']} → entity_type: {c.get('x_kebony_entity_type', 'N/A')}")

# Sales Orders — all confirmed+
so_states = {}
for state in ["sale", "done", "cancel"]:
    count = search_count("sale.order", [("state", "=", state)])
    so_states[state] = count
print(f"\n📌 Sales Orders:")
for s, c in so_states.items():
    print(f"   {s}: {c}")

# Invoices — all posted
inv_types = {}
for move_type in ["out_invoice", "out_refund"]:
    for state in ["draft", "posted", "cancel"]:
        count = search_count("account.move", [
            ("move_type", "=", move_type),
            ("state", "=", state)
        ])
        inv_types[f"{move_type}/{state}"] = count
print(f"\n📌 Invoices & Credit Notes:")
for k, c in inv_types.items():
    print(f"   {k}: {c}")

# Dashboard records
try:
    dash_count = search_count("report.sales.dashboard", [])
    print(f"\n📌 Dashboard report records: {dash_count}")
except Exception as e:
    print(f"\n⚠️  Dashboard model not accessible: {e}")
    dash_count = 0


# ══════════════════════════════════════════════════════════
# PART 2: SALES ORDER → INVOICE LINKAGE AUDIT
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PART 2: SALES ORDER → INVOICE LINKAGE")
print("=" * 70)

# Get all confirmed SOs with their invoice status
sos = search_read("sale.order", [
    ("state", "in", ["sale", "done"])
], [
    "name", "partner_id", "amount_untaxed", "invoice_status",
    "commitment_date", "date_order", "company_id",
    "x_kebony_total_volume_m3",
    "invoice_ids",
], limit=0)

print(f"\n📌 Confirmed Sales Orders: {len(sos)}")

# Categorise by invoice_status
status_buckets = defaultdict(list)
for so in sos:
    status_buckets[so.get("invoice_status", "unknown")].append(so)

print("\n   By invoice_status:")
for status, items in sorted(status_buckets.items()):
    total_amount = sum(s["amount_untaxed"] for s in items)
    print(f"   {status}: {len(items)} orders, total untaxed: €{total_amount:,.2f}")

# SOs with no invoices at all
no_invoice_sos = [so for so in sos if not so.get("invoice_ids")]
print(f"\n⚠️  Confirmed SOs with ZERO invoices: {len(no_invoice_sos)}")
if no_invoice_sos:
    total_uninvoiced = sum(s["amount_untaxed"] for s in no_invoice_sos)
    print(f"   Total uninvoiced amount: €{total_uninvoiced:,.2f}")
    for so in no_invoice_sos[:20]:
        print(f"   - {so['name']}: €{so['amount_untaxed']:,.2f} "
              f"(status: {so.get('invoice_status', '?')}, "
              f"date: {so.get('date_order', '?')})")
    if len(no_invoice_sos) > 20:
        print(f"   ... and {len(no_invoice_sos) - 20} more")


# ══════════════════════════════════════════════════════════
# PART 3: INVOICE AMOUNT RECONCILIATION
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PART 3: INVOICE AMOUNT RECONCILIATION (SO vs Invoice)")
print("=" * 70)

# Get all posted invoices with SO linkage
invoices = search_read("account.move", [
    ("move_type", "in", ["out_invoice", "out_refund"]),
    ("state", "=", "posted"),
], [
    "name", "move_type", "partner_id", "amount_untaxed_signed",
    "amount_residual_signed", "invoice_date", "company_id",
    "x_kebony_total_volume_m3",
    "x_kebony_is_us",
    "line_ids",
], limit=0)

print(f"\n📌 Posted invoices/refunds: {len(invoices)}")

inv_total = sum(i["amount_untaxed_signed"] for i in invoices)
inv_invoices = [i for i in invoices if i["move_type"] == "out_invoice"]
inv_refunds = [i for i in invoices if i["move_type"] == "out_refund"]
print(f"   Invoices: {len(inv_invoices)}, total: €{sum(i['amount_untaxed_signed'] for i in inv_invoices):,.2f}")
print(f"   Refunds:  {len(inv_refunds)}, total: €{sum(i['amount_untaxed_signed'] for i in inv_refunds):,.2f}")
print(f"   Net:      €{inv_total:,.2f}")

# Outstanding balance (cash pipeline)
outstanding = sum(i["amount_residual_signed"] for i in invoices if abs(i["amount_residual_signed"]) > 0.01)
paid = inv_total - outstanding
print(f"\n💰 Cash Pipeline:")
print(f"   Total invoiced (net): €{inv_total:,.2f}")
print(f"   Already paid:         €{paid:,.2f}")
print(f"   Outstanding (to cash in): €{outstanding:,.2f}")


# ══════════════════════════════════════════════════════════
# PART 4: SO-LEVEL RECONCILIATION
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PART 4: SO-LEVEL AMOUNT RECONCILIATION")
print("=" * 70)

# For each SO with invoices, compare SO amount vs total invoiced
discrepancies = []
for so in sos:
    if not so.get("invoice_ids"):
        continue

    # Get invoices linked to this SO
    so_invoices = [i for i in invoices if i["id"] in so["invoice_ids"]]
    if not so_invoices:
        continue

    so_amount = so["amount_untaxed"]
    inv_amount = sum(i["amount_untaxed_signed"] for i in so_invoices)
    diff = abs(so_amount - inv_amount)

    if diff > 1.0:  # More than €1 discrepancy
        discrepancies.append({
            "so": so["name"],
            "so_amount": so_amount,
            "inv_amount": inv_amount,
            "diff": so_amount - inv_amount,
            "invoice_status": so.get("invoice_status", "?"),
            "invoices": [i["name"] for i in so_invoices],
        })

print(f"\n📌 SOs with invoices checked: {len([s for s in sos if s.get('invoice_ids')])}")
print(f"⚠️  Discrepancies (|SO - invoiced| > €1): {len(discrepancies)}")

if discrepancies:
    discrepancies.sort(key=lambda d: abs(d["diff"]), reverse=True)
    total_gap = sum(d["diff"] for d in discrepancies)
    print(f"   Total gap: €{total_gap:,.2f}")
    print(f"\n   Top discrepancies:")
    for d in discrepancies[:30]:
        print(f"   {d['so']}: SO €{d['so_amount']:,.2f} vs INV €{d['inv_amount']:,.2f} "
              f"→ gap €{d['diff']:,.2f} (status: {d['invoice_status']}) "
              f"[{', '.join(d['invoices'][:3])}]")
    if len(discrepancies) > 30:
        print(f"   ... and {len(discrepancies) - 30} more")


# ══════════════════════════════════════════════════════════
# PART 5: VOLUME AUDIT
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PART 5: VOLUME (m³) AUDIT")
print("=" * 70)

so_volume = sum(s.get("x_kebony_total_volume_m3") or 0 for s in sos)
inv_volume = sum(i.get("x_kebony_total_volume_m3") or 0 for i in invoices)
print(f"\n📌 Total volume on confirmed SOs: {so_volume:,.3f} m³")
print(f"📌 Total volume on posted invoices: {inv_volume:,.3f} m³")
print(f"   Gap: {so_volume - inv_volume:,.3f} m³")

# Check for invoices with zero volume
zero_vol_inv = [i for i in invoices if not i.get("x_kebony_total_volume_m3")]
print(f"\n⚠️  Posted invoices with ZERO volume: {len(zero_vol_inv)} of {len(invoices)}")
if zero_vol_inv:
    for i in zero_vol_inv[:10]:
        print(f"   - {i['name']}: €{i['amount_untaxed_signed']:,.2f} (date: {i.get('invoice_date', '?')})")


# ══════════════════════════════════════════════════════════
# PART 6: DASHBOARD CROSS-CHECK
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PART 6: DASHBOARD REPORT CROSS-CHECK")
print("=" * 70)

if dash_count > 0:
    try:
        # Read dashboard data grouped by metric_type
        dash_data = search_read("report.sales.dashboard", [], [
            "metric_type", "view_type", "amount", "volume_m3",
            "sales_area", "month", "partner_id", "move_id", "order_id",
        ], limit=0)

        print(f"\n📌 Dashboard records: {len(dash_data)}")

        # Aggregate by metric_type
        by_metric = defaultdict(lambda: {"count": 0, "amount": 0, "volume": 0})
        for r in dash_data:
            mt = r.get("metric_type", "unknown")
            by_metric[mt]["count"] += 1
            by_metric[mt]["amount"] += r.get("amount") or 0
            by_metric[mt]["volume"] += r.get("volume_m3") or 0

        print("\n   By metric_type:")
        print(f"   {'Metric':<15} {'Count':>8} {'Amount':>15} {'Volume m³':>12}")
        print(f"   {'-'*15} {'-'*8} {'-'*15} {'-'*12}")
        for mt in ["invoiced", "to_invoice", "prepayment", "to_cash_in", "paid"]:
            d = by_metric.get(mt, {"count": 0, "amount": 0, "volume": 0})
            print(f"   {mt:<15} {d['count']:>8} {d['amount']:>15,.2f} {d['volume']:>12,.3f}")

        # Cross-check: dashboard "invoiced" vs actual posted invoices
        dash_invoiced = by_metric.get("invoiced", {}).get("amount", 0)
        actual_invoiced = inv_total
        diff = dash_invoiced - actual_invoiced
        print(f"\n🔍 CROSS-CHECK: Dashboard 'invoiced' vs actual posted invoices:")
        print(f"   Dashboard total:  €{dash_invoiced:,.2f}")
        print(f"   Actual total:     €{actual_invoiced:,.2f}")
        print(f"   Difference:       €{diff:,.2f}")
        if abs(diff) > 1:
            print(f"   ⚠️  MISMATCH DETECTED!")
        else:
            print(f"   ✅ Match (within €1)")

        # Cross-check: dashboard volume vs actual
        dash_inv_volume = by_metric.get("invoiced", {}).get("volume", 0)
        diff_vol = dash_inv_volume - inv_volume
        print(f"\n🔍 CROSS-CHECK: Dashboard 'invoiced' volume vs actual:")
        print(f"   Dashboard volume: {dash_inv_volume:,.3f} m³")
        print(f"   Actual volume:    {inv_volume:,.3f} m³")
        print(f"   Difference:       {diff_vol:,.3f} m³")
        if abs(diff_vol) > 0.01:
            print(f"   ⚠️  MISMATCH DETECTED!")
        else:
            print(f"   ✅ Match")

        # Cross-check: "to_invoice" should match SOs not fully invoiced
        dash_to_invoice = by_metric.get("to_invoice", {}).get("amount", 0)
        actual_to_invoice = sum(s["amount_untaxed"] for s in sos if s.get("invoice_status") == "to invoice")
        print(f"\n🔍 CROSS-CHECK: Dashboard 'to_invoice' vs SO invoice_status:")
        print(f"   Dashboard total:  €{dash_to_invoice:,.2f}")
        print(f"   SO 'to invoice':  €{actual_to_invoice:,.2f}")
        diff_ti = dash_to_invoice - actual_to_invoice
        print(f"   Difference:       €{diff_ti:,.2f}")
        if abs(diff_ti) > 1:
            print(f"   ⚠️  MISMATCH — dashboard computes TO_INVOICE differently (SO amount - already invoiced)")

        # Cross-check: cash pipeline
        dash_paid = by_metric.get("paid", {}).get("amount", 0)
        dash_to_cash = by_metric.get("to_cash_in", {}).get("amount", 0)
        print(f"\n🔍 CROSS-CHECK: Cash Pipeline:")
        print(f"   Dashboard 'paid':       €{dash_paid:,.2f}")
        print(f"   Dashboard 'to_cash_in': €{dash_to_cash:,.2f}")
        print(f"   Dashboard cash total:   €{dash_paid + dash_to_cash:,.2f}")
        print(f"   Actual invoiced total:  €{actual_invoiced:,.2f}")
        diff_cash = (dash_paid + dash_to_cash) - actual_invoiced
        print(f"   Difference:             €{diff_cash:,.2f}")
        if abs(diff_cash) > 1:
            print(f"   ⚠️  CASH PIPELINE MISMATCH!")
        else:
            print(f"   ✅ Cash pipeline balances")

        # Check for dashboard records with missing sales_area
        no_area = [r for r in dash_data if not r.get("sales_area")]
        print(f"\n⚠️  Dashboard records with NO sales_area: {len(no_area)} of {len(dash_data)}")
        if no_area:
            no_area_amount = sum(r.get("amount") or 0 for r in no_area)
            print(f"   Total amount without area: €{no_area_amount:,.2f}")

    except Exception as e:
        print(f"\n❌ Error reading dashboard: {e}")
else:
    print("\n⚠️  Dashboard model has no records — cannot cross-check")
    print("   This could mean the SQL view hasn't been created or the module isn't installed on test")


# ══════════════════════════════════════════════════════════
# PART 7: PREPAYMENT / DOWN-PAYMENT AUDIT
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PART 7: PREPAYMENT AUDIT")
print("=" * 70)

try:
    prepayments = search_read("account.move", [
        ("move_type", "=", "out_invoice"),
        ("state", "=", "posted"),
        ("x_is_prepayment", "=", True),
    ], ["name", "amount_untaxed_signed", "partner_id", "invoice_date"], limit=0)

    print(f"\n📌 Prepayment invoices (posted, x_is_prepayment=True): {len(prepayments)}")
    if prepayments:
        pp_total = sum(p["amount_untaxed_signed"] for p in prepayments)
        print(f"   Total prepayment amount: €{pp_total:,.2f}")
        for p in prepayments[:10]:
            print(f"   - {p['name']}: €{p['amount_untaxed_signed']:,.2f} ({p.get('invoice_date', '?')})")
except Exception as e:
    print(f"   ⚠️  Could not read prepayments: {e}")


# ══════════════════════════════════════════════════════════
# PART 8: US-SPECIFIC ACCRUAL CHECK
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PART 8: US ACCRUAL CHECK")
print("=" * 70)

us_invoices = [i for i in invoices if i.get("x_kebony_is_us")]
print(f"\n📌 US invoices (x_kebony_is_us=True): {len(us_invoices)}")
if us_invoices:
    us_total = sum(i["amount_untaxed_signed"] for i in us_invoices)
    print(f"   US invoiced total: €{us_total:,.2f}")

    # Check accrual fields on invoice lines for US invoices
    us_inv_ids = [i["id"] for i in us_invoices[:50]]  # Sample first 50
    if us_inv_ids:
        try:
            us_lines = search_read("account.move.line", [
                ("move_id", "in", us_inv_ids),
                ("display_type", "=", False),
                ("exclude_from_invoice_tab", "=", False),
            ], [
                "move_id", "product_id", "price_subtotal",
                "x_studio_marketing_accrual_line_item",
                "x_studio_royalities_1",
                "x_studio_royalties_mngmt_fees_charge",
                "x_studio_sales_rep_charge",
                "x_studio_is_accrued",
            ], limit=500)

            accrued = [l for l in us_lines if l.get("x_studio_is_accrued")]
            not_accrued = [l for l in us_lines if not l.get("x_studio_is_accrued") and l.get("price_subtotal")]

            print(f"\n   Invoice lines sampled: {len(us_lines)}")
            print(f"   Lines with accruals computed (is_accrued=True): {len(accrued)}")
            print(f"   Lines WITHOUT accruals (is_accrued=False): {len(not_accrued)}")

            if not_accrued:
                not_accrued_total = sum(l.get("price_subtotal") or 0 for l in not_accrued)
                print(f"   ⚠️  Un-accrued revenue: €{not_accrued_total:,.2f}")

            # Check for zero accrual values on accrued lines
            zero_marketing = [l for l in accrued if not l.get("x_studio_marketing_accrual_line_item")]
            zero_royalties = [l for l in accrued if not l.get("x_studio_royalities_1")]
            zero_mgmt = [l for l in accrued if not l.get("x_studio_royalties_mngmt_fees_charge")]

            print(f"\n   Accrued lines with zero marketing:  {len(zero_marketing)} / {len(accrued)}")
            print(f"   Accrued lines with zero royalties:  {len(zero_royalties)} / {len(accrued)}")
            print(f"   Accrued lines with zero mgmt fees:  {len(zero_mgmt)} / {len(accrued)}")

        except Exception as e:
            print(f"   ⚠️  Could not read invoice lines: {e}")


# ══════════════════════════════════════════════════════════
# PART 9: CONSIGNMENT CHECK
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PART 9: CONSIGNMENT AUDIT")
print("=" * 70)

try:
    consignment_pos = search_read("purchase.order", [
        ("x_kebony_is_consignment_po", "=", True),
    ], ["name", "partner_id", "amount_untaxed", "state", "date_order"], limit=0)

    print(f"\n📌 Consignment POs (x_kebony_is_consignment_po=True): {len(consignment_pos)}")
    if consignment_pos:
        for state in set(p["state"] for p in consignment_pos):
            state_pos = [p for p in consignment_pos if p["state"] == state]
            total = sum(p["amount_untaxed"] for p in state_pos)
            print(f"   {state}: {len(state_pos)} POs, total: €{total:,.2f}")
except Exception as e:
    print(f"   ⚠️  Could not read consignment POs: {e}")

try:
    consignment_prices = search_count("stock.consignment.price", [])
    print(f"\n📌 Consignment price table entries: {consignment_prices}")
except Exception as e:
    print(f"   ⚠️  Consignment price model not found: {e}")


# ══════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("AUDIT SUMMARY")
print("=" * 70)
print(f"""
📊 Data Inventory:
   Sales Orders (confirmed): {len(sos)}
   Posted Invoices:          {len(invoices)}
   Dashboard Records:        {dash_count}

💰 Financial Totals:
   SO total untaxed:         €{sum(s['amount_untaxed'] for s in sos):,.2f}
   Invoice total (net):      €{inv_total:,.2f}
   Outstanding (to cash in): €{outstanding:,.2f}

📦 Volume:
   SO volume:                {so_volume:,.3f} m³
   Invoice volume:           {inv_volume:,.3f} m³

⚠️  Key Findings:
   SOs with zero invoices:   {len(no_invoice_sos)}
   SO↔Invoice discrepancies: {len(discrepancies)}
   Zero-volume invoices:     {len(zero_vol_inv)}
   US invoices:              {len(us_invoices)}
""")

print("Audit complete. Review findings above for dashboard issues.")
