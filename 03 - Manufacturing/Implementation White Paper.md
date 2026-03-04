
  
## **Version 1.1 – FIFO + 3-Stage Absorption + External Treatment Doctrine**

---
## **1. Purpose**

This document defines how Kebony’s industrial manufacturing landscape is implemented in Odoo 19. It translates physical operations, planning grammar, costing doctrine, and traceability requirements into a coherent ERP architecture. It defines how production, inventory, valuation, subcontracting, and contribution margin are structured. It is implementation-oriented but remains system-agnostic at configuration detail level. It freezes architectural decisions required for Phase 1 go-live and ensures scalability for future extensions such as external finishing treatments.

---
## **2. Core Design Principles**

### **2.1 Costing Doctrine**

Raw materials are valued under FIFO. Finished goods are valued under FIFO. Conversion costs are absorbed through Work Centers. Conversion absorption is split into three internal pools: Stacking, Autoclave, and Dryer. Total absorbed indirect cost remains equal to the legacy “Kebony hour” total; only allocation granularity is improved. No multi-layer GL explosion is implemented in Phase 1. Contribution margin decomposition is achieved via analytic distribution, not via GL fragmentation.

### **2.2 Transformation Boundaries**

Three industrial transformation boundaries are explicitly modeled:

1. Reception (raw inventory creation).    
2. Exit from Kebonisation (Semi-FG or FG creation).
3. External subcontracting (Machining or future Finishing).
    
Each boundary corresponds to a valuation control point and traceability checkpoint.  
### **2.3 Bottleneck Recognition**

The Dryer remains the structural bottleneck. Capacity planning remains dryer-centric. However, cost absorption is no longer dryer-exclusive; stacking and autoclave are recognized as cost drivers.

---

## **3. End-to-End Industrial Flow in Odoo**

### **3.1 Reception**

Inventory Receipt creates FIFO valuation layers. Prime material is received into Raw–Prime location. Defect material is received into Raw–Defect location. No production logic occurs at this stage. Claims management is out of scope.  
### **3.2 Asynchronous Mix Production**

Mix production is modeled as an independent Manufacturing Order. Raw chemicals (FIFO) are consumed. Ready-Mix inventory is produced and stored in a tank location. Mix MO absorbs its own labor and overhead (if defined). Autoclave consumes Ready-Mix only, never raw chemicals directly.

### **3.3 Entry to Kebonisation**

Kebonisation Manufacturing Order is created. Raw boards move from Raw location to WIP-Kebonisation. Destacking and stacking operations occur within the MO. Accounting entry: Dr WIP / Cr Raw Inventory (FIFO value preserved).
### **3.4 Kebonisation Core**

Operations inside the MO include:

- Entry Stacking (Process Pack creation, board-by-board QC)
- Autoclave
- Dryer
- Exit Stacking / Destacking (Finished Good Pack creation, board-by-board QC)      

Consumed components:

- Raw boards
- Ready-Mix
- Packaging (if applied at this stage)

Conversion absorbed through three work centers.

### **3.5 Exit from Kebonisation**

After dryer, boards pass through exit stacking (destacking) where board-by-board QC inspection occurs — same 3-way grading as entry stacking (A-Grade / B-Grade / Scrap). Packaging materials are consumed at this stage. Production outputs either:
- Semi-FG (Clear) into WIP-Clear location, or
- Finished FG (Character) into FG location.

Accounting: Dr Semi-FG or FG Inventory / Cr WIP. Valuation includes FIFO material, FIFO mix, and absorbed stacking, autoclave, and dryer costs.

### **3.6 Optional External Machining (RDK)**

Applies primarily to Clear-line (Radiata) products that require post-kebonisation machining (profiling, planing). Some Character-line (Scots Pine) products may also route to RDK for **cut-to-length** operations.

**Operational flow:** Semi-FG or FG is transferred to the RDK subcontractor location. A Subcontracting MO consumes the Semi-FG/FG and adds the machining service, repackaging, and transport (via landed cost). Upon completion: Dr Final FG / Cr WIP-Machining.

**Costing model – Standard then Adjust:**

1. **At production time** – the Subcontracting MO values machining at **standard cost**, derived from a **volume-dependent price list** (cost per m³ decreases at higher volumes). The standard rate used is based on **budget volume assumptions** for the period.
2. **At invoice time** – the actual vendor bill from RDK arrives (typically monthly, after the fact). The real cost may differ from the standard because actual volumes differ from budget.
3. **Variance allocation** – the difference between standard cost absorbed and actual invoice cost must be **allocated back to inventories** (and to COGS for units already sold). The exact allocation rule (e.g., prorate by volume across lots still in stock, or post to a machining price variance account) remains to be defined.

> ⚠ **Open investigation:** The price list modelling in Odoo, budget vs actual reconciliation mechanism, and inventory revaluation vs variance account decision are tracked as **INV-1** in the backlog.

---

## **4. BOM Architecture**

### **4.1 Planning Family as BoM Template**

