# Kebony Entity Registry

> Legal entity details for all Kebony group companies.
> **Pending:** Ask finance/legal team to complete address, VAT, and registration fields.

---

## INC — Kebony Inc.

| Field | Value |
|---|---|
| **Legal name** | Kebony Inc. |
| **Short name** | INC |
| **Country** | USA |
| **Type** | Operating |
| **Currency** | USD |
| **Address** | *pending* |
| **Tax ID (EIN)** | *pending* |
| **State of incorporation** | *pending* |
| **Odoo code** | `x_kebony_entity_type = "inc"` |

**Role:** US sales entity. Sells to US customers directly and via consignment (Biewer Lumber, LLC). All US-specific features (accruals, margin calculation, US reports) are scoped to this entity.

---

## Holding — Kebony Holding

| Field | Value |
|---|---|
| **Legal name** | Kebony Holding |
| **Short name** | Holding |
| **Country** | Belgium |
| **Type** | Holding |
| **Currency** | EUR |
| **Address** | *pending* |
| **VAT** | *pending* |
| **Company number (BCE/KBO)** | *pending* |
| **Odoo code** | `x_kebony_entity_type = "holding"` |

**Role:** Belgian holding company. Group-level entity.

---

## BNV — Kebony BNV

| Field | Value |
|---|---|
| **Legal name** | Kebony BNV |
| **Short name** | BNV |
| **Country** | Belgium |
| **Type** | Operating |
| **Currency** | EUR |
| **Address** | *pending* |
| **VAT** | *pending* |
| **Company number (BCE/KBO)** | *pending* |
| **Odoo code** | `x_kebony_entity_type = "bnv"` |

**Role:** Belgian operating company. Manufacturing site at Kallo. European sales. Intercompany supplier to INC. All manufacturing features (DL, AC, PP, planning families) are scoped to this entity.

---

## KAS — Kebony KAS

| Field | Value |
|---|---|
| **Legal name** | Kebony KAS |
| **Short name** | KAS |
| **Country** | Norway |
| **Type** | Holding |
| **Currency** | NOK |
| **Address** | *pending* |
| **Org.nr** | *pending* |
| **Odoo code** | `x_kebony_entity_type = "kas"` |

**Role:** Norwegian holding company. **Being dissolved in coming months.** Minimal Odoo configuration expected.

---

## NAS — Kebony Norge AS

| Field | Value |
|---|---|
| **Legal name** | Kebony Norge AS |
| **Short name** | NAS |
| **Country** | Norway |
| **Type** | Operating |
| **Currency** | NOK |
| **Address** | *pending* |
| **Org.nr** | *pending* |
| **Odoo code** | `x_kebony_entity_type = "nas"` |

**Role:** Norwegian operating company. Limited transactions going forward.

---

## Intercompany Relationships

```
         Holding (BE)
         /         \
       BNV (BE)    KAS (NO) → being dissolved
       |               |
    [Kallo plant]   NAS (NO) → limited
       |
       └──→ INC (US) [intercompany sales]
```

- **BNV → INC**: Intercompany supply chain. BNV manufactures, INC sells in the US market.
- **Intercompany transaction model**: *To be defined.*

---

*This document should be completed by the finance/legal team with all registration details.*
