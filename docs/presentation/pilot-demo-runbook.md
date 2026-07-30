# Smart Ashauri pilot demonstration runbook

**Target duration:** 12–15 minutes

**Pilot boundary:** Kiambu, Murang'a, Nyeri, Kirinyaga and Nyandarua

**Core claim:** explainable decision support with learner ownership and human review—not
official placement.

## 1. Preflight — 10 minutes before presenting

From the repository root:

```powershell
cd backend
.\venv\Scripts\python.exe manage.py migrate --settings=config.settings.presentation
$pilotDemoCredential = Get-Credential -UserName "pilot-demo" -Message "Enter the temporary demo password"
$env:PILOT_DEMO_PASSWORD = $pilotDemoCredential.GetNetworkCredential().Password
.\venv\Scripts\python.exe manage.py seed_pilot_demo --settings=config.settings.presentation
Remove-Item Env:PILOT_DEMO_PASSWORD
.\venv\Scripts\python.exe manage.py runserver --settings=config.settings.presentation
```

The presentation profile uses `backend/pilot_demo.sqlite3`, which is ignored by Git.
It avoids external MySQL, email and object-storage credentials and persists between
the three commands above. It also disables IP login throttling locally so one presenter
can switch through all five roles; development and production limits are unchanged.
Delete that local database only when an intentional clean rehearsal dataset is required;
the normal seed command is idempotent.

In a second terminal:

```powershell
cd frontend
npm run dev
```

Then verify:

- [ ] `http://localhost:8000/health/` returns `{"status":"ok"}`.
- [ ] `http://localhost:5173/` loads without a console error.
- [ ] The temporary password is available privately to the presenter.
- [ ] Browser zoom starts at 100%.
- [ ] DevTools is closed unless demonstrating responsive/network behavior.
- [ ] Downloads folder is writable for the PDF.
- [ ] Use a fresh private browser session for each presenter-run rehearsal.

Account emails and their seeded states are in
[pilot-test-accounts.md](./pilot-test-accounts.md). The password is never stored there.

## 2. Timed 12–15 minute story

### 0:00–1:30 — Establish the problem and boundary

Open `/`, then `/pathways`.

Say:

- “This is a final-project pilot in five counties.”
- “It structures evidence, interests, available combinations and human support.”
- “It does not predict success or make official placement decisions.”

Show the pilot notice, pathway explanation and public “how it works” language.

### 1:30–6:30 — Learner journey

Sign in as `learner.ready@demo.smartashauri.test`.

1. Dashboard: point to the single next action and real evidence/plan metrics.
2. Grades (`/grades`): select one seeded subject, then show its Grade 9 performance
   level, school source and verification.
3. Results (`/assessment/results`): show the Holland interest profile, explanation,
   version and limitation language.
4. Explorer (`/explore`): filter school-available combinations and open details.
5. Compare (`/compare`): show saved alternatives and one provisional choice.
6. Plan (`/plan`): show the learner reason, completed/open milestones and reviewed state.
7. Download the PDF and point out evidence sources, versions and advisory disclaimer.

Key line: “The system makes the reasoning inspectable; it does not turn an interest score
into a placement verdict.”

### 6:30–8:00 — Parent support without taking ownership

Sign out, then sign in as `parent@demo.smartashauri.test`.

Open the linked child from the dashboard. Show:

- learner-approved access;
- the support summary and next milestone;
- read-only provisional direction;
- no control to replace the learner's choice.

Key line: “The parent can support the process, but the learner owns the choice.”

### 8:00–10:30 — Counsellor attention and follow-up

Sign out, then sign in as `counsellor.one@demo.smartashauri.test`.

1. Dashboard: show that Brian appears because a plan is ready for review—not because a
   simplistic quiz flag labelled the learner “at risk”.
2. Open the learner record.
3. Show assessment/evidence context, provisional choice and the open intervention.
4. Show how a note or follow-up is recorded.

Key line: “Attention reasons are specific and actionable, and the review remains visible.”

### 10:30–12:00 — School operations

Sign out, then sign in as `school.admin@demo.smartashauri.test`.

Show:

- real membership/assignment counts;
- counsellor management;
- the Kiambu school's active combinations under `/admin/offerings`;
- that school offerings constrain the learner explorer.

Key line: “School data changes what is practically available without changing the national
framework catalogue.”

### 12:00–13:30 — Pilot governance

Sign out, then sign in as `system.admin@demo.smartashauri.test`.

Show:

