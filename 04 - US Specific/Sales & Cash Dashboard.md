# Sales & Cash Dashboard — Blueprint

> **Module**: `kebony_bol_report` | **Model**: `report.kebony.sales.dashboard`
> **Status**: Active — iterating | **Owner**: Olivier

---

## Purpose

Two complementary views on the same underlying data, answering two distinct business questions:

| View | Question | Rows grouped by |
|------|----------|-----------------|
| **Sales Pipeline** | How much have we sold vs. how much is still to invoice? | Sales Area, Customer, Month |
| **Cash Pipeline** | How much cash has come in vs. how much is still outstanding? | Sales Area, Customer, Month |

---

## Sales Pipeline

### Metric: Invoiced

**Definition**: Revenue that has been **formally invoiced** to the customer via a final (non-prepayment) invoice.

**Business rules**:
- A SO is considered "invoiced" when at least one **non-prepayment, posted** `out_invoice` exists linked to it
- Once the final invoice exists, **all** related documents contribute to the Invoiced amount:
  - Prepayment invoices (carry the amount when final invoice nets to zero)
  - Final invoice (carries the volume when amount is zero after prepayment deduction)
  - Credit notes (reduce invoiced revenue)
- Prepayment-only SOs (no final invoice yet) are **excluded** from Invoiced — they appear in "To Invoice"

**Measures**:
| Measure | Source | Notes |
|---------|--------|-------|
| Amount | `account_move.amount_untaxed_signed` | Signed: invoices positive, credit notes negative |
| Volume (m3) | `account_move.x_kebony_total_volume_m3` | Credit notes: volume negated |

**Why this design**: A prepayment is a **cash event**, not an invoicing event. The sales team considers a SO "invoiced" only when the actual invoice (with delivery reference, volumes, line items) has been issued. The prepayment amount is correctly shown in the Cash Pipeline.

### Metric: To Invoice

**Definition**: Confirmed sales orders where **no final invoice** has been issued yet.

**Business rules**:
- SO must be in state `sale` (confirmed)
- No posted, non-prepayment `out_invoice` linked to the SO via `sale_order_line_invoice_rel`
- Prepayments do NOT exclude the SO from "To Invoice" — they are cash events
- Draft invoices do NOT count as invoicing
- The full SO amount and volume are shown (not a remaining delta)

**Measures**:
| Measure | Source | Notes |
|---------|--------|-------|
| Amount | `sale_order.amount_untaxed` | Full SO amount |
| Volume (m3) | `sale_order.x_kebony_total_volume_m3` | Full SO volume |

**Why full amount, not remaining**: Since we use existence-based logic (final invoice exists or not), partial invoicing is binary. If a final invoice exists, the SO moves to Invoiced entirely. If not, the full amount stays in To Invoice.

---

## Cash Pipeline

### Metric: Paid

**Definition**: Cash already received on posted invoices (including prepayments).

**Business rules**:
- All posted customer invoices and credit notes (`out_invoice`, `out_refund`)
- Amount = `amount_untaxed_signed - amount_residual_signed` (what has been paid)
- Includes prepayment invoices (prepayments ARE cash events)
- Threshold: only shown when paid amount > 0.01

**Measures**:
| Measure | Source | Notes |
|---------|--------|-------|
| Amount | `amount_untaxed_signed - amount_residual_signed` | What the customer has paid |
| Volume (m3) | `account_move.x_kebony_total_volume_m3` | From the invoice |

### Metric: To Cash In

**Definition**: Outstanding balance on posted invoices.

**Business rules**:
- All posted customer invoices and credit notes
- Amount = `amount_residual_signed` (what is still owed)
- Includes prepayment invoices with open balance
- Threshold: only shown when `|amount_residual| > 0.01`

**Measures**:
| Measure | Source | Notes |
|---------|--------|-------|
| Amount | `amount_residual_signed` | Outstanding balance |
| Volume (m3) | 0 | Not applicable for cash position |

---

## Dimensions (shared across all metrics)

