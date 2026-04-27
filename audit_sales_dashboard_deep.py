#!/usr/bin/env python3
"""
Kebony Sales Dashboard Audit — DEEP DIVE
=========================================
Follow-up on critical findings from initial audit.
"""

import xmlrpc.client
from collections import defaultdict

URL = "https://kebonyprod.odoo.com"
DB = "kebonyprod-main-26738590"
USER = "admin"
API_KEY = "86a5f0f4d63bb7a730fbf8df4a7ba93224c98824"

common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, USER, API_KEY, {})
models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")
print(f"✅ Connected as uid={uid}\n")


def search_read(model, domain, fields, limit=0, order=""):
    kwargs = {"limit": limit}
    if order:
        kwargs["order"] = order
    return models.execute_kw(DB, uid, API_KEY, model, "search_read",
                             [domain], {"fields": fields, **kwargs})


# ══════════════════════════════════════════════════════════
# DEEP DIVE 1: WHY 20 OF 38 INVOICES HAVE ZERO VOLUME
# ══════════════════════════════════════════════════════════
print("=" * 70)
print("DEEP DIVE 1: ZERO-VOLUME INVOICES")
print("=" * 70)

invoices = search_read("account.move", [
    ("move_type", "in", ["out_invoice", "out_refund"]),
    ("state", "=", "posted"),
], [
    "name", "move_type", "amount_untaxed_signed", "invoice_date",
    "x_kebony_total_volume_m3", "x_kebony_total_linear_m", "x_kebony_total_boards",
    "x_is_prepayment",
], limit=0, order="invoice_date desc")

zero_vol = [i for i in invoices if not i.get("x_kebony_total_volume_m3")]
has_vol = [i for i in invoices if i.get("x_kebony_total_volume_m3")]

print(f"\nTotal posted invoices: {len(invoices)}")
print(f"With volume: {len(has_vol)}")
print(f"Without volume: {len(zero_vol)}")

# Hypothesis: prepayment invoices don't have physical lines → no volume
prepay_zero = [i for i in zero_vol if i.get("x_is_prepayment")]
non_prepay_zero = [i for i in zero_vol if not i.get("x_is_prepayment")]

print(f"\nZero-volume breakdown:")
print(f"  Prepayment invoices (x_is_prepayment=True): {len(prepay_zero)}")
print(f"  Regular invoices with zero volume:          {len(non_prepay_zero)}")

if prepay_zero:
    pp_total = sum(i["amount_untaxed_signed"] for i in prepay_zero)
    print(f"\n  Prepayment zero-vol total: €{pp_total:,.2f}")
    print(f"  → These are DOWN-PAYMENT invoices — they have no product lines,")
    print(f"    only a 'Down Payment' line. Volume=0 is EXPECTED.")

if non_prepay_zero:
    print(f"\n  ⚠️  NON-PREPAYMENT invoices with zero volume:")
    for i in non_prepay_zero:
        print(f"    {i['name']}: €{i['amount_untaxed_signed']:,.2f} "
              f"(date: {i.get('invoice_date')}, "
              f"linear_m: {i.get('x_kebony_total_linear_m', 0)}, "
              f"boards: {i.get('x_kebony_total_boards', 0)})")

# ══════════════════════════════════════════════════════════
# DEEP DIVE 2: INVOICE LINES — WHY NO LINES RETURNED
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("DEEP DIVE 2: INVOICE LINE METRICS")
print("=" * 70)

# Try reading invoice lines without the exclude filter
sample_inv = invoices[0]  # Most recent invoice
print(f"\nSampling invoice: {sample_inv['name']} (€{sample_inv['amount_untaxed_signed']:,.2f})")

# Get ALL lines for this invoice
all_lines = search_read("account.move.line", [
    ("move_id", "=", sample_inv["id"]),
], [
    "name", "product_id", "quantity", "price_unit", "price_subtotal",
    "display_type", "account_id",
    "x_studio_linear_feet", "x_boards",
    "x_kebony_volume_m3", "x_kebony_price_m3",
], limit=0)

print(f"Total lines on this invoice: {len(all_lines)}")
for line in all_lines:
    prod = line.get("product_id")
    prod_name = prod[1] if prod else "(no product)"
    dt = line.get("display_type") or "regular"
    acct = line.get("account_id")
    acct_name = acct[1] if acct else ""
    print(f"  [{dt}] {prod_name[:50]}")
    print(f"    qty={line.get('quantity')}, price={line.get('price_unit')}, "
          f"subtotal={line.get('price_subtotal')}")
    print(f"    linear_m={line.get('x_studio_linear_feet', 0)}, "
          f"boards={line.get('x_boards', 0)}, "
          f"vol_m3={line.get('x_kebony_volume_m3', 0)}")
    print(f"    account: {acct_name}")

