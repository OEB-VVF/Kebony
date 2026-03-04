## **1. Purpose of This Document**

This document defines the structural manufacturing object model used to represent Kebony’s physical reality inside Odoo.

It formalizes how:

- Process Packs
- Autoclave Loads
- Dryer Loads

are translated into Manufacturing Orders and traceability objects.

It freezes the architectural doctrine to avoid future redesign, SKU explosion, or valuation distortion.

---
## **2. Core Principle**

### **Dryer Load = Primary Manufacturing Object**

At Kebony: 

> The Dryer Load is the atomic planning, costing, and valuation unit.

Therefore:

- **1 Dryer Load = 1 Manufacturing Order (MO)**
- Everything else is sub-structure
- No nested MOs
- No fake intermediate products
- No GL explosion
---
## **3. Structural Hierarchy**

The manufacturing hierarchy is defined as follows:

### **Level 1 – Dryer Load (DL)**

Represents:
- Primary planning primitive
- Capacity primitive (one DL blocks one dryer for full cycle)
- Cost absorption object
- FIFO boundary

Example reference: **DL-26-0001**

Attributes:
- Planning family
- Total volume (m³)
- Total linear meters
- Board count
- Estimated/actual dates and duration
- State: draft → planned → locked → done

### **Level 2 – Autoclave Batch (AC)**

Each DL contains exactly **two** autoclave batches (physical constraint).

Represents:
- Feeder unit for dryer
- Family-compatible batch grouping
- Scheduling sub-unit (start/finish times)

Example reference: **DL-26-0001-AC1**

### **Level 3 – Process Pack (PP)**

Each AC contains typically **5–8 process packs**.

Represents:
- Homogeneous grouping of boards (same planning family)
- Smallest physical unit moving through production
- Created during entry stacking

Attributes:
- Planning family
- Total volume
- Total linear meters
- Board count
- Raw lots included
- QC downgrade flag (if any)

Process packs:

- Do not create accounting entries
- Do not exist as sellable products
- Do not generate inventory layers
- Exist purely as industrial metadata
---
## **4. Traceability Chain**

The model enables complete reconstruction:

Raw Lot

→ Process Pack
→ Autoclave Batch
→ Dryer Load
→ Finished Lot

This supports:

- FSC / PEFC audits    
- Chemical impregnation trace
- Machine occupancy history
- Future MES reconciliation

Without SKU multiplication.

---
## **5. Capacity & Bottleneck Integrity**

This structure preserves:

- Dryer as primary bottleneck    
- Autoclave as feeder (but measurable)
- Stacking as labor stage

If autoclave becomes bottleneck in future:

- AC batches are already modeled
- Capacity analysis is already available
- No redesign required    
---
## **6. Accounting Doctrine**

Only Dryer Load MO creates:
- WIP absorption
- FIFO material consumption
- Finished Goods valuation
- 
Autoclave and Process Packs are non-financial.

This guarantees:
- No valuation distortion
- No GL fragmentation
- No COGS complexity explosion

---
## **7. Strategic Outcome**

This model:
- Respects physical truth
- Preserves FIFO integrity
- Avoids SKU combinatorial explosion
- Supports subcontracting layers
- Is scalable to finishing treatments
- Is MES-ready
- Is audit-safe

It becomes the foundation of a reusable “Wood Manufacturing Vertical”.

---
## **8. Planning Families — Production-Aligned**

### **8.1 Doctrine**

Planning families represent **what goes through the dryer together** — products with the same impregnation time and chemical absorption characteristics. The **master source** is production (Kallo / RecipeFamily), not finance (Standard Cost sheet).

**Key principle:**
> Downstream machining (rough sawn → finished/machined) is **not** a planning family. It is handled by a standard Odoo BoM linking a rough-sawn product to its machined variant.

This means:
- A KRRS 1” rough sawn board and a KR 1” machined board belong to the **same** planning family (KRRS 1”)
- The machining step is a separate BoM operation, not a separate production run
- This avoids family explosion and keeps planning aligned with physical dryer capacity

