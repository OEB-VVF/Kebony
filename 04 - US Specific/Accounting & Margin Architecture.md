# US Accounting & Margin Architecture

**Scope**: Kebony Inc. (US entity) — Odoo 19
**Module**: `kebony_bol_report`
**Entity filter**: `x_kebony_entity_type == 'inc'`

> This document covers US-specific accounting features: FIFO valuation,
> accrual engine, margin/commission calculation, landed costs, and
> month-end close. It does NOT cover wood metrics or physical units
> (see [[Metrics & Physical Units]]) or consignment
> (see [[Consignment & Biewer]]).

---

## 1. Executive Summary

End-to-end accounting architecture, valuation model, journal flows, and
Odoo configuration for Kebony Inc., a lumber distribution company
operating under US GAAP and IFRS with FIFO inventory valuation and real
landed cost capitalisation.

The architecture supports:

- Accurate FIFO-based inventory valuation
- Integrated landed cost allocation
- Revenue-based accrual accounting (marketing, sales commissions,
  management fees, royalties, rebates, returns)
- Automated perpetual inventory posting
- Audit-ready journal mappings
- Consistent treatment of inventory adjustments (NRV, downgrade,
  slow-moving)
- Robust month-end close procedures

---

## 2. Important Terminology

### "Margin" in this document

The **margin** referred to throughout this module is the **US-specific
margin for commission calculation purposes**. It is NOT the official
Kebony margin definition.

The official Kebony margin is defined by **Contribution Margin (CM)
levels** and will be implemented in a future phase using:

- 4 analytical plans: **Country**, **BU** (cost centre / department P&L),
  **Sales Area** (US only), and **CM Level**
- Automatic allocation rules on journal entries to assign costs to
  country, sales area, BU, and CM level
- BoM-based decomposition to split COGS into direct (GM I) vs indirect (GM II)
- See [[Analytical Accounting Architecture]] for the full white paper

### US Margin Formula (current implementation)

```
Net Sales    = Revenue + Down Payments - Credit Notes
Margin       = Net Sales - COGS - Accruals - Freight - Warehousing - Other Adj.
Margin %     = Margin / Net Sales
```

**Down Payment handling**: When a final invoice is issued after a
prepayment, Odoo adds a negative deduction line reducing `amount_untaxed`.
The margin formula adds back the down payment revenue by tracing the
invoice → SO → sibling prepayment invoices (see §7.1).

**Prepayment invoices**: No margin is computed for invoices flagged
`x_is_prepayment = True`. The margin button is hidden on these documents.

This drives commission calculations for sales representatives.

---

## 3. Chart of Accounts Architecture

The Chart of Accounts supports FIFO valuation, in-transit/impairment
accounts, landed cost clearing, GRNI, sales-based accruals, and NRV
allowances.

### Key Inventory Accounts

| Code   | Description                    |
|--------|--------------------------------|
| 110200 | FIFO Valuation                 |
| 211100 | Bills to Receive (GRNI)        |
| 110410 | Landed Cost Clearing           |
| 110101-110105 | Lumber FG & impairment  |

### Accrual Liabilities (2155xx)

| Code   | Description              |
|--------|--------------------------|
| 215510 | Marketing Accrual        |
| 215520 | Sales Rep Accrual        |
| 215530 | Management Fees Accrual  |
| 215540 | Royalties Accrual        |
| 215550 | Return Accrual           |
| 215560 | Freight Accrual          |
| 215570 | Rebates Accrual          |

### Accrual Expenses (58xxxx)

Each accrual type has paired accounts:

| Type            | Accrual Expense | Actual Expense |
|-----------------|-----------------|----------------|
| Marketing       | 580110          | 580150         |
| Sales Rep       | 580210          | 580250         |
| Management Fees | 580310          | 580350         |
| Royalties       | 580410          | 580450         |
| Returns         | 580510          | -              |
| Rebates         | 580610          | -              |

---

## 4. Inventory Valuation Model (FIFO)

FIFO valuation generates real cost layers:

1. At **goods receipt** -> Odoo creates a valuation layer based on the PO
   price
2. At **delivery** -> Odoo consumes the oldest layers and posts COGS
3. **Landed costs** enrich existing layers
4. **Adjustments** (NRV, downgrade) reduce inventory value immediately

### Why FIFO for Lumber

- Lumber batches have real cost variability
- Quality grades impact cost non-uniformly
- FIFO preserves gross margin integrity
- Price variability makes standard cost inappropriate

### Financial Statement Implications

- Balance sheet reflects real historical costs
- COGS reflects true material flow
- Gross margin is not distorted by costing estimates

---

## 5. Landed Cost Framework

Landed costs include freight, duties, handling, and inbound processing.

