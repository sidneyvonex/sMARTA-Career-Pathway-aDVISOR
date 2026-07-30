# Smart Ashauri pilot demonstration runbook

**Target duration:** 12–15 minutes

**Pilot boundary:** Kiambu, Murang'a, Nyeri, Kirinyaga and Nyandarua

**Core claim:** explainable decision support with learner ownership and human review—not
official placement.

## 1. Preflight — 10 minutes before presenting

From the repository root:

```powershell
cd backend
.\venv\Scripts\python.exe manage.py migrate
$pilotDemoCredential = Get-Credential -UserName "pilot-demo" -Message "Enter the temporary demo password"
$env:PILOT_DEMO_PASSWORD = $pilotDemoCredential.GetNetworkCredential().Password
.\venv\Scripts\python.exe manage.py seed_pilot_demo
Remove-Item Env:PILOT_DEMO_PASSWORD
.\venv\Scripts\python.exe manage.py runserver
```

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
- [ ] Use a fresh private browser session for each rehearsal.

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
2. Grades (`/grades`): show Grade 9 performance levels, source and verification.
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
| Login fails | Rerun `seed_pilot_demo` with the same temporary password; the command is idempotent. |
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
| 360px width, no blocked action | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| No critical console errors | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| No failed main-flow API requests | N/A | [ ] | [ ] | [ ] | [ ] | [ ] |

Additional checks:

- [ ] Slow mobile throttling keeps the first dashboard action usable.
- [ ] Cache Storage contains no authenticated API response.
- [ ] Offline banner and assessment-draft recovery are understandable.
- [ ] PDF contains the correct learner, evidence, versions and disclaimer.
- [ ] Public copy consistently says “pilot” and avoids official-placement claims.

## 5. Three-rehearsal record

Do not mark a rehearsal complete unless it starts in a fresh private browser session and
reaches the closing statement without database edits.

| Run | Date/time | Duration | Desktop/360px | Result | Issues and correction |
|---|---|---:|---|---|---|
| 1 | — | — | Desktop | [ ] | |
| 2 | — | — | 360px | [ ] | |
| 3 | — | — | Desktop + slow network sample | [ ] | |

## 6. Presenter assets

- [Architecture diagram](./pilot-architecture.md)
- [User-flow diagram](./pilot-user-flow.md)
- [Password-safe account reference](./pilot-test-accounts.md)
- [Known limitations and future work](./pilot-limitations-and-future-work.md)
