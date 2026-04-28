# Meeting Notes — EU CRM — Current Structure & Dynamics Walkthrough (DACH)

**Date:** 28 April 2026
**Attendees:** Lars Arndt (LA) – DACH Sales Lead, Rishi Pankaj (RP)
**Duration:** ~58 minutes
**Platform:** Microsoft Teams
**Project:** Kebony ERP Implementation (Odoo 19)
**Tags:** #meeting-notes #CRM #EU #DACH #Dynamics #kebony

> *Note: Transcript was AI-generated and may contain minor inaccuracies in names/terminology.*

---

## 1. Current CRM Setup — Microsoft Dynamics (DACH)

Lars walked Rishi through the current Dynamics CRM used by the DACH sales team. The system is structured around three core objects: Activities, Accounts, and Sales Projects.

The CRM has approximately 10,000 addresses in Germany alone. Accounts are divided into the following customer types:
- Distributor
- Importer
- Retailer / Preferred Partner (Trader PP)
- Industrial
- Architect
- Landscape Architect
- Consumer
- Public Authority

Each account is owned and maintained by the sales rep responsible for that region. The system allows filtering by rep, by customer type, and by region, and data can be exported to Excel.

## 2. Accounts, Contacts & Projects — Structure & Interlinkage

**Accounts**
- An account is created for any company with whom there is a meaningful business relationship or strong potential — not for every inbound enquiry
- Even companies that do not buy directly from Kebony (e.g. Architects) are maintained as accounts, as they are key influencers in the sales process
- Accounts that are only general leads or cold contacts are not entered into the CRM — only those with real potential are created as accounts

**Contacts**
- Contacts are individuals linked to an account (e.g. managing director, purchasing, sales)
- Contacts are created directly within the account record and are automatically linked to it
- The contacts list can be filtered and used for targeted mailings by customer type, which Lars periodically sends to the marketing team

**Sales Projects**
- Projects represent opportunities where Kebony has a realistic chance of being specified and sold
- Four defined stages: Identified → Offer Made → Specified → Order Placed; can also be marked as Won or Lost
- Projects are linked to the relevant Account (typically the architect office responsible for the project)
- Products can be added to a project; the system pulls pricing from the regional price list to automatically calculate project revenue
- Projects with no confirmed product yet can be entered with a zero value and updated as the specification develops
- Minimum project value threshold: €10,000–15,000; below this it is not considered worth entering into the system
- Lars also uses the project module to track new dealer acquisition efforts — however, there is no formal, standardised definition of what constitutes a project; this has not been documented

## 3. Activity Logging

- Sales reps log visit activities against accounts, including the type of visit and a brief description of what was discussed
- Activity types available: phone call, mail, letter, appointment — in practice, only appointments/visits are used
- The activity log functions primarily as a personal record for reps, not as a management control tool
- A historical precedent exists where visit counts (300–400 per year) were part of the rep bonus structure, tracked via the activity log
- **Key pain point:** No integration between Dynamics and Outlook calendar. Reps manage all appointments in Outlook/Teams; the CRM is not used for scheduling or daily task management. The lack of calendar sync creates double-entry and is cited as a reason for low CRM adoption
- **Desired future state:** Any appointment or follow-up created in the CRM should automatically sync to Outlook calendar, and vice versa

## 4. Email Tracking to Accounts & Projects

- Dynamics is integrated with Outlook, allowing individual emails to be manually tracked against an account or project
- Only important emails are tracked; not all communications are logged
- Lars flagged this as a **critical data continuity requirement** for the Odoo migration: all historical email communications must not be lost in the transition
- **Proposed migration approach:** Phased — design and launch the new system first, then import legacy data in a second phase. Lars suggested retaining a single read-only Dynamics licence post-migration so historical data remains accessible

## 5. Lead Management — Current Gaps

