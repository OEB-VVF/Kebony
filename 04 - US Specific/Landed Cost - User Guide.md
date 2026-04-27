# Landed Cost Automation — User Guide

> **Module:** kebony_bol_report v1.6.0+
> **Scope:** US entity (Kebony Inc.) only
> **Date:** 8 April 2026

---

## Overview

When Kebony buys wood from overseas, there are two costs:
1. **The goods** — the wood itself (Goods PO)
2. **The freight / customs / handling** — getting it here (Cost PO)

US GAAP requires freight to be **capitalized into inventory value**, not expensed. This module automates the process.

---

## Terminology

| Term | Meaning |
|------|---------|
| **Goods PO** | The purchase order for the physical product (wood, accessories) |
| **Cost PO** | A separate PO for freight, customs, or handling services — linked to a Goods PO |
| **Landed Cost** | An Odoo record that allocates additional costs to a receipt, enriching the FIFO inventory valuation |
| **Estimated LC** | Auto-created when goods are received but the freight bill hasn't arrived yet |
| **Actual LC** | Replaces the estimated LC when the real vendor bill is posted |
| **Accrual JE** | Journal entry booking the estimated cost: DR Clearing / CR GRNI |

---

## Configuration (one-time setup)

Go to **Settings → Companies → Kebony Inc. → Landed Cost Automation** tab:

| Setting | Account | Purpose |
|---------|---------|---------|
| Landed Cost Clearing Account | 110410 | Temporary account between receipt and bill |
| GRNI Accrual Account | 211000 | Goods Received Not Invoiced (liability) |
| LC Accrual Journal | Miscellaneous Operations | Journal for accrual entries |

---

## Step-by-Step Flow

### Step 1: Create the Goods PO

1. Go to **Purchase → Orders → New**
2. Select the vendor (e.g. Biewer Lumber)
3. Add product lines (e.g. 1931-I-10, 500 LF @ $6.00)
4. **Confirm** the order

### Step 2: Create the Cost PO (linked to Goods PO)

1. Go to **Purchase → Orders → New**
2. Select the freight vendor (e.g. DESERT MOUNTAIN TRANSPORT)
3. **Set the "Goods PO" field** → select the Goods PO from Step 1
   - This links the two POs together
   - A banner appears: "This is a Cost PO linked to [Goods PO]"
4. Add service lines (e.g. Import Freight, 1 unit @ $1,500)
   - **Only service products** are allowed on Cost POs
5. **Confirm** the order

### Step 3: Receive the Goods

1. Go to the **Goods PO** → click **Receive Products**
2. Set the quantities → **Validate** the receipt

**What happens automatically:**
- System detects this Goods PO has a linked Cost PO (from Step 2)
- No vendor bill exists yet for the Cost PO
- Creates an **Estimated Landed Cost** with cost lines ($1,500)
- Creates and posts an **Accrual Journal Entry**:
  ```
  DR 110410 Landed Cost Clearing    $1,500
      CR 211000 GRNI Accrual        $1,500
  ```
- The estimated LC is validated → $1,500 added to inventory valuation
- The Goods PO shows a "Landed Costs" smart button (count = 1)

### Step 4: Freight Bill Arrives

1. Go to the **Cost PO** → click **Create Bill**
2. Verify the amounts (may differ from the estimate)
3. **Post** the vendor bill

**What happens automatically:**
- System finds the estimated LC linked to this Cost PO
- **Cancels** the estimated LC
- **Reverses** the accrual JE (creates a reversal entry)
- Creates a **new Actual LC** from the real bill amounts
- **Validates** the actual LC → inventory valuation adjusted to actual cost
- Posts a message on the Goods PO showing: estimated → actual, delta

---

## Monitoring

### Accounting Hub

Go to **Accounting → Kebony Hub → End of Month**:

| Button | What it shows |
|--------|--------------|
| **Pending Landed Cost Accruals** | All estimated LCs not yet settled (waiting for vendor bills) |

### Goods PO Smart Button

On any Goods PO, the **Landed Costs** smart button shows all LCs (estimated + actual) linked to it.

### Cost PO Banner

Any Cost PO shows a banner indicating it's linked to a Goods PO.

---

## Edge Cases

### Partial Receipt
If only part of the Goods PO is received, the LC amount is **proportionally allocated**:
- Receipt value / Total PO value = ratio
- LC amount = Cost PO amount × ratio

### Bill Arrives Before Receipt
If the vendor bill is posted on the Cost PO before the goods are received:
- At receipt validation, the system detects the bill already exists
- Creates an **actual** LC directly (no estimate, no accrual)

### Multiple Cost POs on One Goods PO
Supported — each Cost PO creates its own LC. All visible via the Goods PO's smart button.

### Currency Conversion
If the Cost PO is in a different currency than the company, amounts are converted at the receipt date rate.

---

## GL Account Flow

```
Step 1 — Estimated LC (receipt, no bill yet):
    DR 110410  Landed Cost Clearing        $1,500
        CR 211000  GRNI Accrual            $1,500

    LC validates → enriches FIFO layer:
    DR 110200  FIFO Valuation Layer        $1,500
        CR 110410  Landed Cost Clearing    $1,500

Step 2 — Bill arrives ($1,600 actual):
    Reverse accrual:
    DR 211000  GRNI Accrual                $1,500
        CR 110410  Landed Cost Clearing    $1,500

    Cancel estimated LC (reverses FIFO enrichment)

    Post actual LC from bill:
    DR 110200  FIFO Valuation Layer        $1,600
        CR 506000  Landed Cost Expense     $1,600

    Standard AP entry:
    DR 506000  Landed Cost Expense         $1,600
        CR 211000  Accounts Payable        $1,600
```

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| No LC created on receipt | Cost PO not linked (goods_po_id empty) | Edit Cost PO, set the Goods PO field |
| LC created but empty (0 amount) | Missing expense account on freight product | Set expense account on product or product category |
| Accrual JE not posted | Missing GL config on company | Check Settings → Kebony Inc → Landed Cost tab |
| "Only service products" error | Non-service product on Cost PO | Remove non-service lines, use service products only |
