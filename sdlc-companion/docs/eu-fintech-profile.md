# EU-Regulated Fintech — Current Profile Rules

> **Status:** descriptive reference. This documents the rules that **already
> ship** in the `eu-fintech` Company Profile
> (`sdlc-companion/backend/data/profiles/eu-fintech.json`). It is not a change —
> it's a readable snapshot of the current tech radar and compliance constraints.
> Keep this in sync if the JSON changes.

Profile id: **`eu-fintech`** · name: **"EU-Regulated Fintech"**

---

## 1. Purpose & scope

A Company Profile is the org-specific grounding the pipeline reasons against. It
has two parts:

- a **tech radar** — approved technologies per category, each on a ring
  (Adopt / Trial / Hold), and
- **compliance rules** — `COMP-*` constraints, each hard or soft.

The `eu-fintech` profile models a European, regulated financial-services shop:
EU data residency, no customer data to third parties, immutable audit logs,
encryption everywhere, and a preference for managed services.

---

## 2. How this profile drives the gates

Stage 3 (Stack / ADR) has two **hard, deterministic** gate dimensions that read
this profile directly (`engines/structural.py`):

- **Radar-compliance** (`radar_compliance`) — every technology chosen in an ADR
  must be on the radar and **not Hold**. The Stack Advisor
  (`agents/stack_advisor.py`) only picks from the radar, prefers Adopt over
  Trial, and **escalates rather than silently choosing** a Hold/off-radar item.
- **Compliance-satisfaction** (`compliance_satisfaction`) — every **hard**
  `COMP-*` rule must be satisfied by at least one ADR.

Ranking/selection logic lives in `profile/retriever.py`: Hold entries are
excluded from candidates and Adopt is ranked ahead of Trial.

---

## 3. Tech radar (current)

Transcribed verbatim from `eu-fintech.json`, grouped by category.

### Languages
| Technology | Ring | Notes |
|---|---|---|
| Python | Adopt | primary backend language |
| Go | Trial | for high-throughput services |
| Rust | Hold | not enough in-house expertise |

### Backend frameworks
| Technology | Ring | Notes |
|---|---|---|
| FastAPI | Adopt | team standard |
| Django | Adopt | for admin-heavy apps |
| Flask | Trial | legacy only |

### Frontend
| Technology | Ring | Notes |
|---|---|---|
| React | Adopt | team standard |
| Vue | Trial | isolated apps only |
| Angular | Hold | being phased out |

### Datastore
| Technology | Ring | Notes |
|---|---|---|
| PostgreSQL | Adopt | managed, EU region pinned |
| MySQL | Trial | legacy systems |
| DynamoDB | Hold | data residency concerns |
| MongoDB | Hold | not approved for PII |

### Cloud
| Technology | Ring | Notes |
|---|---|---|
| AWS (eu-central) | Adopt | EU region mandatory |
| GCP | Trial | analytics workloads only |
| Azure | Hold | no contract |

### Auth
| Technology | Ring | Notes |
|---|---|---|
| OAuth2 / OIDC | Adopt | standard |
| Auth0 | Adopt | managed identity |
| Custom JWT | Trial | discouraged |

### Messaging
| Technology | Ring | Notes |
|---|---|---|
| RabbitMQ | Adopt | managed broker |
| Kafka | Trial | high-volume events |
| AWS SQS | Trial | simple queues |

### Cache
| Technology | Ring | Notes |
|---|---|---|
| Redis | Adopt | managed ElastiCache |

### Realtime
| Technology | Ring | Notes |
|---|---|---|
| WebSocket (managed) | Adopt | self-hosted gateway |
| Firebase Realtime DB | Hold | data leaves EU / third-party |

---

## 4. Compliance rules (current)

| ID | Rule | Scope | Constraint |
|---|---|---|---|
| COMP-1 | All PII must be stored and processed in the EU region | data-residency | **hard** |
| COMP-2 | No third-party LLM or SaaS may receive customer data | data-sharing | **hard** |
| COMP-3 | Every data mutation must be written to an immutable audit log | auditability | **hard** |
| COMP-4 | Data must be encrypted at rest and in transit | security | **hard** |
| COMP-5 | Prefer managed services to reduce operational risk | operations | soft |

Only the **hard** constraints (COMP-1…COMP-4) gate Stage 3; COMP-5 is a
preference that informs but does not block.

---

## 5. Ring legend

| Ring | Meaning in this system |
|---|---|
| **Adopt** | Approved and preferred; the Stack Advisor picks these first. |
| **Trial** | Allowed with a caveat + a named Adopt fallback + a risk note. |
| **Hold** | Not allowed; excluded from candidates. Choosing one is escalated, never silently written into an ADR. |
