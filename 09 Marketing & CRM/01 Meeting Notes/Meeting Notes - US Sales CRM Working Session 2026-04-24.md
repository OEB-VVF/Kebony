# Meeting Notes — US Sales & CRM Working Session — Salesforce / Odoo CRM Design

**Date:** 24 April 2026
**Attendees:** Andy Hehl (AH), Bethany Dunnam (BD), Rishi Pankaj (RP)
**Platform:** Microsoft Teams
**Project:** Kebony ERP Implementation (Odoo 19)
**Tags:** #meeting-notes #CRM #US #Salesforce #kebony

> *Note: Transcript was partially captured.*

---

## 1. Overall Issue & Future State Vision (Andy Hehl)

Andy opened with the overarching concern that the business is operating across too many disconnected data sources, and that moving towards a single source of truth is essential for efficiency.

- Data is currently fragmented across Excel spreadsheets, SharePoint, and Salesforce — none of which are fully integrated or consistently used
- Quiz/training records and project tracking sit partially in SharePoint and partially in Excel — not a sustainable setup
- Andy's position: everything should ultimately live in one system, making data accessible, consistent, and actionable
- The current state creates duplicated effort, poor visibility, and an inability to measure commercial performance meaningfully
- Future state vision: a single CRM where Accounts, Projects, and Contacts are properly interlinked and outcomes can be tracked end to end

## 2. CRM Architecture — Accounts, Projects & Contacts *(Critical)*

The interlinkage between Accounts, Projects, and Contacts was identified as the most critical design consideration for the CRM.

**Accounts**
- Represent the organisations Kebony engages with (e.g. Architecture firms, Distributors, Retailers, Rep Group firms)

**Projects**
- Created when Kebony is specified by an Architect for a design/build project
- Focus threshold: projects valued at $10,000 or more
- Project outcomes are highly uncertain — architects may substitute Kebony for a cheaper alternative if costs are challenged
- Once a project moves past the specification stage to the builder/contractor, Kebony's visibility is frequently lost
- A significant number of projects end up in an unknown state — the team cannot confirm whether the project ultimately sold or was lost
- Follow-up is attempted via distributors, retailers, and rep groups, but responses are inconsistent

**Contacts**
- Contacts are the individual people associated with Accounts (e.g. an Architect at a firm, a Sales rep at a distributor)
- Bethany shared that the team works with a defined set of Contact Personas — screenshot shared via email during the meeting
- Personas (not a strict hierarchy, but defined roles) include at minimum: Architects, Distributors, Retailers, and Rep Groups
- Rishi requested a detailed walkthrough of the persona model to map it accurately into the CRM data structure

**Interlinkage**
- A Contact belongs to an Account
- A Project is linked to both an Account and the Contacts involved at each stage
- Without this linkage it is not possible to track which Architect specified which Project, which Distributor is responsible for fulfilment, or measure conversion by persona, geography, or channel

## 3. Key Issues
1. No single source of truth — data fragmented across Excel, SharePoint, and Salesforce
2. Project outcome visibility gap — the team loses sight of project status after the specification stage
3. Architect substitution risk — cost pressure at the contractor stage can result in Kebony being replaced; not currently tracked
4. Distributor/rep group feedback loop is unreliable — external parties are the primary source of outcome data but respond inconsistently
5. CRM adoption is poor — not being used systematically to capture all leads, contacts, and project activity
6. Contact personas not formalised in the CRM — the framework exists informally but is not structured into the data model

## 4. KPIs — Rep Performance Tracking (Bethany Dunnam)

Bethany walked through how rep performance is currently tracked in Salesforce using a points-based scoring system:

- Reps are measured against a defined set of activities, each carrying a specific weighted score
- The scoring model is activity-based — reps accumulate points by completing specific tasks/interactions
- Each activity type has a defined weight, reflecting its relative importance to the sales process
- This KPI framework is used to track and compare rep performance across the team

> *Full detail of activity types and their respective weights to be captured in the Monday follow-up session.*

## 5. Actions & Next Steps

| # | Action | Owner | Status |
|---|--------|-------|--------|
| 1 | Share contact persona document via email | Bethany Dunnam | Complete |
| 2 | Schedule follow-up call for Monday | Rishi Pankaj | Complete |
| 3 | Call with Bethany to walk through lead-to-sale lifecycle in Salesforce for different customer segments (Distributor, Projects) | Rishi Pankaj | In Progress |
| 4 | Understand the Product Champion incentive structure and workflow in Salesforce | Rishi Pankaj | In Progress |
| 5 | Provide Salesforce access to Rishi | Andy Hehl | In Progress |