| Dimension | Source | Notes |
|-----------|--------|-------|
| Month | Invoice date (Parts 1,3,4) or SO commitment/order date (Part 2) | Truncated to first of month |
| View Type | `sales` or `cash` | Allows filtering in pivot |
| Metric Type | `invoiced`, `to_invoice`, `paid`, `to_cash_in` | Column grouping in pivot |
| Sales Area | `res.partner.x_studio_area_of_sales` (Studio M2O) | Joined via display name |
| Country | `res.partner.country_id` | From commercial partner |
| Customer | `res.partner` | `am.partner_id` or `so.partner_id` |
| Sales Rep | `res.partner.x_studio_sales_representative` (Studio M2O) | From commercial partner |
| Reference | Invoice name or SO name | For drill-down |
| Company | From invoice or SO | Multi-company support |

---

## Prepayment Handling — Summary

Prepayments in Odoo create a complex document chain. Here is how each document type flows through the dashboard:

| Document | Example | Sales Pipeline | Cash Pipeline |
|----------|---------|----------------|---------------|
| Prepayment invoice | INV/00013 (x_is_prepayment=True) | **Invoiced** (only if final invoice exists for same SO) | **Paid** / **To Cash In** |
| Final invoice (post-prepayment) | INV/00033 (amount=0, has volume) | **Invoiced** (triggers SO inclusion, carries volume) | N/A (amount=0, below threshold) |
| Credit note on prepayment | RINV/00002 | **Invoiced** (negative amount) | **Paid** (negative) |
| SO with prepayment only | S00069 | **To Invoice** (full SO amount) | Prepayment in Paid/To Cash In |

### Key principle
> **Prepayment = cash event, not invoicing event.**
> A SO stays in "To Invoice" until the final invoice is posted, regardless of prepayment status.

---

## Known Edge Cases

### 1. Odoo `invoice_status` unreliable
Odoo's native `sale.order.invoice_status` field gets stuck on `'to invoice'` or `'no'` when prepayments exist. **We do NOT rely on this field.** All logic is based on document existence and amounts.

### 2. Zero-amount final invoices
After a 100% prepayment, the final invoice has `amount_untaxed_signed = 0`. This is normal — the prepayment carries the amount, the final invoice carries the volume. Both are included in Invoiced.

### 3. Credit notes cancelling prepayments
A credit note reversing a prepayment does not carry `x_is_prepayment = True`. It shows as a regular credit note in Invoiced (negative amount). This is correct accounting — the revenue reduction is real.

### 4. Partial invoicing
Current logic is binary: a SO is either fully in "To Invoice" or fully in "Invoiced" based on the existence of a final invoice. Partial invoicing (some SO lines invoiced, some not) is not supported — this matches Kebony's business process where SOs are invoiced in full.

---

## SQL View Structure

```
PART 1: INVOICED     — posted invoices for SOs with a final invoice
PART 2: TO INVOICE   — confirmed SOs without a final invoice
PART 3: TO CASH IN   — posted invoices with open balance
PART 4: PAID         — cash received on posted invoices
```

ID ranges to avoid collision in the UNION:
- Part 1: `am.id` (invoice IDs, typically < 100M)
- Part 2: `so.id + 100,000,000`
- Part 3: `am.id + 200,000,000`
- Part 4: `am.id + 300,000,000`

---

## Revision History

| Date | Change | Reason |
|------|--------|--------|
| 2026-03-26 | Initial blueprint (retroactive) | Document requirements after iterative fixes |
| 2026-03-26 | Redefine invoiced vs to-invoice around final invoice existence | Prepayment-only SOs incorrectly shown as invoiced |
| 2026-03-26 | Include all invoice types in Part 1 when final exists | Volume missing from prepayment invoices, amount missing from final invoices |
| 2026-03-26 | Remove reliance on `so.invoice_status` | Field unreliable with prepayments |
| 2026-03-26 | Use gross invoiced for coverage, net for display | Credit notes shouldn't trigger re-invoicing |
