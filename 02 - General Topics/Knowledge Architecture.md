# Knowledge Architecture

> Version 1.0 — figAIro + Obsidian Role Definition
> Module: All | Updated: 2026-04-01

---

## 1. Principle

Two systems, two roles. No overlap in ownership.

- **Obsidian** = Published documentation. Architecture, decisions, references. Shared with humans. Long-form, versioned.
- **figAIro** = Living brain. State, tasks, context, patterns. Queryable, live, auto-maintained.

CLAUDE.md and MEMORY.md are bootstrap pointers — minimal, pointing to Obsidian and figAIro.

---

## 2. What Lives Where

| Content Type | Owner | Why |
|---|---|---|
| Business architecture | Obsidian | Long-form, versioned, shared with team |
| Architectural decisions | Obsidian | Need human-readable record |
| Slide decks | Obsidian | Presentation format, synced to Odoo Knowledge |
| Terminology glossary | Obsidian | Reference material |
| Backlog / tickets | figAIro | Must be live, queryable, linked to work |
| Workstream state | figAIro | Changes every session |
| Session journals | figAIro | Auto-generated on session end |
| Asset registry | figAIro | Auto-built from code analysis |
| Deploy tracker | figAIro | Git SHA to Odoo instance mapping |
| Requirement to task linkage | figAIro | From conversations to actionable items |
| Dependency graph | figAIro | Detected from code + domain logic |
| Odoo 19 gotchas | figAIro | Growing knowledge base, queryable |
| Decisions log | Both | Obsidian for record, figAIro links to it |

---

## 3. Five Systems Today

### 3.1 Obsidian Vault

Location: `/Users/oeb/Documents/Manufacturing Kebony/`

| Folder | Content | Status |
|---|---|---|
| 01 - Terminology | Glossary | Stable |
| 02 - General Topics | Product, Metrics, Pack Reservation, Knowledge Architecture | Active |
| 03 - Manufacturing | Architecture, Dryer-Centric, Kallo Landscape | Active |
| 04 - US Specific | Accounting, Consignment | Active |
| 05 - Working Plan | Backlog, Working Plan | STALE — move backlog to figAIro |
| 06 - Slide Decks | HTML presentations + PDF export | Active |
| 07 - Validation | Test scripts | Active |

**Rule**: Obsidian documents are the definitive reference for business architecture. They answer "what is the design?" not "where are we?"

### 3.2 figAIro (compAnion)

Capabilities needed (Layer 1 — Solo Maker):

| Capability | Status | Description |
|---|---|---|
| Memory (STM/LTM) | Exists | Stores observations, facts, session context |
| Knowledge Graph | Exists | Entities and relationships |
| Workstream State | Missing | Per-workstream: phase, status, blockers, next |
| Session Journal | Missing | Auto-capture on session end: what changed, what's pending |
| Asset Registry | Missing | What models, wizards, views exist per module |
| Deploy Tracker | Missing | What's in code vs what's on which Odoo instance |
| Backlog | Missing | Live task list with priority, dependency, status |
| Requirement Capture | Missing | From conversations/emails to structured requirements |
| Dependency Graph | Missing | A needs B before C — auto-detected |
| Gotchas KB | Partial | Started today with Odoo 19 gotchas |

### 3.3 CLAUDE.md (per repo)

Location: repo root `/.claude/` or repo root

**Role**: Bootstrap context for new Claude sessions. Minimal. Points to Obsidian for architecture, figAIro for state.

**Contains**: repo structure, conventions, field naming rules, entity table, Obsidian vault location, key commands.

**Does NOT contain**: current state, progress, backlog, session history.

### 3.4 CLAUDE MEMORY.md (per project)

Location: `~/.claude/projects/<path>/memory/MEMORY.md`

**Role**: Persistent notes across Claude sessions for a specific project.

**Contains**: workflow notes, cross-repo references, discovered gotchas.

**Limitation**: Static file, not queryable, goes stale.

### 3.5 Git

**Role**: Source of truth for code state. Commits, branches, PRs.

**figAIro should read**: branch state, recent commits, deploy tags to know what's live.

---