# Now sample a NON-prepayment invoice with volume
for inv in invoices:
    if inv.get("x_kebony_total_volume_m3") and not inv.get("x_is_prepayment"):
        print(f"\n\nSampling invoice WITH volume: {inv['name']} "
              f"(€{inv['amount_untaxed_signed']:,.2f}, vol={inv['x_kebony_total_volume_m3']:.3f} m³)")
        lines = search_read("account.move.line", [
            ("move_id", "=", inv["id"]),
        ], [
            "name", "product_id", "quantity", "price_unit", "price_subtotal",
            "display_type",
            "x_studio_linear_feet", "x_boards",
            "x_kebony_volume_m3",
            "x_studio_marketing_accrual_line_item",
            "x_studio_royalities_1",
            "x_studio_royalties_mngmt_fees_charge",
            "x_studio_sales_rep_charge",
            "x_studio_is_accrued",
        ], limit=0)

        print(f"Total lines: {len(lines)}")
        product_lines = [l for l in lines if not l.get("display_type")]
        print(f"Product lines (non-display): {len(product_lines)}")

        for line in product_lines[:10]:
            prod = line.get("product_id")
            prod_name = prod[1] if prod else "(no product)"
            print(f"  {prod_name[:60]}")
            print(f"    qty={line.get('quantity')}, subtotal=€{line.get('price_subtotal', 0):,.2f}")
            print(f"    linear_m={line.get('x_studio_linear_feet', 0):.3f}, "
                  f"boards={line.get('x_boards', 0)}, "
                  f"vol_m3={line.get('x_kebony_volume_m3', 0):.4f}")
            print(f"    accruals: mktg={line.get('x_studio_marketing_accrual_line_item', 0)}, "
                  f"royal={line.get('x_studio_royalities_1', 0)}, "
                  f"mgmt={line.get('x_studio_royalties_mngmt_fees_charge', 0)}, "
                  f"sales_rep={line.get('x_studio_sales_rep_charge', 0)}, "
                  f"is_accrued={line.get('x_studio_is_accrued')}")
        break


# ══════════════════════════════════════════════════════════
# DEEP DIVE 3: DASHBOARD SQL VIEW EXISTENCE
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("DEEP DIVE 3: DASHBOARD MODEL STATUS")
print("=" * 70)

# Check if the model is registered
try:
    model_info = search_read("ir.model", [
        ("model", "=", "report.sales.dashboard")
    ], ["name", "model", "state", "info"], limit=1)
    if model_info:
        print(f"\n✅ Model 'report.sales.dashboard' is registered:")
        for k, v in model_info[0].items():
            if k != "id":
                print(f"   {k}: {v}")
    else:
        print("\n❌ Model 'report.sales.dashboard' NOT registered in ir.model")
        print("   → The module may not be installed on production")
except Exception as e:
    print(f"\n❌ Error checking model: {e}")

# Check installed modules
try:
    mod = search_read("ir.module.module", [
        ("name", "=", "kebony_bol_report")
    ], ["name", "state", "installed_version"], limit=1)
    if mod:
        print(f"\n📌 Module kebony_bol_report:")
        print(f"   State: {mod[0].get('state')}")
        print(f"   Version: {mod[0].get('installed_version')}")
    else:
        print("\n❌ Module kebony_bol_report NOT found")
except Exception as e:
    print(f"   Error: {e}")


# ══════════════════════════════════════════════════════════
# DEEP DIVE 4: FULL SO → INVOICE → PAYMENT CHAIN
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("DEEP DIVE 4: FULL ORDER-TO-CASH CHAIN")
print("=" * 70)

# Get SOs with their invoices
sos = search_read("sale.order", [
    ("state", "in", ["sale", "done"])
], [
    "name", "partner_id", "amount_untaxed", "invoice_status",
    "date_order", "commitment_date", "company_id",
    "invoice_ids", "x_kebony_total_volume_m3",
], limit=0, order="date_order desc")

print(f"\nFull Order-to-Cash mapping ({len(sos)} confirmed SOs):\n")
print(f"{'SO':<10} {'Partner':<30} {'SO Amount':>12} {'Status':<12} "
      f"{'#Inv':>4} {'Inv Total':>12} {'Residual':>12} {'Vol m³':>8} {'Prepay €':>12}")
print("-" * 130)

for so in sos:
    inv_ids = so.get("invoice_ids", [])
    partner = so["partner_id"][1] if so.get("partner_id") else "?"

    # Get linked invoices
    inv_total = 0
    inv_residual = 0
    prepay_total = 0
    if inv_ids:
        linked_invs = search_read("account.move", [
            ("id", "in", inv_ids),
            ("state", "=", "posted"),
        ], [
            "name", "amount_untaxed_signed", "amount_residual_signed",
            "x_is_prepayment", "move_type",
        ], limit=0)

        for inv in linked_invs:
            inv_total += inv["amount_untaxed_signed"]
            inv_residual += inv.get("amount_residual_signed", 0)
            if inv.get("x_is_prepayment"):
                prepay_total += inv["amount_untaxed_signed"]

    vol = so.get("x_kebony_total_volume_m3") or 0
    print(f"{so['name']:<10} {partner[:30]:<30} {so['amount_untaxed']:>12,.2f} "
          f"{so.get('invoice_status', '?'):<12} {len(inv_ids):>4} "
          f"{inv_total:>12,.2f} {inv_residual:>12,.2f} {vol:>8.2f} {prepay_total:>12,.2f}")


