# Go-Live Cutover — Supplier Notification Memo

> **Status:** Draft — for review by Joris / Finance before sending
> **Date:** 8 April 2026
> **Effective:** 1 July 2026 (Odoo go-live)

---

## Context

Kebony is migrating from Microsoft AX2012 to Odoo 19. As part of this migration, the purchasing entity for raw materials and services changes:

| | Before (AX) | After (Odoo) |
|---|---|---|
| **Purchasing entity** | Kebony Norge AS (Norway) | Kebony BNV (Belgium) |
| **VAT number** | NO xxx xxx xxx MVA | BE 0xxx.xxx.xxx |
| **Address** | [Norway address] | Ketenislaan 2, 9130 Beveren, Belgium |
| **Delivery address** | Kallo plant (Belgium) — unchanged | Kallo plant (Belgium) — unchanged |
| **Bank details** | [Norway bank] | [Belgium bank — TBD] |

**The physical delivery point (Kallo, Belgium) does not change.** Only the legal buyer and invoicing entity changes.

---

## Supplier Communication Template

```
Subject: Change of purchasing entity — effective 1 July 2026

Dear [Supplier Name],

We are writing to inform you of an administrative change in our
purchasing structure, effective 1 July 2026.

WHAT CHANGES:
- Our purchasing entity changes from Kebony Norge AS (Norway)
  to Kebony BNV (Belgium).
- All new purchase orders from this date will be issued by Kebony BNV.
- Invoices should be addressed to Kebony BNV.

NEW INVOICING DETAILS:
  Company:    Kebony BNV
  VAT:        BE 0xxx.xxx.xxx
  Address:    Ketenislaan 2, 9130 Beveren, Belgium
  Email:      [invoices@kebony.com — TBD]

WHAT DOES NOT CHANGE:
- Delivery address: Kallo plant, Belgium (same as today)
- Your commercial contact at Kebony
- Product specifications, quality requirements
- Payment terms (unless separately renegotiated)

FOR ORDERS ALREADY IN TRANSIT:
- Shipments already dispatched before 1 July may still reference
  Kebony Norge AS on transport documents (Bill of Lading).
- This is acceptable — please issue the commercial invoice to
  Kebony BNV regardless.
- If you have already issued an invoice to Kebony Norge AS for
  goods shipped before 1 July, no change is needed for that invoice.

CUTOFF RULE:
- Invoice date before 1 July → Kebony Norge AS (old entity)
- Invoice date on or after 1 July → Kebony BNV (new entity)

Please acknowledge receipt of this notice and update your records
accordingly. If you have questions, please contact [name] at [email].

Kind regards,
[Name]
Kebony BNV
```

---

## Internal Cutover Checklist

### Before Go-Live (June 2026)

- [ ] Send supplier notification to all active vendors (raw wood, chemicals, freight, services)
- [ ] Confirm new bank details for BNV with each supplier
- [ ] Update vendor master in Odoo with BNV as the purchasing company
- [ ] Verify customs broker has BNV EORI number for import declarations
- [ ] Confirm with tax advisor: interco cleanup for in-transit goods

### At Go-Live (1 July 2026)

- [ ] Transfer open POs from AX (Norway) → Odoo (BNV)
- [ ] Cancel remaining AX POs that won't be fulfilled
- [ ] For each in-transit shipment:
  - If invoice not yet received → supplier invoices to BNV
  - If invoice already received to Norway → Norway does final interco to BNV
- [ ] Last interco transactions posted in AX
- [ ] AX set to read-only

### Post Go-Live (July–August 2026)

- [ ] Monitor incoming invoices — redirect any still addressed to Norway
- [ ] Process last few interco transactions (in-transit tail)
- [ ] Reconcile AX ↔ Odoo opening balances
- [ ] Close Norway purchasing accounts after tail period

---

## BOL Mismatch — Legal Assessment

**Risk:** Shipments in transit at cutover will have BOLs naming Kebony Norge AS as consignee/notify party, but the purchase invoice will be to Kebony BNV.

**Assessment:**
- The BOL is a **transport document**, not a tax or ownership document
- **Customs:** The importer of record on the customs declaration determines tax treatment, not the BOL consignee. BNV can clear customs as importer regardless of BOL naming.
- **VAT:** Determined by the purchase invoice, not the BOL
- **Ownership:** Determined by the commercial contract + Incoterms, not the BOL

**Action needed:** Confirm with customs broker that BNV EORI can be used on import declarations even when BOL references Norway AS. This is standard practice in back-to-back trade structures.

---

## Open Questions

1. **Bank details:** Has BNV communicated new bank details to suppliers?
2. **EORI:** Does BNV have its own EORI number for Belgian customs?
3. **Incoterms:** Do existing contracts need amendment, or just the buyer entity?
4. **Payment terms:** Any suppliers with Norway-specific terms that need renegotiation?
5. **Norway AS wind-down:** When does Norway AS stop being an active purchasing entity in AX?
