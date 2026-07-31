# Pilot user flow — one-page presentation view

> **Audit status (2026-07-31):** This is the intended user flow. The audit will
> compare every step with the behavior currently implemented on `main` and with
> the verified official Senior School guidance process.

```mermaid
flowchart TD
    Start["Public visitor learns the pilot scope"] --> Login["Learner signs in"]
    Login --> Evidence["Review Grade 9 evidence\nwith source and verification"]
    Evidence --> Interest["Complete or review RIASEC interest assessment"]
    Interest --> Explain["See versioned, non-predictive\ninterest alignment explanation"]
    Explain --> Explore["Explore school-available combinations"]
    Explore --> Compare["Save and compare alternatives"]
    Compare --> Provisional["Choose one provisional combination"]
    Provisional --> Plan["Add reason and milestones"]
    Plan --> Review["Request counsellor review"]

    Review --> Counselor["Counsellor sees an explicit attention reason"]
    Counselor --> Action["Record note / intervention / follow-up"]
    Action --> Reviewed["Plan reviewed with learner"]

    Provisional --> ParentApproval["Learner approves parent access"]
    ParentApproval --> Parent["Parent sees a support summary\nwithout editing the learner's choice"]

    School["School administrator approves membership,\nassigns counsellors and manages offerings"] --> Explore
    Admin["System administrator monitors five-county health,\nframework freshness and audit events"] --> School

    Reviewed --> PDF["Download evidence-backed plan PDF"]
    Parent --> PDF
```

## Decision ownership

| Actor | Can do | Cannot do |
|---|---|---|
| Learner | Own evidence, assessment, saved/provisional choice and plan | Treat interest alignment as placement |
| Parent/guardian | View an approved summary and support next steps | Change the learner's provisional choice |
| Counsellor | Review evidence, document a note/intervention and follow up | Silently decide for the learner |
| School administrator | Manage school membership, assignments and offerings | Access another school's private records |
| System administrator | Monitor pilot health, catalogue status and audit events | Convert the pilot into an official placement decision |
