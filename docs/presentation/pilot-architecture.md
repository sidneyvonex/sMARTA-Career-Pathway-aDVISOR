# Pilot architecture — one-page presentation view

Smart Ashauri is a five-county decision-support pilot. It helps a learner combine
academic evidence, stated interests, available subject combinations and human review.
It does not make placement or eligibility decisions.

```mermaid
flowchart LR
    subgraph Users["Pilot users"]
        L["Learner"]
        P["Parent / guardian"]
        C["Counsellor"]
        S["School administrator"]
        A["System administrator"]
    end

    subgraph Client["React + TypeScript PWA"]
        Public["Public pilot pages"]
        Dash["Role dashboards"]
        Flow["Evidence → interests → compare → plan"]
        SW["Service worker\nApp shell + public framework only"]
    end

    subgraph API["Django REST API"]
        Auth["JWT authentication\nRole + school permissions"]
        Guidance["Guidance services\nFramework, offerings, choices, plans"]
        Support["Support services\nParent access, reviews, notifications"]
        Reports["Versioned PDF report"]
        Audit["Audit events + pilot health"]
    end

    DB[("Relational database\nFive counties")]

    L --> Client
    P --> Client
    C --> Client
    S --> Client
    A --> Client
    Public --> Guidance
    Dash --> Auth
    Flow --> Guidance
    Dash --> Support
    Dash --> Reports
    SW -. "Never caches private APIs" .-> Client
    Auth --> DB
    Guidance --> DB
    Support --> DB
    Reports --> DB
    Audit --> DB
```

## Trust boundaries

- Public framework data may use short-lived network-first caching.
- Authenticated API responses are never placed in runtime Cache Storage.
- Assessment drafts are user-scoped in the browser and expire after seven days.
- Every private route checks authentication and role; school operations also enforce
  school scope and active membership.
- The PDF records evidence sources, framework/instrument/algorithm versions and an
  advisory disclaimer.

## Pilot boundary

The data model and public copy are limited to Kiambu, Murang'a, Nyeri, Kirinyaga and
Nyandarua. The current catalogue is curated and versioned for the final-project pilot,
not represented as a national placement service.