### Two-Step Accounting Model

**Step 1 - Vendor bill:**
```
DR 110410  Landed Cost Clearing
    CR 211000  Accounts Payable
```

**Step 2 - Allocation:**
```
DR 110200  FIFO Valuation
    CR 110410  Landed Cost Clearing
```

### Capitalisation Rules (GAAP/IFRS)

| Capitalisable              | NOT Capitalisable        |
|----------------------------|--------------------------|
| Freight-in                 | Warehousing fees         |
| Customs, duties            | Storage                  |
| Inbound handling/processing| Outbound freight         |

---

## 6. Accrual Engine

### Two-Phase Architecture

**Phase 1: Line-Level Computation** (`account_move_line.py`)

Accrual amounts are computed and stored **per invoice line** as Studio fields.
This happens either:
- Automatically when the margin button is clicked (`_kebony_apply_accrual_vals(force=True)`)
- Could be triggered at invoice posting (not currently implemented)

**Phase 2: EOM Journal Entry** (`kebony_accounting_hub.py`)

At end-of-month, a button on the Accounting Hub collects all un-accrued lines
and posts a single journal entry with debit/credit pairs grouped by analytic account.

### Accrual Types & Rates (hardcoded)

| Type            | Wood  | Accessory | Condition              |
|-----------------|-------|-----------|------------------------|
| Marketing       | 4%    | 1.5%      | Distributors only (`x_studio_customer_catagory` = "Distributor") |
| Royalties       | 5%    | **0%**    | Wood only — not consignment. Accessories excluded. |
| Management Fees | 14%   | **5%**    | Not consignment        |
| Sales Rep       | variable | variable | From `x_studio_sales_rep_commission` or `x_studio_sales_rep_rate` |

> **Change log (Feb 2026):** Royalties reduced from 5% → 0% for
> accessories. Management fees reduced from 14% → 5% for accessories.
> Wood rates unchanged.

### Base Amount

`price_subtotal` (or `quantity * price_unit` as fallback). Always absolute value.

### Sign Convention

- `out_invoice`: positive accruals
- `out_refund`: negative accruals (sign = -1)

### GAAP/IFRS Justification (ASC 606 / IFRS 15)

Accruals are created **at the time of sale** because GAAP/IFRS requires
recognition of variable consideration when revenue is recognised. Companies must:

1. Estimate variable consideration (rebates, marketing contributions,
   returns, royalties)
2. Recognise it when revenue is recognised
3. Not wait for supplier invoices or actual events

This justifies booking provisions at sale time for: marketing contributions,
volume rebates, royalty costs, sales commissions, and returns reserve.

### Accrual Posting at Sale

```
DR 58xxxx  Accrual Expense
    CR 2155xx  Accrual Liability
```

### When the actual invoice arrives

**If actual = provision:**
```
DR 2155xx  Accrual Liability
    CR 211000  Accounts Payable
```

**If actual > provision:**
```
DR 2155xx  Accrual Liability
DR 58xxxx  Additional Expense
    CR 211000  Accounts Payable
```

**If actual < provision (release unused):**
```
DR 2155xx  Accrual Liability
    CR 780000  Provision Release (Income)
```

### EOM GL Mapping (in code)

| Type            | Debit  | Credit |
|-----------------|--------|--------|
| Marketing       | 580150 | 215510 |
| Sales Rep       | 580250 | 215520 |
| Management Fees | 580350 | 215530 |
| Royalties       | 580450 | 215540 |

### Line-Level Fields (Studio)

| Field | Description |
|---|---|
| `x_studio_marketing_accrual_line_item` | Marketing accrual amount |
| `x_studio_royalities_1` | Royalties amount (typo intentional - Studio field) |
| `x_studio_royalties_mngmt_fees_charge` | Management fees amount |
| `x_studio_sales_rep_charge` | Sales rep commission amount |
| `x_studio_accrual_base_snapshot` | Base amount used for computation |
| `x_studio_is_accrued` | Boolean - True once posted to GL |

### EOM Posting Logic (`action_run_eom_accruals`)

1. Search all invoice lines where `x_studio_is_accrued = False` and invoice is posted
2. Group accrual amounts by type and analytic account
3. Create one journal entry with debit/credit pairs
4. Post the journal entry
5. Mark all processed lines as `x_studio_is_accrued = True`

### Consignment Exception

Products in category `"Product in Consignment"`:
- **No royalties** (set to 0)
- **No management fees** (set to 0)
- Marketing and sales rep still apply if conditions met

---

## 7. Margin Recompute Button

### Purpose

Approximate margin stored directly on the invoice document. Informational
only - does not create journal entries. Can be changed after the invoice is
posted. Gives the sales/finance team a quick profitability view per invoice.

