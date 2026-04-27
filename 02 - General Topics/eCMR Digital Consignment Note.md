# eCMR — Digital Consignment Note (EU road freight)

**Status:** Scoping only — not on the Phase-1 go-live critical path
**Regulatory deadline:** **1 July 2027** (EU-wide mandatory, eFTI regulation)
**Owner:** Olivier Eberhard / VVF Consulting
**Date:** 2026-04-24

---

## 1. What it is

**eCMR** = electronic version of the **CMR consignment note** (Convention relative au contrat de transport international de Marchandises par Route, Geneva 1956). The paper waybill drivers carry today becomes a digital document accessible via a certified platform's mobile app.

Governed by the **eFTI Regulation (EU) 2020/1056** — Electronic Freight Transport Information. From **1 July 2027** all national authorities in the EU must accept eFTI-compliant digital transport documents.

## 2. Kebony exposure — which shipments are CMR

| Route | CMR? | Notes |
|---|---|---|
| **BNV (Belgium) → EU customers** | ✅ Yes | International road freight inside EU |
| **Norway (NAS) → Belgium (BNV)** | ✅ Yes | EEA road transport — Norway has ratified eCMR protocol |
| **RDK subcontract pickups (domestic BE)** | Maybe | Domestic CMR is optional; national law applies |
| **BE → Tabaknatie (TBK) (3PL)** | ✅ Yes (still CMR scope if cross-border) | Cross-border if TBK across the border |
| **BE / US → US customers** | ❌ No | Sea freight — different regime (Bill of Lading) |
| **US (INC) domestic road** | ❌ No | US regulation, not CMR |
| **Intercompany BNV ↔ NAS** | ✅ Yes | Standard CMR shipment |

Majority of Kebony freight is CMR-in-scope. Non-trivial preparation needed.

## 3. Regulatory timeline (per industry publications, 2026)

- **2017** — Additional Protocol to CMR Convention on eCMR signed.
- **2023** — 33+ countries ratified, including FR, DE, NL, LU, NO, FI, SE, DK, CH.
- **2024** — Belgium completed Benelux+FR pilot but **not yet ratified** formally.
- **2026** — **Industry turning point** (expected). Major carriers and 3PLs push eCMR adoption ahead of the 2027 deadline. Customers start to demand it.
- **1 July 2027** — **eFTI mandate**: all EU authorities must accept digital transport documents.
- **2029** — Industry expects full adoption.

## 4. What's in the CMR document (data model reference)

Standard CMR fields (per 1956 Convention):
- Sender (name, address)
- Consignee (name, address)
- Place of taking over goods (place + date)
- Place designated for delivery
- Carrier (name, address)
- Successive carriers (if applicable)
- Vehicle(s) — registration plates
- Driver — name + signature
- Goods description — marks & numbers, number of packages, type of packaging
- Gross weight
- Volume (for some goods)
- Dangerous goods (ADR classification)
- Carriage charges (freight cost)
- Instructions for customs / formalities
- Reservations (damage at pickup / delivery)
- Signatures — sender, carrier, consignee at delivery

eFTI adds machine-readable structured equivalents + event/status codes.

## 5. Odoo preparation — what exists + what's missing

| Data point | Odoo source (today) | Gap |
|---|---|---|
| Sender | `res.company` → Kebony BNV | ✓ |
| Consignee | `stock.picking.partner_id` | ✓ |
| Place of taking over | `stock.picking.location_id` + address | Need address translation |
| Place of delivery | `stock.picking.partner_shipping_id` | ✓ |
| Carrier | `stock.picking.carrier_id` | ✓ (standard Odoo) |
| Vehicle plate | — | **Missing** — need field on picking or `fleet.vehicle` ref |
| Driver | — | **Missing** — need name + ID |
| Goods description | `stock.move.product_id + description` | ✓ |
| Marks & numbers | `stock.lot.name` (our FA-xxxxx pack labels) | ✓ (will be very clean once product master cleanup lands) |
| Packages count | `stock.move.quantity / product.packaging.qty` | ✓ |
| Gross weight | `stock.move.product_id.weight × qty` | ✓ |
| ADR (dangerous goods) | — | Not applicable to wood products (unless chemicals move separately) |
| Carriage charges | Not in picking; in SO / `delivery.carrier` | Needs link |
| Customs instructions | — | **Missing** — custom field |
| Signatures | Photo on delivery (Gate 7 in Quality Gates) | Digital sig comes from eCMR platform app, not Odoo |

**Net:** ~80% of the data is already there. Gaps are vehicle plate, driver, customs fields, and digital signature collection — all doable with light Odoo extensions.

