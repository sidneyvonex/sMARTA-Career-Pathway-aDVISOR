# Smarta Shauri Five-County Pilot Product Specification

> **Audit status (2026-07-31):** This specification records intended pilot
> behavior. It must not be treated as evidence that the behavior exists or that
> its education-policy claims are current. The audit will verify implementation
> against `main` and policy claims against authoritative sources.

**Date:** 2026-07-30  
**Status:** Execution baseline for the final-project pilot  
**Pilot counties:** Kiambu, Murang'a, Nyeri, Kirinyaga, Nyandarua  
**Primary goal:** Demonstrate a correct, safe, practical and visually coherent learner-to-school career-guidance workflow.

## 1. Product outcome

Smarta Shauri will be presented as an evidence-backed Senior School exploration and planning platform for a five-county pilot. It will not claim to perform official placement, predict learner success or replace a qualified counsellor.

The pilot is successful when a learner can:

1. Create a profile.
2. Record subjects and academic evidence correctly.
3. Complete an interest assessment.
4. Understand separate interest-alignment and academic-readiness evidence.
5. Compare Senior School pathways, tracks and a curated set of subject combinations.
6. Select a provisional combination.
7. Create a practical plan with a next step.
8. Share or review that plan with a parent and counsellor.

School staff must be able to onboard, assign and support the learner. System administrators must be able to manage the five-county pilot and inspect important activity.

## 2. Fixed pilot decisions

These decisions prevent the final project from expanding into a national production programme.

- Keep the existing five counties.
- Keep Grades 9 and 10.
- Use the existing Django REST Framework, React, TypeScript and React Query architecture.
- Keep the current roles: student, parent, counsellor, school administrator and system administrator.
- Keep the current public pages and authenticated shell.
- Extend existing models and APIs where possible.
- Use a curated, source-dated pilot catalogue of Senior School pathways, tracks and combinations.
- Seed at least one demonstration school in each pilot county.
- Allow a school administrator to select which seeded combinations the school offers.
- Treat learner-entered academic information as self-reported unless a school administrator marks it verified.
- Present RIASEC as an interest-exploration input, not an outcome prediction.
- Use deterministic eligibility and explanation rules.
- Cache public/reference content only. Do not build private offline mutation synchronization for the pilot.

## 3. Explicitly out of scope

- Expansion to all 47 counties.
- Official Ministry, KNEC or KUCCPS API integration.
- Recreating official placement or KJSEA pathway-strength calculations.
- AI career coach.
- USSD.
- WhatsApp integration.
- M-Pesa and paid subscriptions.
- Mentorship marketplace.
- Scholarship/opportunity marketplace.
- Predictive learner-risk or success models.
- Full legal guardian identity verification.
- National catalogue completion if it threatens pilot completion.
- Complex two-way offline conflict resolution for private data.

These can appear as future-work items in the presentation.

## 4. Design direction

All public and authenticated experiences must use the design language already established by the redesigned public pages and the lively student dashboard.

### Design characteristics

- Warm cream application background.
- Forest-green primary surfaces.
- Marigold/gold primary calls to action.
- Flame accent used sparingly for emphasis.
- Poppins display typography and DM Sans body typography.
- Rounded but not childish cards.
- Illustrated people and landscape motifs where they improve comprehension.
- Purposeful charts; no decorative or misleading percentages.
- Clear empty, loading, error and retry states.
- Minimum 44px interactive targets.
- Keyboard focus visibility.
- Reduced-motion behavior.
- Responsive card layouts; tables convert to cards or deliberate horizontal-scrolling layouts on small screens.

### Shared authenticated page pattern

Every role dashboard and management page should reuse:

1. Role-aware hero/header.
2. One primary "next action" or operational priority.
3. Compact status metrics.
4. Action-oriented content cards.
5. Contextual empty state.
6. Activity/help area.
7. Consistent skeleton, error panel and retry action.

Create shared primitives rather than copying the student dashboard:

- `DashboardHero`
- `MetricCard`
- `SectionHeader`
- `ActionCard`
- `StatusBadge`
- `EmptyState`
- `ErrorState`
- `LoadingSkeleton`
- `ResponsiveDataList`
- `ProgressSteps`
- `EvidenceCard`
- `ActivityList`

## 5. Terminology

Use:

- Competency-Based Education (CBE) for the wider system.
- CBC only when referring to the curriculum.
- Senior School.
- Pathway, track and subject combination as separate entities.
- Interest alignment instead of pathway match.
- Academic readiness instead of success probability.
- Suggested for exploration instead of recommended placement.
- Provisional choice instead of final choice.

Avoid:

- "You are 87% STEM."
- "Guaranteed pathway."
- "Best career for you."
- "Official placement result."
- "At-risk learner" without a visible, specific reason.

## 6. Information architecture

### Public

- Home
- About
- Pathways
- How It Works
- For Schools
- Sign In
- Create Account

The Pathways page becomes a public, source-dated overview of pathways and tracks. Detailed learner-specific comparison remains authenticated.

### Student

- Home
- My Evidence
  - Profile
  - Subjects and academic evidence
  - Interests and preferred activities
- Explore
  - Pathways and tracks
  - Subject combinations
  - Compare
- My Plan
- Assessment
- Report
- Support and access

For the pilot, existing `/profile`, `/grades` and `/assessment` routes can remain, but navigation labels and cross-links should make them feel like one evidence flow.

### Parent

- Home
- Child detail
- Child plan
- Support actions
- Access information
- Report

### Counsellor

- Home
- Caseload
- Learner detail
- Interventions/notes
- Follow-ups
- Reports

### School administrator

- Home
- Students
- Counsellors
- Assignments
- School profile
- School offerings
- Cohort progress

### System administrator

- Home
- Schools
- Users
- Framework catalogue
- Audit activity
- Pilot health

## 7. Core learner flow

### 7.1 Registration and onboarding

1. Learner chooses self-guided or school-linked.
2. Learner enters minimum account details and one of the five counties.
3. School-linked learner supplies a valid active-school code.
4. The interface explains that school membership is pending approval.
5. Learner verifies email.
6. The dashboard directs the learner to the next incomplete evidence step.

Required pilot safeguards:

- Child-friendly data-use notice.
- Clear explanation of who can access school-linked information.
- Active-school validation.
- Pending/approved/rejected school-link status.
- Shared-device warning on login and logout.

### 7.2 My Evidence

Evidence is shown in three separate groups:

- Academic evidence.
- Interest evidence.
- Preferences, goals and activities.

Academic evidence records:

- Learning area/subject.
- Grade.
- Term and year.
- Performance level.
- Source: learner-entered or school-verified.
- Verification timestamp and verifier when applicable.

Correct level ordering:

1. EE1
2. EE2
3. ME1
4. ME2
5. AE1
6. AE2
7. BE1
8. BE2

Charts may show ordered bands or points labelled as a visualization aid. They must not invent percentages.

### 7.3 Interest assessment

- Keep the existing 30-question RIASEC assessment.
- Store an assessment/instrument version.
- Store drafts under a user-scoped key.
- Explain the purpose before starting.
- Explain that interests can change and are only one input.
- Show ordinary-language dimension names and examples.
- Retain technical RIASEC codes as secondary information.

### 7.4 Guidance results

The result screen has four panels:

1. **Interest profile** - strongest interest themes.
2. **Pathways to explore** - RIASEC-based interest alignment, labelled clearly.
3. **Academic readiness** - separate evidence status for pathway-relevant subjects.
4. **Next step** - compare combinations, add missing evidence or request counsellor review.

Do not combine interest and grades into one unexplained percentage.

Each pathway explanation includes:

- Why it appeared.
- Supporting interest evidence.
- Supporting academic evidence.
- Missing or weak evidence.
- Relevant tracks.
- Alternative pathway.
- Source/version date.

### 7.5 Combination explorer