# ══════════════════════════════════════════════════════════
# DEEP DIVE 5: PREPAYMENT IMPACT ON DASHBOARD
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("DEEP DIVE 5: PREPAYMENT ANALYSIS")
print("=" * 70)

all_prepays = search_read("account.move", [
    ("move_type", "=", "out_invoice"),
    ("state", "=", "posted"),
    ("x_is_prepayment", "=", True),
], [
    "name", "amount_untaxed_signed", "amount_residual_signed",
    "invoice_date", "partner_id",
    "x_kebony_total_volume_m3",
], limit=0, order="invoice_date desc")

regular_invs = search_read("account.move", [
    ("move_type", "=", "out_invoice"),
    ("state", "=", "posted"),
    ("x_is_prepayment", "!=", True),
], [
    "name", "amount_untaxed_signed", "amount_residual_signed",
    "invoice_date", "partner_id",
    "x_kebony_total_volume_m3",
], limit=0)

pp_total = sum(p["amount_untaxed_signed"] for p in all_prepays)
reg_total = sum(r["amount_untaxed_signed"] for r in regular_invs)

print(f"\n📌 Prepayment invoices: {len(all_prepays)}, total: €{pp_total:,.2f}")
print(f"📌 Regular invoices:    {len(regular_invs)}, total: €{reg_total:,.2f}")
print(f"📌 Combined:            €{pp_total + reg_total:,.2f}")
print(f"\n⚠️  Prepayments represent {pp_total / (pp_total + reg_total) * 100:.1f}% of total invoiced amount")
print(f"   If dashboard includes prepayments in 'invoiced' metric → DOUBLE-COUNTING risk")
print(f"   because the final invoice also includes the full SO amount")

# Check: do any SOs have both prepayment invoices AND regular invoices?
print(f"\n📌 Checking for SO double-counting (prepay + final invoice):")
for so in sos:
    if not so.get("invoice_ids"):
        continue
    linked = search_read("account.move", [
        ("id", "in", so["invoice_ids"]),
        ("state", "=", "posted"),
    ], ["name", "x_is_prepayment", "amount_untaxed_signed", "move_type"], limit=0)

    prepays = [i for i in linked if i.get("x_is_prepayment")]
    finals = [i for i in linked if not i.get("x_is_prepayment") and i["move_type"] == "out_invoice"]

    if prepays and finals:
        pp_sum = sum(p["amount_untaxed_signed"] for p in prepays)
        final_sum = sum(f["amount_untaxed_signed"] for f in finals)
        print(f"  {so['name']}: prepays €{pp_sum:,.2f} + finals €{final_sum:,.2f} = €{pp_sum + final_sum:,.2f} "
              f"(SO amount: €{so['amount_untaxed']:,.2f})")
        if pp_sum + final_sum > so["amount_untaxed"] * 1.01:
            print(f"    ⚠️  POTENTIAL DOUBLE-COUNT: sum of invoices > SO amount!")


# ══════════════════════════════════════════════════════════
# SUMMARY OF FINDINGS
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("AUDIT FINDINGS SUMMARY")
print("=" * 70)
print("""
🔴 CRITICAL:
   1. Dashboard model (report.sales.dashboard) NOT accessible on production.
      → Module may not be installed or SQL view not created.
      → Users cannot see the sales/cash pipeline dashboard.

🟡 IMPORTANT:
   2. 20 of 38 invoices have ZERO volume.
      → Hypothesis: prepayment invoices (11) have no product lines → volume=0 is expected.
      → Need to verify: are there regular invoices also missing volume?

   3. Prepayments = {pp_pct:.1f}% of total invoiced amount.
      → If the dashboard UNION includes both prepayments AND final invoices,
        the 'invoiced' metric is DOUBLE-COUNTED for SOs with down payments.
      → The SQL view has a separate 'prepayment' metric_type, but the total
        'invoiced' might still include prepayment amounts in PART 1.

   4. 4 SO↔Invoice discrepancies (total gap: €3,618)
      → Small amounts — likely partial deliveries or adjustments.

   5. 3 confirmed SOs with ZERO invoices (€321K uninvoiced)
      → S00026 and S00027 are large orders (~€154K each) from early March.
      → Need to check if these are blocked, awaiting delivery, or forgotten.

🟢 GOOD:
   6. Cash pipeline appears clean: €1.81M paid, €145K outstanding.
   7. Consignment flow working: 6 POs, 112 price table entries.
   8. All 38 posted invoices are US (Kebony Inc.) — entity gating works.
""".format(pp_pct=pp_total / (pp_total + reg_total) * 100))
