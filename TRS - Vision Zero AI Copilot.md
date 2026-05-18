# TRS – Vision Zero AI Copilot (POC)

# Purpose

The TRS project aims to build an **AI-powered Vision Zero Copilot** for the City of Toronto. The goal is to assist Vision Zero analysts, planners, and policy teams by enabling **data-grounded answers, reasoning, and recommendations** that are not possible with a generic LLM alone.

This POC focuses on:

- Querying **external structured datasets** (collisions, speed limits, traffic volumes, enforcement data)
- Reasoning over **policy and bylaw text** (e.g., HTA amendments, Toronto bylaws)
- Generating **evidence-backed explanations and recommendations** similar to Vision Zero reports and dashboards

This document serves as the foundation for:

- Project plan & milestones
- User stories for junior engineers
- Architecture and tooling decisions for the POC

---

## Vision Zero (Context)

Vision Zero is a road safety strategy that treats traffic fatalities and serious injuries as **preventable**, not inevitable. Instead of focusing on driver error alone, it emphasizes **system design** that anticipates human mistakes and reduces their consequences.

Typical Vision Zero interventions include:

- Lowering speed limits in school/community safety zones
- No-right-turn-on-red restrictions at high pedestrian conflict intersections
- Automated Speed Enforcement (ASE) deployment
- Road diets (lane reductions)
- Speed humps and raised intersections
- Leading pedestrian intervals (LPIs)
- Protected cycling infrastructure

The TRS Copilot is designed to reason about *why* and *where* these interventions are implemented.

---

## Current Issues Faced by Vision Zero Analysts

### 1. Fragmented Data Sources

- Collision data, traffic volumes, speed limits, and enforcement data live in separate systems
- Analysts manually join datasets for each study or report

### 2. High Effort for Repetitive Analysis

- Common questions require repeated SQL queries, GIS work, and report writing
- Example: *“Why was a speed limit reduced on this corridor?”*

### 3. Observed Limitations of Standalone LLMs (ChatGPT)

During exploratory conversations, several Toronto-specific road safety questions could not be answered accurately using a generic LLM due to lack of access to local datasets, bylaws, and policy history.

Examples of failed or incomplete prompts:

- “Why is right turn on red prohibited at Leona Dr & Sheppard Ave W?”
    
    → LLM could only give generic safety reasons; no intersection-level evidence or bylaw confirmation.
    
- “When was this no-right-turn-on-red rule implemented and under which authority?”
    
    → Requires Toronto bylaw text and council decisions not available to the LLM.
    
- “Why did the City deploy automated speed enforcement only in school and community safety zones?”
    
    → Needs HTA amendments (Bill 65) and municipal policy documents.
    
- “Why was this road designated as a Community Safety Zone?”
    
    → Requires designation data, proximity rules, and enforcement criteria.
    
- “Why was the speed limit reduced on this specific corridor?”
    
    → Requires historical speed limit data and before/after collision analysis.
    

These examples highlight that while LLMs are effective at language generation, they **cannot safely answer Toronto Vision Zero questions without structured data retrieval and policy grounding**, directly motivating the TRS Vision Zero Copilot.

---

## Core Use Cases (POC Scope)

For the initial POC, the system is **explicitly limited** to answering only two categories of questions. This constraint is intentional to keep scope tight, reduce ambiguity, and make evaluation clear.

### Question Types Supported in POC

1. Natural Language (NL) Factual Queries Over External Data
    
    These are questions where the answer exists directly in structured or semi-structured datasets.
    
    Examples:
    
    - “How many pedestrian KSI collisions occurred at this intersection in the last 5 years?”
    - “Is this road designated as a Community Safety Zone?”
    - “What is the posted speed limit on this corridor?”
    
    System behavior:
    
    - Translate NL question into structured intent
    - Query external datasets (SQL / filtered retrieval)
    - Return factual, verifiable answers
    - **No free-form reasoning or speculation**