## 4. The Invisible PM Loop

```
Requirements (from conversations, emails, meetings, observation)
    |
    v
figAIro captures as structured items
    |
    v
Dependencies detected (from code, domain logic, explicit links)
    |
    v
Plan emerges (PERT ordering, critical path, priorities)
    |
    v
Execution observed (session journals, commits, deployments)
    |
    v
Reporting generated (status, Gantt, burndown for stakeholders)
    |
    v
Retrospective auto-generated (what took longer, why, lessons)
```

Nobody "does project management." The solo maker works. figAIro observes and structures.

---

## 5. Four User Layers

| Layer | User | Experience | Relationship to Plan |
|---|---|---|---|
| 1 | Solo Maker | "Just let me work" — context continuity, session briefing | GENERATES plan data by working |
| 2 | Team (2-5) | "Who's doing what?" — handoffs, coordination | COLLABORATES on the plan |
| 3 | Change Mgmt | "What's the impact?" — dependency graph, risk | VALIDATES changes |
| 4 | Stakeholder | "Where are we, when done?" — dashboards, Gantt | READS the plan |

Layer 1 produces the data that feeds Layers 2, 3, and 4 automatically.

### 5.1 Layer 1 — Solo Maker

The maker just works. figAIro observes and structures.

**figAIro provides**: session briefing on start, context continuity, backlog awareness, asset registry ("this already exists"), deploy state, drift detection.

**figAIro captures**: session journal (auto on end), requirements from conversation, decisions, blockers, gotchas.

**Key principle**: zero overhead. The maker never "updates a plan" — the plan updates itself.

### 5.2 Layer 2 — Team

The team communicates naturally. figAIro participates in the discussion.

**Architecture**: channel-based. figAIro is a first-class participant in team conversations, not a passive observer.

**AI must be IN the conversation** for full automation. Without AI participation, someone must manually translate discussions into tasks. With AI in the channel, capture is live and the plan updates instantly.

**figAIro's role in channels**:
- Captures requirements, decisions, blockers from natural conversation
- Links to existing tasks and dependencies automatically
- Detects conflicts ("this contradicts what Dev 2 said yesterday")
- Pushes updates ("dependency resolved, you can start Z now")
- Generates briefings per person ("your priorities today")

**Three communication modes** in one channel:
- Async (like Slack): most of the time
- Sync (like meeting): when real-time discussion needed
- Briefing (push): daily/weekly summaries per person

**Central figAIro**: hub-and-spoke. Each team member has local figAIro for personal context. Central figAIro aggregates, plans, and distributes.

### 5.3 Layer 3 — Change Management

When a requirement changes or a new one arrives, impact must be assessed before action.

**figAIro provides**:
- Dependency graph: "changing X affects Y and Z"
- Impact analysis: "this adds 3 days to the critical path"
- Risk flags: "this touches a production system — requires sign-off"
- Historical patterns: "last time we changed this area, it took 2 sprints"

**figAIro captures**: change requests, approval decisions, rollback plans.

**Key principle**: change management is not bureaucracy — it's awareness. figAIro makes the impact visible so the team can decide fast.

### 5.4 Layer 4 — Stakeholder

Management and customers want visibility without doing work.

**figAIro generates**:
- Status dashboards (where are we on each workstream)
- Gantt charts (timeline with dependencies)
- Burndown (velocity and predicted completion)
- PERT diagrams (critical path, slack time)
- Executive summaries (natural language, one paragraph)

**Key principle**: all reporting is GENERATED from Layer 1+2 data. No one writes status reports. figAIro composes them from session journals, task completions, and dependency state.

---

## 6. Design Principles

1. **The best PM is invisible** — priorities are natural because of business needs and logical dependencies
2. **Requirements drive plans** — capture requirements, plans emerge from dependencies
3. **The rest is reporting** — once you have requirements + dependencies + execution data, all views (Gantt, burndown, status) are generated
4. **Companies want control + speed** — Agile scares them (when does it end?), PRINCE2 is too heavy. figAIro gives both.
5. **Solo to team is seamless** — same system scales from 1 person to 5 without changing tools
