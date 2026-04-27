# Product Master Cleanup Plan

**Status:** Plan only — not yet executed.
**Owner:** Olivier Eberhard / VVF Consulting
**Date drafted:** 2026-04-23
**Target environment:** `test` first → `main` / production after sign-off
**Audience:** Kebony team (Product, Planning, Production, IT) + VVF

---

## 1. Purpose

Bring the Odoo product master to a clean, coherent state in one auditable wave. Today's issues:

- Incomplete product records in production Odoo (missing config, missing fields)
- All finished goods currently point to their **Master**, but should point to the **SKU** (profile + length)
- Duplicate / inconsistent Studio fields on `product.template`
- Some masters missing entirely (e.g. code `1003`)
- Planning family not set on every manufacturable
- RDK operations not linked on relevant products
- MES-mandatory field (`x_studio_length_m`) not guaranteed present

## 2. Source files (authoritative)

| File | Location | Purpose | Precedence |
|---|---|---|---|
| `Product Masterdata_FINAL_v7.xlsx` | `/Users/oeb/Documents/` | Master product reference — FG complete, white wood incomplete | **Attributes** (name, UoM, metrics, classification) |
| `RecipeFamily.xlsx` | `/Users/oeb/Documents/` | Recipe family with key-in / key-out in decimals — SKU linkage + yields | **Planning family + yields + parent linkage** |
| `1_RAP MPS.xlsx` | `/Users/oeb/Documents/` | RAP MPS replenishment tool — also carries SKU-to-parent linkage | **SKU ↔ parent resolution** where the master file is silent |
| `product_full_export.json` | vault root | Current Odoo production state (Apr 7 snapshot) | **Baseline for diff** |
| Prior audits (`Manufacturing_Product_Audit.xlsx`, `Missing_Parent_SKUs.xlsx`, `Parent_ID_Plan_v2.xlsx`, `Product_Audit_RAP_Crossref.xlsx`) | vault | Starting point — don't reinvent | Reference only |

**Precedence rule when sources disagree:**
1. `Product Masterdata_FINAL_v7` wins for product attributes (name, UoM, metrics, classification, packaging)
2. `RecipeFamily` wins for `kebony_planning_family_id` and yield coefficients
3. `1_RAP MPS` wins for SKU ↔ parent resolution when the master is silent
4. Odoo production state = baseline — never overwritten blindly; every change is an explicit delta

## 3. Scope

**In scope:**
- `product.template` records across the 3 levels (Master Item, M/I Master, SKU): create missing, complete incomplete
- **Archive length-only Master Variants** (`1127-3.2` style records, ~1 331 rows) → `active=False`, keep history, don't delete
- Re-parent every storable SKU per §4.2 dual semantics:
  - Metric SKU → metric raw consumption parent (from RecipeFamily + decimeter encoding)
  - Imperial SKU → nearest metric FG twin (business-validated)
- `product.category` valuation config (where incomplete)
- `product.packaging` definitions (boards per pack, lm per pack)
- `kebony_planning_family_id` coverage on every manufacturable
- RDK operation mapping (subcontract prices from master file)
- MES-mandatory fields (`x_studio_length_m`)

**Out of scope (this wave):**
- Accrual rates (US) — handled separately
- Vendor pricing / `product.supplierinfo`
- Reordering rules / `stock.warehouse.orderpoint`
- BoM creation — picked up via planning family push, not here
- Tax rules / fiscal positions
- Studio *view* rebuild (the orange-builds cleanup) — separate initiative

## 4. Target state

### 4.1 Product hierarchy — 3 record types, only one storable

```
Master Item            (1127)        non-storable · template for SKU creation + quotation descriptor
  ├── M/I Master       (1127-M)      non-storable · metric description for quotations when length unknown
  │     ├── SKU        (1127-M-3.2)  storable · lot-tracked · the real product
  │     ├── SKU        (1127-M-3.6)  storable · lot-tracked
  ├── M/I Master       (1127-I)      non-storable · imperial description
  │     ├── SKU        (1127-I-10)   storable · lot-tracked
  │     └── SKU        (1127-I-12)   storable · lot-tracked
  └── Master ref link  1127 → 1003   template-level: "Character Decking comes from Furu"
```