### Button Flow: `action_recompute_management_margin()`

```
1. _kebony_apply_accrual_vals(force=True)
   |-- For each invoice line: compute and write accrual fields

2. _recompute_total_accruals_from_lines()
   |-- Sum: marketing + royalties + mgmt fees + sales rep -> write header total

3. _compute_management_cogs_amount()
   |-- Per line, in priority order:
      a) Consignment -> stock.consignment.price table
      b) Dropship -> vendor bill allocation (pro-rata by PO qty)
      c) Stock -> lot cost (wood) or standard_price (accessories)

4. Compute margin = net_sales - cogs - accruals - freight - warehousing - other_adj

5. Write to header: x_studio_cogs, x_studio_margin, x_studio_margin_in_pourcentage, x_studio_credit_note
```

### COGS Sources (3 paths)

**Path 1: Consignment**
- Product category = `"Product in Consignment"`
- Cost from `stock.consignment.price` (active, matching product_id)
- Unit price x qty in product UoM

**Path 2: Dropship**
- Detected via `sale_line_ids.purchase_line_ids` (auto-generated PO lines)
- Cost from **posted vendor bills** linked to the PO line
- Total bill `amount_untaxed` (includes freight/services) allocated pro-rata by PO qty
- Currency conversion if vendor bill in different currency

**Path 3: Stock (default)**
- From done stock moves linked via `sale_line_ids.move_ids.move_line_ids`
- **Lot-tracked products (wood):** `lot.x_studio_unit_cost` (or `x_studio_cost` or `cost`) x `move_line.quantity`
- **Non-lot products (accessories):** fallback to `product.standard_price` x qty in product UoM
- Lot cost field priority: `x_studio_unit_cost` > `x_studio_cost` > `cost` > `product.standard_price`

### Credit Notes & Down Payments

**Credit notes**: Automatically detected — posted `out_refund` where
`reversed_entry_id = invoice.id`. Deducted from gross sales.

**Down payments**: Detected by tracing back to the SO and finding
sibling invoices flagged `x_is_prepayment = True`. The method
`_compute_down_payment_amount()` sums `amount_untaxed` of all posted
prepayment invoices linked to the same sale order.

The combined value is stored in `x_studio_credit_note` (label:
**"Credit Note / Pre-payment"**):
- Positive value = down payment revenue restored
- Negative value = credit note reducing revenue

**Prepayment skip**: Invoices with `x_is_prepayment = True` are
skipped entirely by the margin button — no COGS, no accruals, no
margin computed.

### Header Fields Written

| Field | Description |
|---|---|
| `x_studio_cogs` | Total COGS |
| `x_studio_total_accruals_cost` | Total accruals (sum from lines) |
| `x_studio_freight_cost` | Freight (user input, not overwritten) |
| `x_studio_warehousing_cost` | Warehousing (user input, not overwritten) |
| `x_studio_other_adjustment` | Other adjustments (user input, not overwritten) |
| `x_studio_margin` | Calculated margin |
| `x_studio_margin_in_pourcentage` | Margin % |
| `x_studio_credit_note` | Credit Note / Pre-payment (combined: DP − CN) |

### Known Constraints

- Margin is an **approximation** - it depends on available cost data at compute time
- Dropship COGS requires vendor bills to be posted; if pending, COGS = 0 for those lines
- Stock COGS depends on lot cost being populated; if missing, falls back to standard price
- The button can be clicked multiple times - it overwrites previous values

---

## 8. Journal Entry Map

| Transaction               | Debit          | Credit         |
|---------------------------|----------------|----------------|
| Goods Receipt             | 110200 FIFO    | 211100 GRNI    |
| Supplier Invoice          | 211100 GRNI    | 211000 AP      |
| Landed Cost Vendor Bill   | 110410 LC Clr  | 211000 AP      |
| Landed Cost Allocation    | 110200 FIFO    | 110410 LC Clr  |
| Sales Invoice             | 121000 AR      | 400000 Revenue + 253000 Tax |
| Delivery / COGS           | 500000 COGS    | 110200 FIFO    |
| Accrual at Sale           | 58xxxx Exp     | 2155xx Liab    |
| Accrual Utilisation       | 2155xx Liab    | 211000 AP      |
| Over-accrual Release      | 2155xx Liab    | 780000 Release |

---

## 9. Inventory Adjustments

| Adjustment         | Debit                      | Credit       |
|--------------------|----------------------------|--------------|
| NRV Adjustment     | 110105 NRV Adjustment      | 110200 FIFO  |
| Downgrade / Quality| 110104 Lumber Downgrade    | 110200 FIFO  |
| Slow-moving Allow. | 110103 Slow-moving Deprec. | 110200 FIFO  |

