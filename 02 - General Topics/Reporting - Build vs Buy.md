	# Reporting Architecture — Build in Odoo vs. Buy Fabric

> **Status:** Working paper — for SteerCo discussion
> **Date:** 8 April 2026
> **Author:** Olivier Eberhard (VVF)

---

## The Question

The reporting strategy proposes Microsoft Fabric (Data Factory + Lakehouse + Power BI) as the BI layer — 7 source systems, Bronze/Silver/Gold medallion architecture, Copilot AI.

The budget module proposes an Odoo-native CEO dashboard built with Odoo Spreadsheet + PIVOT views.

**If budget entry AND actuals both live in Odoo, what does Fabric add — and is it worth the cost?**

---

## What Odoo Already Covers (Today)

| Domain | Data Source | Odoo Model | Status |
|--------|-----------|------------|--------|
| Revenue (invoiced) | `account.move` (posted) | Live | ✅ |
| Revenue by country/area | `account.move` + partner | Live | ✅ |
| Volume (m³, LF, boards) | `x_kebony_total_volume_m3` on invoice | Live | ✅ |
| COGS | `x_studio_cogs` on invoice | Live | ✅ |
| GM1 / GM1% | Revenue − COGS (computed) | Live | ✅ |
| Expenses by GL | `account.move.line` by account | Live | ✅ |
| EBITDA | GL mapping → waterfall | Needs GL map | ✅ |
| Cash flow (indirect) | Balance sheet deltas | Needs opening bal | ✅ |
| Production output (m³) | `mrp.production` completed MOs | Live | ✅ |
| Dryer loads | `kebony.dryer.load` | Live | ✅ |
| Inventory by location | `stock.quant` | Live | ✅ |
| Inventory valuation | FIFO layers (`stock.valuation.layer`) | Live | ✅ |
| DOS (days of stock) | Quant qty / trailing consumption | Computable | ✅ |
| AR aging / DSO | `account.move` receivables | Live | ✅ |
| AP aging | `account.move` payables | Live | ✅ |
| OTIF % | `stock.picking` promised vs actual date | Live | ✅ |
| FTE / headcount | HR module or manual | Available | ✅ |
| Order backlog | Confirmed SO, remaining qty | Live | ✅ |
| Top 10 customers | Invoice aggregation | Live | ✅ |

**Coverage: ~95% of the CEO dashboard runs on Odoo data alone.**

---

## What Odoo Cannot Cover (Without Fabric)

| Domain | Source System | Why Odoo Can't | Workaround |
|--------|-------------|----------------|------------|
| OEE (availability, performance, quality) | Prediktor MES | Real-time IoT telemetry, sub-second data | Capture daily aggregates in Odoo via API or manual entry |
| Cycle times, temperatures, pressures | Prediktor MES | Sensor-level data, not ERP scope | Log actual hours on dryer load (already in the model) |
| Scrap events (real-time) | Prediktor MES | Detected by sensors | Enter at exit stacking QC step in Odoo |
| CRM pipeline / opportunities | Salesforce | Separate system, no Odoo CRM yet | Defer until Odoo CRM implemented |
| Customer 360° (contacts, history) | D365 / Dataverse | Legacy CRM | Migrate to Odoo contacts |
| Historical financials (pre-Odoo) | AX2012 | Legacy ERP, frozen | Import opening balances; YoY available from Jan 2027 |
| Product specs / images | Perfion PIM | External catalog | Migrate to Odoo product fields |
| Web traffic / marketing analytics | WordPress | Different domain | Keep separate (Google Analytics) |

---

## MES Data — The Grey Zone

The strongest argument for Fabric is Prediktor integration (OEE, cycle times). But let's examine what we actually need vs. what Prediktor provides:

### What the CEO dashboard needs from MES:

| KPI | Granularity needed | Can Odoo capture it? |
|-----|-------------------|---------------------|
| Dryer hours (actual vs planned) | Per dryer load | ✅ Already in `kebony.dryer.load.actual_duration_hours` |
| Autoclave cycles per day | Daily count | ✅ `kebony.autoclave.batch` with actual dates |
| Scrap % (B-grade + internal) | Per dryer load | ✅ Enter at exit stacking, store on DL |
| OEE (availability) | Per work center per day | ⚠️ Needs a simple daily log model |
| OEE (performance) | Per work center per day | ⚠️ Same — planned vs actual throughput |
| OEE (quality) | Per dryer load | ✅ = 1 − scrap% (already captured) |
| Temperatures / pressures | Per autoclave cycle | ❌ Not ERP scope — but also not on the CEO dashboard |