### **8.2 Family Registry**

#### Scots Pine (KSP) — Belgium

| Family | Code | Prod CODE2 | Thickness | Dryer (h) | Mix (kg/m³) | Products |
|--------|------|-----------|-----------|-----------|-------------|----------|
| KSP 1” Cladding | KSP1C | SP Clad1 | 21mm | 55 | 230 | 1243, 1407, 2216, 2338, 2339, 2378, 2380, 2594, 2596, 2649 |
| KSP 1.5” Terrace | KSP15T | SP Terrace | 28mm | 75 | 309 | 1127, 2449, 2485 |
| KSP 2” Pier Decking | KSP2PD | SP Pierdec | 34mm | 75 | 267 | 1171 |
| KSP 2” Construction | KSP2CON | SP Constru | 36–98mm | 80 | 251 | 1128, 1130, 1174, 1178, 1181, 1182, 1200, 1217, 2168, 2405 |

> **Note:** Finance treats item 1200 (48×73mm) as “KSP 2” Cladding” — production groups it under Construction. Production is correct.

#### Radiata (KRRS / KR) — Belgium

| Family | Code | Prod CODE2 | Thickness | Dryer (h) | Mix (kg/m³) | Products |
|--------|------|-----------|-----------|-----------|-------------|----------|
| KRRS 1” | KRRS1 | Radiata 1 | 25mm | 54 | 676 | 1931, 1935, 2234, 2535 |
| KRRS 2” | KRRS2 | Radiata 2 | 38–50mm | 54 | 676 | 2220, 2423, 2489, 2523, 2537, 2752, 2754 |
| Radiata NCC | KRNCC | Radiata NCC | 25mm (light) | 48 | 541 | 2755, 2756, 2757, 2758, 2759, 2760, 2761 |
| KRRS 3” (75×75) | KRRS3 | Radiata 3 | 75mm | TBD | TBD | 2780 |
| KRRS 4” (100×100) | KRRS4 | Radiata 4 | 100mm | TBD | TBD | 2781 |

> **NCC** = New Cladding Collection — lighter chemical treatment (48h dryer vs 54h). Absorbs the former “KRRS 1” Light” family (identical processing).

> **KRRS 3” and 4”** have no data in the Standard Cost sheet yet. Parameters estimated from KRRS 2” as placeholder — production must provide actual dryer hours and chemical consumption.

#### Other / Specialty

| Family | Code | Type | Dryer (h) |
|--------|------|------|-----------|
| KMRS | KMRS | Maple | 210 |
| KRRS Norway | KRRSNO | Radiata (Norway site) | 54 |
| KSemiClear | KSEMICLEAR | Radiata | 54 |
| KSUGIRS | KSUGIRS | Sugi | 140 |
| KHINOKIRS | KHINOKIRS | Hinoki | 192 |
| Kebony Spruce | KSPRUCE | Spruce | 30 |
| Taeda RS | TAEDARS | Taeda | 54 |
| KS | KS | Other | 54 |

### **8.3 Downstream Machining (BoM, not Planning Family)**

The following are **not** planning families — they represent machining steps applied **after** Kebonization:

| Finance Name | What It Really Is | BoM Logic |
|-------------|-------------------|-----------|
| KR 1” | Machined from KRRS 1” rough sawn | BoM: KRRS 1” product → KR 1” finished product |
| KR 1” PRE | Pre-machined before Kebonization | BoM: raw → pre-machine → Kebonize (uses KRRS 1” family) |
| KR 2” | Machined from KRRS 2” rough sawn | BoM: KRRS 2” product → KR 2” finished product |
| KR 2” PRE | Pre-machined before Kebonization | BoM: raw → pre-machine → Kebonize (uses KRRS 2” family) |

These are modelled as standard Odoo BoMs with different product codes for input and output. Each finished product has its own product code, and the BoM defines the transformation from rough sawn to machined.