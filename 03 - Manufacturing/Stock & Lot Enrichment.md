
Conceptual White Paper – Inventory, Capacity & Traceability Layer

## **1. Purpose of This Document**

This document defines the inventory enrichment layer required for Kebony’s Odoo 19 implementation.

It extends the Manufacturing and Planning White Papers by enabling economic normalization in cubic meters, embedding capacity equivalents at stock level, supporting board-level KPIs, preserving operational linear measurement, and strengthening end-to-end traceability.

This document defines what inventory must represent, not how it is technically implemented.
## **2. Foundational Doctrine**

Kebony inventory simultaneously carries three dimensions:

| **Dimension** | **Unit**                | **Purpose**                |
| ------------- | ----------------------- | -------------------------- |
| Operational   | Linear meter            | Handling, sales, logistics |
| Economic      | Cubic meter             | Costing, margin, KPI       |
| Capacity      | Dryer / Autoclave hours | Bottleneck economics       |
| Commercial    | coverage                | selling information        |
Linear meter remains the operational stock unit.
Cubic meter becomes the economic normalization unit.
Dryer and autoclave hours become capacity normalization units.
Inventory must expose all three without distorting operational flow.

## **3. Stock-Level Enrichment**

Enrichment applies at Stock Move, Stock Move Line, Stock Quant, and optionally Stock Valuation Layer.
All enrichment values are computed at movement time, stored (not dynamic), and historically frozen.

### **3.1 Cubic Volume**

Each stock movement must store cubic_volume.
It is derived from normalised linear quantity (in meters) multiplied by the **normalised volume ratio** (`x_studio_volume_m3` — always m³ per linear meter, regardless of whether the product is metric or imperial). The standard Odoo `volume` field must NOT be used for this calculation because it is localised (m³/lm for metric, ft³/lf for imperial) and would produce incorrect results for imperial products. The `volume` field is retained for transport/supply chain documents where localised units are required.
Purpose: board KPI in cubic meters, margin normalization, economic stock reporting, cubic forecasting.
Cubic volume becomes the economic stock quantity.


### **3.2 Board Count**


Inventory must expose board_count.
Board count is stored and frozen at movement time.
It supports operational control, packaging verification, and logistics clarity.
Board count is informational, not a valuation driver.
### **3.3 Capacity Equivalents**

Inventory must embed dryer_hours_equivalent and autoclave_hours_equivalent.
These represent bottleneck resource consumption embedded in stock.
Purpose: capacity normalization, product mix simulation, inventory saturation analysis, fixed-cost absorption analysis, and investment simulation (e.g. 4th dryer impact).
Capacity equivalents are frozen at production time and expressed in hours.
### **3.4 Economic Normalization**

Each stock layer must allow calculation of eur_per_cubic.
This is derived from stock valuation divided by cubic_volume.
Purpose: margin per cubic, family profitability, cross-species comparability, and board KPI consistency.
This value should be stored for performance and historical stability.
### **3.5 Cubic Stock States**

Operational stock states exist as quantity_on_hand, reserved, available, and forecasted.
Economic equivalents must exist as cubic_on_hand, cubic_reserved, cubic_available, and cubic_forecasted.
Forecast cubic must include MO outputs, PO receipts, SO commitments, and internal consumption.
This ensures board-level cubic KPIs reflect operational truth.
### **3.6 Capacity Stock States (Advanced Layer)**

Optional but strategic fields include dryer_hours_on_hand, dryer_hours_reserved, dryer_hours_forecasted, and autoclave_hours equivalents.
These reveal bottleneck capacity embedded in inventory and constrained resource allocation across families.

### **3.7 Commercial Information**

Each profile has a specific coverage depending on the shape. It would be important for the sales team to know how many square meters are readily available in stock. For architecture projects this could be important information.

##
## **4. Lot-Level Enrichment**

Lots represent traceable physical identity and are critical for FSC / PEFC certification, supplier traceability, quality audits, and sustainability reporting.
### **4.1 Frozen Production Identity**

Each lot must store snapshot information: species, planning family, production date, dryer reference time, autoclave reference time, cubic volume produced, and capacity equivalents.
Snapshotting prevents master data changes from corrupting historical analysis.
### **4.2 Traceability Chain (1-to-N Model)**

Transformation must preserve input lots and output lots across production.
Production may follow 1 input lot → N output lots, N input lots → 1 output lot, or N input lots → N output lots.
Every finished lot must be traceable back to supplier, purchase order, inbound reception, quality inspection, chemical mix batch, and autoclave cycle.
This is essential for certification, recall management, audit compliance, and sustainability reporting.
### **4.3 Supplier & Invoice Traceability**

Through lot chains and valuation layers, it must be possible to trace:
Finished lot → Production order → Consumed raw material lots → Supplier receipt → Purchase order → Supplier invoice.
This ensures financial traceability and certification continuity.

## **5. Snapshot Principle**

Stock must represent what was true at the time of movement.
If planning families or dimensions evolve, historical stock must remain stable.
Snapshot fields are therefore required for family ID, species, conversion factors, and capacity equivalents.
Dynamic recalculation is prohibited.
## **6. Strategic Impact**

This enrichment enables cubic-based board KPIs, margin normalization, capacity economics analysis, product mix profitability simulation, inventory saturation analysis, certification-grade traceability, and investment decision modeling.
It transforms Odoo from an inventory system into an industrial economic cockpit.
## **7. Scope Boundaries**

This document does not define technical implementation, Odoo model structure, field naming, UI presentation, or performance architecture.
These decisions belong to implementation-level documentation.
## **8. Final Principle**

Inventory must simultaneously represent material, money, capacity, and origin.
Only then does Kebony’s ERP reflect industrial reality.