The pilot catalogue supports:

- Pathway.
- Track.
- Official or curated source code.
- Three elective subjects.
- Short description.
- Related careers/routes.
- Source URL and effective date.
- Active/inactive state.
- Schools in the pilot that offer it.

Learners can:

- Filter by pathway, track and pilot county.
- Save up to three combinations.
- Compare saved combinations.
- See structural validity separately from readiness.
- Select one provisional combination.

### 7.6 My Plan

The plan records:

- Provisional pathway.
- Provisional track.
- Provisional subject combination.
- Learner reason.
- Evidence gaps.
- Up to five milestones.
- Owner for each milestone: learner, parent or counsellor.
- Target date.
- Status.
- Last reviewed date.

Minimum milestones:

- Complete missing evidence.
- Compare at least two combinations.
- Discuss with parent/guardian.
- Review with counsellor.
- Check schools offering the preferred combination.

## 8. Parent flow

1. Learner invites a parent.
2. Parent accepts and states relationship.
3. Link remains pending until learner confirms access.
4. Learner can see and revoke the link.
5. Parent dashboard shows:
   - learner's current next step;
   - provisional pathway/combination;
   - milestones;
   - suggested conversation prompt;
   - report action.

Pilot limitation:

- The system records claimed relationship and learner approval.
- It must not claim that the adult's legal guardian identity was independently verified.

Parent-visible counsellor notes remain explicit. Private and safeguarding notes are not shown.

## 9. Counsellor flow

Counsellor priorities use explicit reasons:

- No assessment.
- Missing academic evidence.
- No provisional plan.
- Invalid/unavailable combination.
- Learner requested review.
- Follow-up overdue.

Counsellor actions:

1. Open caseload.
2. Filter by reason.
3. Review learner evidence and saved combinations.
4. Record intervention/note.
5. Agree a next step.
6. Set follow-up date.
7. Mark intervention complete.

The pilot does not calculate a predictive risk score.

## 10. School-administrator flow

1. Review school profile and active status.
2. Configure offered combinations from the curated pilot catalogue.
3. Review pending school-link requests.
4. Approve or reject learner membership.
5. View students and assignment status.
6. Assign or unassign counsellors.
7. View cohort completion:
   - evidence started;
   - assessment complete;
   - combination saved;
   - plan created;
   - counsellor review complete.

CSV import is a should-have for the pilot. If schedule pressure is high, present it as a validated import preview using a small template rather than building a full school MIS integration.

## 11. System-administrator flow

System administrator can:

- See pilot totals by the five counties.
- Manage schools and activation.
- Manage users and activation.
- Manage the curated pathway/track/combination catalogue.
- Inspect source/effective-date metadata.
- Review important audit events.
- See pilot health:
  - registered learners;
  - verified learners;
  - active schools;
  - plans completed;
  - pending school links;
  - counsellor assignment coverage.

## 12. Pilot data model

### Extend existing

- `School`
  - retain county and active state;
  - add relationship to offered combinations.
- `StudentProfile`
  - add school-link status;
  - add onboarding completion state if derived state becomes too costly.
- `CBCGrade`
  - add source and verification metadata.
- `RIASECAssessment`
  - add instrument version.
- `Recommendation`
  - retain ranking but expose it as interest alignment;
  - add algorithm/framework version and explanation snapshot.
- `ParentStudentLink`
  - add relationship, learner approval, status and revoked timestamp.
- `CounselorNote`
  - add category and follow-up date if intervention workflow is implemented.
- `AuditLog`
  - add sensitive action types and object metadata.

### Add

- `FrameworkVersion`
- `PathwayTrack`
- `SubjectCombination`
- `SchoolOffering`
- `LearnerCombinationChoice`
- `LearnerPlan`
- `PlanMilestone`

Keep models narrow. Do not create a generic content-management system for the pilot.

## 13. API additions and changes

### Public/reference