**Length-only variants (`1127-3.2` in `import_master variant`, 1 331 rows) are NOT product records** — they carry no useful information beyond what the SKU already has. They become a characteristic on the SKU (length field) only. Existing records → `active=False` (archived, not deleted).

### 4.2 The two semantics of `kebony_parent_id`

This field is overloaded by measurement system — this is intentional, drives the US↔EU automatic flip:

| SKU measurement system | `kebony_parent_id` points to | Purpose |
|---|---|---|
| **Metric** (Belgium-native) | Another **Metric** SKU (raw material / input) | Manufacturing consumption. AX is metric-native; all BoM logic lives here. |
| **Imperial** (US-only) | The **Metric twin** FG SKU of the same physical dimensions | System-conversion link. Enables PO Imperial → SO Metric → delivery Metric → reception Imperial automatically when US purchases from Europe. |

**Imperial → Metric twin matching:** generator proposes the **nearest** metric length (e.g. `1127-I-10` = 10 ft = 3.048 m → nearest metric `1127-M-3.0` or `1127-M-3.2`); flagged in the cleanup Excel as "proposed, requires business validation" (red/white inverted cell).

### 4.3 AX decimeter encoding (RecipeFamily source)

The `KEY_In` / `KEY_out` columns encode length in **decimeters**. Divide by 10 to get meters.

| In file | Means |
|---|---|
| `1127 - 29` | SKU `1127-M-2.9` |
| `1003 - 30` | SKU `1003-M-3.0` |
| `1935 - 35` | SKU `1935-M-3.5` |

The `1003-30 → 1127-29` row therefore means: "Furu raw material at 3.0 m produces Character decking at 2.9 m" — 10 cm yield trim.

### 4.4 Mandatory fields per record type

| Record type | Mandatory |
|---|---|
| **Master Item** (1127) | `name`, `default_code`, `type = consu` (non-storable), `categ_id`, `x_studio_is_master_item = True`. May carry `x_studio_master_parent_id` pointing to another Master (for SKU-creation wizard linkage). |
| **M/I Master** (1127-M, 1127-I) | `name`, `default_code`, `type = consu`, `categ_id`, `x_studio_measurement_system` (Metric / Imperial), `x_studio_master_item_code_1` (points to parent Master Item), `x_studio_is_metric_imperial_master = True`. |
| **SKU** (1127-M-3.2, 1127-I-10) | `name`, `default_code`, `type = product` (storable, lot-tracked), `uom_id`, `uom_po_id`, `categ_id`, `route_ids`, `x_studio_length_m` (MES-mandatory), `x_studio_volume_m3`, `x_studio_boards_per_pack`, `x_studio_product_classification`, `x_studio_measurement_system`, `x_studio_master_variant_code` (points to M/I Master), `kebony_parent_id` (dual semantics per §4.2), `kebony_planning_family_id` for every manufacturable. |
| **`product.category` (on SKUs)** | `property_valuation = real_time`, `property_cost_method = FIFO`, input/output/stock valuation accounts set |
| **`product.packaging`** (on SKUs) | ≥1 line with boards per pack + lm per pack |

## 5. Output artefact — the cleanup Excel

A single `Product_Master_Cleanup_v1.xlsx` with one tab per product line:

- **Tab 1**: Scots Pine Character (white wood → SKU → FG, with master line first, then SKU rows, then FG rows)
- **Tab 2**: Radiata Pine (KRRS)
- **Tab N**: Chemicals
- **Tab N+1**: Accessories

**Columns** (consistent across tabs):