## 6. Architecture — Odoo + certified eCMR platform

Odoo is **not** an eCMR provider — it needs to integrate with a certified platform.

### 6.1 Certified platform candidates

| Platform | Notes |
|---|---|
| **TransFollow** | Market leader, ~90 % of European eCMR traffic, driver app, carrier-portal, accepted in BE/NL/FR/LU/NO/DE/… |
| **Transporeon** | Large TMS; eCMR is a module within their platform |
| **TESISQUARE eCMR** | Italian origin; good API |
| **DORA TMS** | Newer, cheaper entry point |
| **CargoON** | Growing, focused on carrier adoption |
| **Direct eFTI** | Skip TMS — connect to national competent authority via eFTI message format. More effort, more control. Probably **not** the right approach for Kebony (shipper, not a platform). |

Recommended path for Kebony: **pick one platform (likely TransFollow given BE market share) + build an Odoo connector**.

### 6.2 Integration pattern

```
Odoo delivery picking  ──[REST API]──►  eCMR platform  ──[driver app]──►  Driver / Consignee
         ▲                                    │
         │                                    │ (status + signatures)
         └──[webhook / polling]───────────────┘
```

- **Outbound**: when picking is validated, push CMR data to platform → get eCMR ID back
- **Inbound**: platform pushes status updates (picked-up, in-transit, delivered, signed) → Odoo updates picking + triggers invoice / Gate 7 completion
- **Attachment**: PDF of the eCMR stored on the picking as `ir.attachment`

### 6.3 Odoo module shape — `kebony_ecmr` (new, ~6–10 days build)

| Artefact | Purpose |
|---|---|
| `ir.config_parameter` | Platform URL + API key (one per env) |
| Fields on `stock.picking` | `x_ecmr_id`, `x_ecmr_status`, `x_driver_name`, `x_vehicle_plate` |
| Model `kebony.ecmr.event` | Audit trail of platform events on each picking |
| Button "Send to eCMR" | Manual trigger on picking form |
| Automation | Auto-send on picking validation (configurable) |
| Webhook controller | `/api/ecmr/webhook` — receive status updates |

## 7. Decision points before building

1. **Carrier buy-in** — Kebony isn't the carrier. The carrier's truck + driver use the eCMR app. If our carriers already use TransFollow (or any specific platform), pick that one.
2. **Which subset first** — BE → EU customers is the biggest volume. Start there. Intercompany BE ↔ NO can follow.
3. **Sender OR carrier driving adoption?** — Carriers usually drive (they avoid paper). We can support whatever platform they use, or have our own preferred one for status visibility.

## 8. Proposed timeline (aligned with EU 2027 mandate)

| Period | Action |
|---|---|
| **2026 Q3** | Scope: pick platform (ideally aligned with Kebony's main carriers) · cost estimate · pilot candidate shipment |
| **2026 Q4** | Build `kebony_ecmr` connector + Odoo field extensions · pilot on 1–2 carriers |
| **2027 Q1** | Scale to all EU carriers · train dispatch team |
| **2027 Q2** | Rollout to NAS → BNV intercompany · soft-launch before 1 Jul |
| **2027 Q3** | Mandate live — fully running on eCMR |

## 9. Open questions

- Which eCMR platform(s) are Kebony's current carriers using? (Survey needed.)
- Is there a budget / stream within BE digital-freight grants for 2026–2027 adoption?
- How does this intersect with **EUDR due-diligence statements** (wood-specific deforestation-free origin) — which must travel *with* the goods from 30 Dec 2026? → worth a separate note [[EUDR Due Diligence]].

## 10. References

- [eCMR in 2026 — Hauliers must act before the paper era ends (trans.info)](https://trans.info/en/ecmr-in-2026-434860)
- [Ratification of the eCMR protocol in Europe 2023 (TransFollow)](https://www.transfollow.org/ratification-ecmr-protocol-eu/)
- [eCMR: Meaning and Benefits for Shippers (Transporeon)](https://www.transporeon.com/en/community/blog/ecmr-guide-for-shippers)
- [eCMR Protocol (trucknet.io)](https://trucknet.io/ecmr-protocol/)
- [e-CMR Guide (DORA TMS)](https://doratms.com/en/knowledge/ecmr-digital-consignment-note/)

---

## Document history

| Date | Change |
|---|---|
| 2026-04-24 | Initial scoping doc — eCMR vs eFTI, Kebony shipment exposure, Odoo data gaps, `kebony_ecmr` connector module shape, 2026-Q3 → 2027-Q2 timeline. Not on Phase-1 go-live path but 2027 mandate is real. |