One BoM per **product** (not per family). The Planning Family serves as a **template** that defines shared operations (stacking, autoclave, dryer hours) and chemical consumption rates. A "Push BoM to Products" action copies the family template to all products in that family. The wood component remains product-specific and must be set per product.

### **4.2 Kebonisation BOM**


Components include:

- Raw wood
- Ready-Mix (liters per m³)
- Packaging materials (if internal stage)
  

Scrap percentages defined at component level. Machining is excluded from this BOM and handled via subcontracting.

---

## **5. Work Centers & Cost Absorption**

### **5.1 Internal Work Centers**


Four work centers are defined:

- Stacking (covers both entry stacking and exit stacking/destacking — two separate operations on the same machine)
- Autoclave (impregnation operations)
- Dryer (primary bottleneck, includes general plant overhead allocation)
- Chemical Mixing (for asynchronous mix MO — not part of kebonisation cost absorption)

  

Each has a fixed duration per planning family and a defined hourly rate.

### **5.2 Cost Pool Allocation**

  

Annual indirect cost pool is split into:

- Stacking pool → allocated by stacking hours
- Autoclave pool → allocated by autoclave hours
- Dryer pool (+ general overhead) → allocated by dryer hours

  

Total annual absorbed cost equals legacy model. Only allocation distribution changes.


### **5.3 Economic Rationale**

This prevents over-concentration of cost on dryer stage and improves transparency without altering total cost base or destabilizing contribution margins.

---

## **6. Accounting Flow Summary**

  
Raw Receipt:

Dr Raw Inventory / Cr GRNI (FIFO layer created)
Mix MO Consumption:
Dr WIP-Mix / Cr Raw Chemical
Completion: Dr Ready-Mix / Cr WIP-Mix

  
Kebonisation MO Consumption:
Dr WIP / Cr Raw Inventory
Dr WIP / Cr Ready-Mix
  

Kebonisation Completion:
Dr Semi-FG or FG / Cr WIP

  

Subcontract Machining:
Dr WIP-Machining / Cr FG (transfer to subcontractor)
MO Completion at standard: Dr FG / Cr WIP-Machining (standard cost from price list)
Vendor Bill (actual): Dr WIP-Machining / Cr AP
Variance: Dr Machining Variance (or FG revaluation) / Cr WIP-Machining
  *(allocation rule TBD – see INV-1)*

  

Sale:

Dr COGS-FG / Cr FG Inventory

COGS posted to single GL account. Analytic distribution provides contribution margin structure.

---

## **7. Analytic Contribution Structure**

  

GL remains simplified. Analytic plans include:

- Business Unit
- Country
- Margin Layer (optional)


COGS-FG receives analytic distribution into:

- Wood
- Chemicals
- Machining
- Other Direct
- Conversion

  

Managerial waterfall preserved without GL fragmentation.

---

## **8. Inventory & Traceability**

FIFO maintained end-to-end. Lot traceability preserved across all transformations. Cubic volume, board count, and capacity equivalents are snapshot at movement time. No dynamic recalculation allowed.

---

## **9. External Finishing Treatment Doctrine (0 → N Model)**

### **9.1 Status**

External finishing (fire retardant, coloring, etc.) is not operational in Phase 1 but architecture must allow seamless activation.

### **9.2 Structural Principle**

Finishing treatment is a post-production transformation, not a dimensional attribute. It is modeled as subcontracting stage, not product variant.

### **9.3 Product Identity**

Base finished product remains singular per species/dimension/profile. Treatment does not create SKU variants.

### **9.4 Lot-Level Treatment Attributes**

Treatment is stored at Lot level as multi-value attributes (0 → N), such as:

- Fire Retardant
- Coloring
- Future treatments

Products remain dimensionally identical. Treatments do not alter volume or unit conversions.

### **9.5 Operational Flow**

Finished FG → Transfer to Finishing Partner → Subcontracting MO → Return Treated FG. Each treatment stage accumulates cost on same SKU via FIFO layer.

### **9.6 Accounting**


Dr WIP-Finishing / Cr FG
Vendor Bill: Dr WIP-Finishing / Cr AP
Completion: Dr FG / Cr WIP-Finishing

### **9.7 Why Variants Are Rejected**

Variants would cause combinatorial SKU explosion and distort planning grammar. Treatment is a transformation layer, not a dimensional variant. 
### **9.8 Reporting**

Sales, margin, and volume by treatment remain reportable via lot attributes without SKU multiplication.

---

## **10. Phase 1 Exclusions**


No real-time labor tracking. No advanced variance accounting for internal production (external machining uses standard-then-adjust with variance — see §3.6). No chemical overhead micro-splitting. No dynamic allocation automation. No GL-level COGS explosion.

---

## **11. Strategic Outcome**


This architecture preserves industrial truth, FIFO integrity, bottleneck logic, traceability, and contribution margin clarity. It minimizes SKU complexity, avoids variant fragility, supports subcontracting stages, and provides stable foundation for April go-live while remaining extensible.

---