- There is currently no Lead module in the Dynamics setup — only Accounts and Sales Projects
- New dealer prospects, inbound sample requests, website enquiries, and rep-identified target accounts are tracked informally in Excel, OneNote, or not at all
- Lars's view: all sample requests should automatically be captured as leads in the CRM, assigned to the relevant rep by region
- A lead should only be converted to an account once confirmed as a genuine prospect, to avoid inflating account numbers
- Lead-to-account qualification criteria need to be defined — Lars suggested this should be done collectively across all country managers to ensure a consistent approach
- Rishi to prepare a lead qualification framework/questions document to share ahead of that discussion
- There are currently 4 country managers: Marta (Norway, Sweden, Denmark), Nina (Rest of World), a newly hired French country manager, and the DACH manager. A cross-country workshop on CRM design alignment was proposed once the design is sufficiently advanced

## 6. Distributor Management & Sales Model

Two distinct sales motions operate in parallel:

1. **Distributor channel** — Kebony trains the distributor's internal sales team so they can sell Kebony to installers. The target for a sales rep working a new distributor is always a stock order (typically €30,000–100,000 for an initial stock-up). Once stocked, the distributor has internal pressure to sell through
2. **Project specification** — Completely independent from the distributor channel. Sales reps work directly with architects and installers to get Kebony specified in construction/renovation projects. Once specified, Kebony does not control which dealer fulfils the order — the product finds its route to market through the tendering process

**Preferred Partner criteria (Germany-specific):** Must stock Kebony Clear and Kebony Character, minimum annual turnover of €100,000, trained inside and outside sales staff, showroom display, joint Tandem tours with Kebony sales rep. Preferred Partners receive year-end kickbacks and are listed on the Kebony website.

Distributor stock replenishment frequency varies significantly — some turn stock 4x per year, others very slowly. Size of distributor is not a reliable predictor of performance.

## 7. Customer Segmentation — Direct vs. Indirect

- All sales in Germany flow through a single central importer (Veltholz, located in Bremen). Kebony invoices only this importer; regional dealers buy from Veltholz, not directly from Kebony
- Account types in use: Distributors, Importers, Retailers/Preferred Partners, Architects, Landscape Architects, Industrial (carpenters, pool builders, windows & doors, furniture producers), Public Authorities, Consumers
- Proposed framework: **Direct** (installers, dealers, end users) vs. **Indirect** (architects, landscape architects, public authorities) — to be refined and agreed as part of the CRM design

## 8. KPIs & Performance Tracking

Lars currently tracks sales rep performance using two primary measures:

1. **Turnover by region** — derived from monthly importer sellout data (Veltholz Excel file). Each rep receives a monthly breakdown of their region's turnover by dealer. Quarterly and annual targets are set per rep. New dealer wins are also visible from this data. This file is shared monthly with each sales rep and with controlling/Sami
2. **Project activity in CRM** — volume of new projects entered, and project status (won/lost/specified). Lars can filter by rep, stage, and period directly in Dynamics

Tracking turnover at the project level is not currently possible, as all revenue is consolidated at the importer level and cannot be directly attributed to individual projects within the CRM.

## 9. Cross-Regional CRM Consistency

- Lars's view: the CRM setup in DACH is broadly representative of how other EU regions operate
- Norway (Marta's team) uses slightly more Dynamics functionality — possibly including email and phone call logging in addition to appointments
- No shared or cross-border accounts exist in practice; all accounts are regional

## 10. Actions & Next Steps

| # | Action | Owner |
|---|--------|-------|
| 1 | Share monthly importer sellout Excel file (sample) with Rishi | Lars Arndt |
| 2 | Provide access to Dynamics CRM for Rishi — to be arranged via IT (Ronaldo Beck) | Lars Arndt |
| 3 | Prepare lead qualification framework/questions document to share with Lars ahead of cross-country discussion | Rishi Pankaj |
| 4 | Organise cross-country manager workshop on CRM design alignment once design is sufficiently advanced | Rishi Pankaj |
| 5 | Investigate feasibility of retaining a read-only Dynamics licence post-migration for historical data access | Rishi Pankaj |