- five-county health metrics;
- schools/users;
- active framework and combinations;
- audit events for school setup, provisional choice and plan review.

Key line: “The pilot can be monitored and audited without presenting activity metrics as
educational outcomes.”

### 13:30–15:00 — Close honestly

Open or present
[pilot-limitations-and-future-work.md](./pilot-limitations-and-future-work.md).

Close with:

“Smart Ashauri helps learners make a more informed, explainable and supported provisional
choice. People remain responsible for the decision, and official policy remains the
authority.”

## 3. Recovery paths

| Problem | Recovery |
|---|---|
| Login fails | Rerun `seed_pilot_demo --settings=config.settings.presentation` with the same temporary password; the command is idempotent. |
| API is unavailable | Confirm backend terminal, then open `/health/`; use the visible retry action after recovery. |
| Old frontend is shown | Hard refresh once; if an update banner appears, apply it. |
| Network drops during assessment | Show the offline banner and saved draft; reconnect before submitting. |
| A role page is empty | Confirm the correct seeded email, then return to `/` and use the dashboard action. |
| PDF does not open automatically | Use the browser download list; do not regenerate database data mid-demo. |
| Time is running short | Keep learner → counsellor → governance; describe parent/school screens in one sentence each. |

## 4. Manual quality matrix

Complete this on desktop and at 360px before the final presentation.

| Check | Public | Learner | Parent | Counsellor | School admin | System admin |
|---|---:|---:|---:|---:|---:|---:|
| Keyboard-only path and visible focus | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Logical focus order after navigation/dialog | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 200% browser zoom | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 360px width, no blocked action | [x] | [x] | [x] | [x] | [x] | [x] |
| No critical console errors | [x] | [x] | [x] | [x] | [x] | [x] |
| No failed main-flow API requests | N/A | [x] | [x] | [x] | [x] | [x] |

Additional checks:

- [ ] Slow mobile throttling keeps the first dashboard action usable.
- [x] Cache Storage contains no authenticated API response.
- [x] Offline banner and assessment-draft recovery are understandable.
- [x] PDF contains the correct learner, evidence, versions and disclaimer.
- [x] Public copy consistently says “pilot” and avoids official-placement claims.

Recorded responsive evidence on 31 July 2026:

- the public site and all five role dashboards were measured at a 360 x 800 CSS-pixel
  viewport with no document-level horizontal overflow and visible primary actions;
- the learner dashboard and grades page were measured at 768 x 1024 with no overflow;
- a 640px CSS viewport, equivalent to the layout width of a 1280px display at 200%,
  showed no clipped learner headings, paragraphs or actions. This is not a substitute
  for the unchecked native browser-zoom row above;
- the grade-history table initially failed at 360px, was corrected in commit `1700fcf`,
  and then verified to scroll inside its 277px wrapper while the document remained
  contained;
- the complete frontend suite and responsive shell/mobile-navigation tests pass.

## 5. Three-rehearsal record

Do not mark a rehearsal complete unless it starts logged out, verifies anonymous state,
and reaches the closing statement without database or code edits. Use a fresh private
session for a presenter-run rehearsal. An automation-controlled rehearsal may use a new
logged-out tab when the anonymous authentication probes and subsequent role changes are
recorded.

| Run | Date/time | Duration | Desktop/360px | Result | Issues and correction |
|---|---|---:|---|---|---|
| 1 | 31 Jul 2026, 00:40 EAT | 13m 49s | Desktop automation | [x] | New logged-out tab; all five roles and public close passed; zero console errors; only expected anonymous auth probes. |
| 2 | 31 Jul 2026, 00:54 EAT | 13m 22s | Desktop automation | [x] | Independent repeat with all recorded checks true; PDF request and audit event passed; no failed authenticated main-flow request. |
| 3 | 31 Jul 2026, 01:08 EAT | 12m 55s | Desktop automation | [x] | Independent repeat with all recorded checks true; no database/code edits; zero console errors. |

The 360px matrix was completed separately across public, learner, parent, counsellor,
school-admin and system-admin surfaces after the timed runs. Slow-network throttling,
native 200% zoom and hands-on keyboard traversal remain unchecked and must be completed
in a presenter-controlled browser before the final presentation.

## 6. Presenter assets

- [Architecture diagram](./pilot-architecture.md)
- [User-flow diagram](./pilot-user-flow.md)
- [Password-safe account reference](./pilot-test-accounts.md)
- [Known limitations and future work](./pilot-limitations-and-future-work.md)