| # | Column | Content |
|---|---|---|
| 1 | `code` | SKU code (profile-system-length) or Master code |
| 2 | `parent_id` (code) | Human-readable parent code — **dual semantics per §4.2** |
| 2a | `parent_kind` | `metric_consumption` / `imperial_twin_proposed` / `master_template` / `none` |
| 3 | `level` | `master_item` / `mi_master` / `sku_metric` / `sku_imperial` / `archive_master_variant` |
| 4 | `name` | Product name |
| 5 | `x_studio_length_m` | |
| 6 | `x_studio_volume_m3` | |
| 7 | `x_studio_boards_per_pack` | |
| 8 | `x_studio_product_classification` | |
| 9 | `kebony_planning_family_id` | |
| 10 | `kebony_parent_id` | Resolved parent (or empty if unresolved) |
| 11 | `categ_id` | |
| 12 | `route_ids` | |
| 13 | `uom_id` | |
| 14 | `rdk_operation_id` | From master file |
| 15 | `action` | `create` / `update` / `no_change` |
| 16 | `unresolved_reason` | Only if row is unresolved |

**Colour coding (cell-level):**

| Colour | Meaning |
|---|---|
| 🔴 Full row red | Brand new — will be **created** |
| 🟠 Orange cell | Cell value will be **edited** (before → after) |
| 🟢 Green cell | Cell value unchanged |
| ⚪🔴 Inverted red/white | Parent or field **unresolved** — needs human input |

## 6. Script architecture — two scripts, different phases

| Phase | Script | Purpose | Writes to Odoo? |
|---|---|---|---|
| A (now) | `tools/product_master_generate.py` | Read the 3 source Excels + Odoo export, apply precedence rules, emit the cleanup Excel with colour coding | **No** — Excel only |
| B (after Excel is locked) | `tools/product_master_cleanup.py` | Read the **finalised** cleanup Excel, apply changes to Odoo | Yes — test first, then prod |

**Phase B script: `tools/product_master_cleanup.py`**

**Capabilities:**
- Read the 3 source Excels + current Odoo export
- Apply precedence rules, generate the cleanup Excel
- `--dry-run` (default): emit cleanup Excel + delta CSV, no writes to Odoo
- `--apply`: write to Odoo via XML-RPC (authenticated), wave-by-wave (`--wave scots-pine` etc.)
- `--undo-from <file>`: restore from a previous undo Excel
- Emit `undo_<timestamp>.xlsx` alongside every apply run
- Idempotent: second apply run = no-op if nothing changed
- Append a row per changed field to `changelog_<timestamp>.csv` (before / after / user / timestamp)