1. Policy Reasoning Queries (LLM-Assisted)
    
    These are questions asking *why* a rule, restriction, or intervention was implemented.
    
    Examples:
    
    - “Why is right turn on red prohibited at this intersection?”
    - “Why was ASE deployed in this school zone?”
    - “Why was the speed limit reduced on this road?”
    
    System behavior:
    
    - Retrieve relevant collision data, policy text, and bylaws
    - Use the LLM **only for reasoning and explanation**, not fact generation
    - Generate structured, evidence-backed narratives aligned with Vision Zero principles
    
    ---
    
    ---
    
    1. Policy & Infrastructure Reasoning
    
    Examples:
    
    - “Why did the City introduce ASE in school zones?”
    - “What policy enabled municipalities to deploy speed cameras?”
    
    Copilot behavior:
    
    - Retrieve Bill 65 / HTA amendments
    - Link policy text to observed safety outcomes
    - Explain intent vs impact
    
    b. Safety Improvement Suggestions (Decision Support)
    
    Examples:
    
    - “What interventions could reduce speeding on this road?”
    - “Suggest Vision Zero improvements for a high-KSI intersection”
    
    Copilot behavior:
    
    - Analyze collisions + speeds + road context
    - Suggest interventions aligned with Vision Zero principles
    - Cite similar implementations elsewhere
    
    c. Evidence Builder for Reports
    
    Examples:
    
    - “Build evidence supporting a speed limit reduction proposal”
    - “Summarize safety issues for a council briefing”
    
    Copilot behavior:
    
    - Extract relevant stats
    - Structure findings like a Vision Zero memo
    - Reduce analyst time spent on narrative writing

---

### Explicitly Out of Scope (For Now)

- Open-ended planning recommendations
    - Optimization or prediction use cases
    - Real-time enforcement or operational decisioning
    
    These may be considered in later phases but are **not part of the current POC**.
    

## Datasets Used in the POC

### 1. Toronto Police – Killed & Seriously Injured (KSI) Collision Data

**Purpose:** Identify high-risk locations and trends

- Collision location
- Severity (fatal, serious injury)
- Road user type (pedestrian, cyclist, motorist)
- Time and date

Used for:

- Hotspot detection
- Before/after policy analysis

---

### 2. Toronto Traffic Volume Data

**Purpose:** Contextualize collision risk

- Average daily traffic (ADT)
- Turning movement counts

Used for:

- Exposure-based reasoning
- Explaining why certain corridors are prioritized

---

### 3. Toronto Speed Limit Dataset

**Purpose:** Understand regulatory context

- Posted speed limits
- Historical changes (where available)

Used for:

- Explaining speed reductions
- Correlating speed with injury severity

---

### 4. Automated Speed Enforcement (ASE) Locations & Tickets

**Purpose:** Enforcement and compliance analysis

- Camera locations
- Ticket volumes (where available)

Used for:

- Justifying ASE deployment
- Evaluating behavior change

---

### 5. Toronto Road Safety Bylaws & Policy Text (Additional Dataset)

**Purpose:** Policy reasoning and explainability

Includes:

- Toronto Municipal Code chapters (traffic, parking, safety zones)
- Community Safety Zone rules
- No-right-turn-on-red bylaws
- HTA amendments relevant to municipalities (e.g., Bill 65)

Used for:

- Answering *why* a rule exists
- Linking legal authority to on-street changes

---

## Solution Architecture (POC)

### High-Level Flow

1. User asks a natural language question
2. Query is classified:
    - Factual
    - Analytical
    - Policy reasoning
3. Relevant datasets and documents are retrieved (RAG)
4. Structured data is queried (SQL / vector + filters)
5. LLM performs reasoning over retrieved evidence
6. Response is generated with sources and logic

---

## Outcome

By the end of the POC, the TRS Vision Zero Copilot should:

- Answer analyst-grade questions ChatGPT cannot
- Explain *why* safety decisions were made
- Reduce time spent on manual analysis
- Serve as a foundation for production-grade tools