**Conclusion:** 90% of what the CEO needs from "MES" is already captured or capturable in Odoo's manufacturing module. The remaining 10% (sensor-level data) is not CEO-dashboard material — it's plant-floor monitoring.

### A simple `kebony.daily.production.log` model could capture:
- Date, work center, planned hours, actual hours, planned m³, actual m³
- Computed: availability %, performance %, OEE %
- Entry: by plant operator or shift supervisor (5 min/day)

This replaces the need for a Prediktor → Fabric → Power BI pipeline for executive KPIs.

---

## Cost Comparison

### Option A: Microsoft Fabric Stack

| Item | Annual Cost (est.) | Notes |
|------|-------------------|-------|
| Fabric licence (F64 capacity) | €50–100k | Depends on capacity tier |
| Power BI Pro (15 users) | €15k | €12/user/month |
| Data Factory pipelines | €10–20k | 7 source connectors |
| Purview governance | €10k | Data catalog |
| Implementation (consultants) | €150–300k | One-time, 6–12 months |
| Maintenance / evolution | €30–50k/year | ETL changes, new KPIs |
| **Year 1 total** | **€265–485k** | |
| **Ongoing annual** | **€115–185k** | |

### Option B: Odoo-Native (Custom Module)

| Item | Annual Cost (est.) | Notes |
|------|-------------------|-------|
| Odoo licence | €0 incremental | Already paying for Odoo |
| Budget module development | €15–25k | 4 weeks (one-time) |
| Daily production log model | €3–5k | Simple model + form (one-time) |
| Odoo Spreadsheet dashboards | €5–10k | PIVOT + formatting (one-time) |
| Maintenance / evolution | €5–10k/year | Same developer team |
| **Year 1 total** | **€28–50k** | |
| **Ongoing annual** | **€5–10k** | |

**Delta: €237–435k saved in Year 1. €110–175k/year ongoing.**

---

## What You Give Up (Going Odoo-Only)

1. **Copilot NL queries** — "show me margin by country last quarter" in natural language. Nice but not essential. Odoo has filters + pivots.
2. **Cross-source joins** — Joining Odoo + Salesforce + Prediktor in one query. Only matters if those systems stay separate.
3. **Historical YoY** — AX2012 comparison. Goes away naturally after 12 months of Odoo data.
4. **Sub-second IoT data** — Plant-floor monitoring dashboards. Not CEO scope. Prediktor can keep its own dashboards for operators.
5. **Data lineage (Purview)** — Formal governance audit trail. Odoo has audit log + access rights but not Purview-level lineage.

---

## Recommendation

### Phase 1 (Go-Live, July 2026): Odoo-Only

Build the budget module + CEO dashboard in Odoo. Capture basic MES KPIs via manual daily log or simple API. Covers 95% of needs at 10% of the cost.

### Phase 2 (Q1 2027): Evaluate

After 6 months of live data, assess:
- Is the CEO dashboard sufficient? Any gaps?
- Is daily manual MES entry sustainable or do we need automation?
- Is Salesforce being replaced by Odoo CRM?
- Do we have genuine cross-source analytics needs?

### Phase 3 (If Needed): Targeted Fabric

If cross-source analytics prove necessary, implement a **minimal** Fabric setup:
- Only Odoo + Prediktor (2 sources, not 7)
- Only for OEE dashboards (plant-floor, not CEO)
- Skip Purview, skip Copilot, skip Gold layer
- Estimated cost: €50–80k total vs. €300k+ for full stack

---

## Open Questions for SteerCo

1. **Is Prediktor staying?** If yes, do we need real-time OEE or are daily aggregates sufficient?
2. **Salesforce timeline?** If migrating to Odoo CRM within 12 months, Fabric CRM integration is throwaway work.
3. **AX2012 history** — How important is YoY comparison in the first 6 months? Can we live with "LY = n/a" until Jan 2027?
4. **Who owns the BI budget?** IT or Finance? This affects the build-vs-buy decision framing.
5. **Data governance requirements** — Is Purview-level lineage a compliance requirement or a nice-to-have?