- `GET /api/v1/guidance/framework/current/`
- `GET /api/v1/guidance/pathways/`
- `GET /api/v1/guidance/combinations/`
- `GET /api/v1/guidance/combinations/{id}/`

### Student

- `GET /api/v1/students/evidence-summary/`
- `GET /api/v1/students/grades/summary/`
- `GET|POST /api/v1/students/combination-choices/`
- `DELETE /api/v1/students/combination-choices/{id}/`
- `GET|PUT /api/v1/students/plan/`
- `POST|PATCH|DELETE /api/v1/students/plan/milestones/`
- `GET /api/v1/students/access/`
- `POST /api/v1/students/access/{link_id}/approve/`
- `POST /api/v1/students/access/{link_id}/revoke/`

### Parent

- Extend child detail with learner-approved plan summary.
- Add explicit access-status endpoint or include status in existing child response.

### Counsellor

- Extend student list with `attention_reasons`.
- Extend student detail with evidence, saved combinations and plan.
- Add intervention/follow-up fields through the existing notes domain where practical.

### School administrator

- `GET|PUT /api/v1/school-admin/offerings/`
- `GET /api/v1/school-admin/link-requests/`
- `POST /api/v1/school-admin/link-requests/{id}/approve/`
- `POST /api/v1/school-admin/link-requests/{id}/reject/`
- Extend stats with pilot journey completion.

### System administrator

- Framework catalogue CRUD for the curated pilot set.
- Extend dashboard stats with pilot journey metrics.

Every new endpoint must use the existing response envelope and role/object permissions.

## 14. Offline and PWA policy

For the pilot:

- Precache the application shell and public assets.
- Cache public framework endpoints with explicit versioned cache names.
- Do not cache authenticated API endpoints through Workbox.
- Keep assessment draft locally under a user-specific key with expiry.
- Clear private local state on logout.
- Show a clear offline indicator.
- Disable network-required submissions with a helpful recovery message.

Do not claim that the complete product works offline. State that public/reference content and in-progress assessment answers have limited offline support.

## 15. Reports

The learner report contains:

- Learner and school identity.
- Evidence-source labels.
- Interest profile.
- Pathways to explore.
- Academic readiness summary.
- Saved/provisional combination.
- Plan milestones.
- Framework and algorithm version.
- Generated date.
- Clear advisory disclaimer.

It must not contain a success probability or imply official placement.

## 16. Presentation demo script

The final demonstration should use seeded data and follow one learner across roles:

1. Public visitor opens the redesigned home and pathways pages.
2. Grade 9 learner in Kiambu registers or signs in.
3. Learner sees one next action.
4. Learner adds academic evidence.
5. Learner completes or reviews the interest assessment.
6. Results show interest alignment and academic readiness separately.
7. Learner compares two combinations and saves one provisionally.
8. Learner creates a milestone plan.
9. Parent sees an approved summary and conversation prompt.
10. Counsellor sees the learner's review request, adds an intervention and follow-up.
11. School administrator sees cohort progress and assignment.
12. System administrator sees five-county pilot health and audit activity.
13. Learner downloads the updated report.
14. Presenter demonstrates mobile responsiveness and explains safe limited offline behavior.

## 17. Pilot definition of done

- All five role dashboards use the same design system.
- Public and authenticated experiences feel like one product.
- Correct performance-level ordering is used everywhere.
- Grade 10 subject content is no longer a duplicate of Grade 9.
- RIASEC result is labelled interest alignment, not predictive match.
- Learner can save and compare combinations.
- Learner can create a provisional plan.
- Parent and counsellor can support the same plan within explicit access rules.
- School admin can approve school links, configure offerings and monitor journey progress.
- System admin can manage and audit the pilot.
- Authenticated API data is not cached by the service worker.
- Main flows work at 360px, tablet and desktop widths.
- Keyboard, focus, reduced-motion and common screen-reader labels are verified.
- Backend tests, frontend tests and production build pass.
- Seed script creates a repeatable demonstration dataset.
- A presentation runbook can complete the full demo without manual database edits.