**Dependencies:**
- Studio fields must already exist in Odoo (script writes values, doesn't create fields)
- API credentials in `.env` (same pattern as `sync_to_odoo.py`)

**Cascading creates:**
- If a SKU references a Master that doesn't exist yet, the script creates the Master first, then the SKU, then the FG
- Order: Master → SKU → FG → packaging lines → routes

## 7. Validation layer (pre-flight, read-only)

Run before any write:

- [ ] No duplicate codes in the cleanup Excel
- [ ] Every SKU has a resolvable parent (Master exists or will be created)
- [ ] Every manufacturable has `kebony_planning_family_id`
- [ ] Every MES-bound SKU has `x_studio_length_m > 0`
- [ ] Every `categ_id` referenced meets the valuation checklist
- [ ] Every product has a `uom_id` in the length family
- [ ] All `route_ids` exist (manufacture / buy / dropship routes)
- [ ] No conflicts between the 3 source Excels that precedence rules don't resolve

Validation failures in `--dry-run` → report, don't abort. In `--apply` → abort unless `--force`.

## 8. Workflow (phased) — Excel-first, script-later

### Phase A — Excel only, zero Odoo writes

1. Plan doc signed off (this file)
2. **Read-only generator script** reads the 3 source Excels + current Odoo export → emits the cleanup Excel + validation report. No Odoo writes at this stage — everything happens in Excel.
3. Cleanup Excel circulated to Kebony team for gap-fill: missing masters, unresolved parents (red/white inverted cells), SKUs to create, RDK operations to map
4. Team fills in the red-inverted cells, iterates with Olivier until green across the board
5. **Final Excel locks** — signed off by Olivier, circulated as `Product_Master_Cleanup_v1_FINAL.xlsx`

### Phase B — Build the write-script, run on test

6. Build the write-script (`tools/product_master_cleanup.py --apply`) that consumes the locked Excel
7. Script `--dry-run --env test` on **test** Odoo with the final Excel → diff report
8. Olivier reviews diff → approves
9. Script `--apply --env test --wave scots-pine` → first wave applied to test
10. Smoke test in test (MO can be generated from a product, valuation JEs fire, MES-required fields present, etc.)
11. Repeat per wave (KRRS, chemicals, accessories)

### Phase C — Production

12. **Full snapshot** of production product data (export all relevant tables as rollback)
13. Script `--apply --env production --wave scots-pine`
14. Smoke test in production
15. Repeat per wave
16. Archive the undo Excel + changelog with the wave

**Hard rule:** no production write until Phase B is fully green on test.

## 9. Multi-company

Product master is mostly global, but some fields are company-scoped (accruals, consignment). This wave touches **global** fields only — the script runs in a neutral company context. US-specific accrual fields are NOT in scope (handled separately).

## 10. Sign-off sequence

1. Plan reviewed and approved by Olivier → **this file locks**
2. Audit script + cleanup Excel generated → reviewed by Kebony team
3. Team gap-fills → Olivier approves final Excel → **Excel locks**
4. Dry run on test → Olivier approves delta
5. Apply wave 1 on test → smoke test → approve
6. Repeat waves 2–N on test
7. Production apply (wave by wave)

## 11. Decisions made + open questions

### Decisions locked 2026-04-23

- **Belgium = Metric native.** AX thinks only metric. Imperial = translation layer for US only.
- **`kebony_parent_id` dual semantics** per §4.2 — metric = manufacturing parent, imperial = metric twin for US↔EU flip.
- **Decimeter encoding** in AX sources — divide `KEY_In/KEY_out` suffix by 10 for length in metres (§4.3).
- **Imperial → Metric twin** = generator proposes **nearest metric length**, business validates in the cleanup Excel (red/white inverted cell).
- **Archive, don't delete** — deprecated Master Variant (length-only) records get `active=False`.
- **Master Variant records as products = DEAD CONCEPT.** Length lives only on SKUs going forward.

### Still open (need input from you / team)

- Which product line goes first after Scots Pine Character? (KRRS Radiata? Chemicals?)
- Are there Studio fields on `product.template` declared but never populated — candidates for removal in the later view-rebuild wave?
- Who on the Kebony side owns final sign-off on the cleanup Excel?
- RDK operations in the master file — straightforward mapping, or per-SKU judgement?
- **Yield trim per species** — RecipeFamily shows a 10 cm trim for Scots Pine Character (1003-30 → 1127-29). Is this constant across the species, or does it vary by SKU? Affects metric consumption-parent resolution.

## 12. Parallel work

Independent from this plan:
- **Product form rebuild** (from Studio → code) — separate initiative, same module. The cleanup script doesn't care which form is active; it writes to fields, not views.
- **MES API contract** (`MES API Contract.md`) — separate, read-only dependency on `x_studio_length_m` being present.
- **🔭 Product Hub** (on the horizon) — once the 3-level hierarchy is clean and the `kebony_parent_id` dual-semantics rule is locked, we naturally want a dedicated administration screen:
  - Master Item list view with "create SKU batch" wizard: pick a Master → multi-select lengths (metric or imperial) → generates SKUs with pre-filled parent, planning family, packaging inherited from the Master
  - Imperial-Metric twin manager: visual matcher, drag-drop or auto-nearest with manual override
  - Master-to-Master template linkage editor (white wood Master → brown wood Master)
  - Archive / reactivate controls
  - Bulk field editor for `x_studio_*` fields on SKUs within a Master
  - Read-only audit panel showing MES operation codes observed per SKU (from `kebony.process.pack.event`)
  Built as a new top-level menu item in `kebony_manufacturing`. Deferred until data cleanup is complete — no point wrapping a UI around messy data.

---

## See also

- [[Product Master Data]] — existing reference on product hierarchy, classification, field conventions
- [[Terminology Bible]] §1 Product Hierarchy + §5 Manufacturing Terms
- [[MES API Contract]] — downstream consumer that needs `x_studio_length_m`
- Prior audit files in the vault root
