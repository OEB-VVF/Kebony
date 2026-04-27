# MES ↔ Odoo API Contract

**Shareable spec:** `06 - Slide Decks/mes_api_contract.html` (v1.0, 2026-04-23)
**Source:** [[SIS_MES_Axapta_Summary]] (v0.1 first draft)
**Owner:** Olivier Eberhard / VVF Consulting
**Target audience:** SIS middleware team (Rinaldo + co.)
**Status:** Draft for review — **not** yet implemented

---

## TL;DR

Odoo will expose an HTTP/JSON API (`/api/v1/mes/…`) that an SIS-owned middleware polls + pushes to. Middleware bridges Odoo ↔ SIS `MES_ERP_Mailbox` database. Three flows:

| Flow | Direction | Endpoints |
|---|---|---|
| White wood stock | middleware pulls | `GET /raw-packages` + `GET /inventory-moves` |
| MO instructions | middleware pulls | `GET /production-orders` |
| Production feedback | middleware pushes | `POST /events` + `POST /consumption` + `POST /produced-packages` |

## Key design choices

- **Middleware isolates both sides** — Odoo never touches MES DB; MES never calls Odoo
- **Cursor-based polling** (not streaming) — simple, good enough for Kallo volumes
- **API key auth** in `X-API-Key` header — rotated via Odoo admin UI
- **Idempotency** via MES stable identifiers (`mes_produced_package_ident`, `mes_ref`)
- **Partial success** on batch POSTs — accepted items commit, rejected items returned for retry
- **Ingest queue** (`kebony.mes.ingest.queue`) for dead-letter + replay

## Already built on Odoo side (v1.4.1)

The data model to receive MES events is already in place:
- `kebony.process.pack.event` with `mes_op_code` (10/23/26/30) + `mes_produced_package_ident`
- `kebony.process.pack.mes_quality` (Selection 1/2/3)
- `kebony.equipment` with 1 autoclave + 3 dryer records

The `kebony_mes_api` module (to be built) only adds HTTP controllers on top.

## Open questions for SIS

Listed in the HTML spec §10. Top-3 blockers:
1. **Quality 1 vs 2 meaning** (only Quality=3 scrap is explicit in the SIS doc)
2. **Operator code stability** — do we get a stable key for `res.users` mapping?
3. **Equipment ID on MES events** — does MES report which dryer (1/2/3)?

## Review / sign-off sequence

1. SIS middleware team reviews → flags contract issues
2. Olivier incorporates feedback → v1.1
3. Rinaldo sign-off
4. Kickoff Odoo-side implementation (module `kebony_mes_api`, estimated 3–5 days)

---

## See also

- [[Quality Gates Architecture]] — Gates 3/4 annotated with MES op codes
- [[Terminology Bible]] §5 — MES interface contract reference
- User guide (future): `06 - Slide Decks/mes_api_user_guide.html` — operational doc for ops / IT once implemented

## Document history

| Date | Change |
|---|---|
| 2026-04-23 | v1.0 — Initial draft. 6 endpoints, cursor polling, idempotency, error queue, 8 open questions for SIS. Based on SIS_MES_Axapta_Summary v0.1. |