---

## 10. Accounts Payable & GRNI Flow

GRNI (Bills to Receive) ensures accurate cutoff when deliveries occur
before invoices.

**Month 1 (goods delivered, no invoice yet):**
```
DR 110200  Inventory
    CR 211100  GRNI
```

**Month 2 (invoice arrives):**
```
DR 211100  GRNI
    CR 211000  AP
```

This ensures inventory is correct, AP is correct, and there is no timing
distortion.

---

## 11. Odoo Configuration Blueprint

### Product Category

| Setting              | Value                |
|----------------------|----------------------|
| Cost Method          | FIFO                 |
| Inventory Valuation  | Automated            |
| Stock Input Account  | 211100 GRNI          |
| Stock Output Account | 500000 COGS          |
| Valuation Account    | 110200 FIFO Valuation|

### Landed Cost Product

| Setting        | Value            |
|----------------|------------------|
| Product Type   | Service          |
| Is Landed Cost | Yes              |
| Expense Account| 110410 LC Clearing|

### Stock Journal

| Setting | Value                          |
|---------|--------------------------------|
| Debit   | 110200 Inventory               |
| Credit  | 211100 GRNI or 500000 COGS     |

---

## 12. Month-End Close Procedures

### Inventory
- Validate all receipts have invoices
- Validate landed cost clearing is zero
- Review NRV, downgrade, and slow-moving accounts
- Ensure LIFO reserve (if unused) is unchanged

### Accruals
- Reconcile each 2155xx liability
- Apply actual invoices
- Release over-accruals
- Book additional accruals if needed

### COGS
- Review negative stock
- Validate FIFO cost layers integrity

### AP
- GRNI review (old receipts without invoices)

### AR
- Review unapplied payments and credit notes

---

## 13. Future: CM-Level Margin (Not Yet Implemented)

The real Kebony margin definition is by **Contribution Margin levels**.
Full design: **[[Analytical Accounting Architecture]]**

Summary:

1. Add **4 analytical plans** in Odoo:
   - **Country** → margin by geography (75 values for Europe, USA + CAN for INC)
   - **BU** (Business Unit / cost centre) → P&L by department (9 shared values)
   - **Sales Area** → US/Canada sub-regional detail (9 regions, INC only)
   - **CM Level** → contribution margin tier in the P&L waterfall (GM I → GM II → EBITDA → EBIT → Net Income)

2. **Auto-post analytics** at transaction time: Country from customer address, Sales Area from contact field (US), BU from sales team, CM Level from GL account / BoM decomposition

3. **BoM-based COGS decomposition** (preferred): split COGS into direct (COGS-D → GM I) and indirect (COGS-I → GM II) using the product's BoM cost structure

4. **EOM allocation**: unabsorbed production overhead (BNV), country distribution of costs tagged COM, CM-level tagging on accrual JE lines (US)

5. CM Level applies to **both** BNV and INC — enables group-level consolidated P&L

---

## Appendix A - Flow Diagrams

### FIFO Flow
```
Goods Receipt              Vendor Invoice           Delivery (COGS)
  DR 110200                  DR 211100                DR 500000
  CR 211100                  CR 211000                CR 110200
      |                          |                        |
      +-------------------------+------------------------+
```

### Landed Cost Flow
```
LC Vendor Bill             LC Allocation
  DR 110410                  DR 110200
  CR 211000                  CR 110410
      |                          |
      +--------------------------+
```

### Sales Accrual Flow
```
Accrual at Sale            Vendor Invoice Arrives
  DR 58xxxx                  DR 2155xx
  CR 2155xx                  CR 211000
      |                          |
      |                   +------+------+
      |                   |             |
      |            Actual > Accrual  Actual < Accrual
      |              DR 58xxxx        CR 780000
      +------------------------------------------
```

---

## Appendix B - Odoo Module Reference

| Feature                    | File(s)                        | US-only? |
|----------------------------|--------------------------------|----------|
| Margin recompute button    | `account_move.py`              | Yes      |
| Prepayment flag & cross-links | `account_move_prepayment.py` | Yes      |
| Accrual engine             | `account_move_line.py`         | Yes      |
| EOM accrual journal entry  | `kebony_accounting_hub.py`     | Yes      |
| Biewer PO generation       | `account_move_biewer_po.py`    | Yes      |
| US reports (BOL, Quote...) | `report/*.xml`                 | Yes      |
| Consignment pricing        | `stock_consignment_price.py`   | Yes      |
| Wood metrics layer         | `kebony_metrics_layer.py`      | No       |
| Pack reservation           | `stock_lot.py`, `sale_order.py`| No       |
| Logistics date             | `stock_picking.py`             | No       |
