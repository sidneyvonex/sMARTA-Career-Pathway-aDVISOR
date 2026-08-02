# Smarta Shauri User Manual Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a visually verified, editable Word user manual of approximately 20 pages that documents every Smarta Shauri role, dashboard, frontend route, and major navigation flow with live browser screenshots and annotations.

**Architecture:** Treat browser evidence, written procedures, and document assembly as separate work products. Capture each implemented route into a structured asset inventory, annotate only the controls referenced by the instructions, then assemble those assets into one branded DOCX using explicit Word styles and deterministic page geometry. Render the finished DOCX to PNG pages and revise it until every page is readable and free of layout defects.

**Tech Stack:** Smarta Shauri React/Vite frontend, Django REST backend, in-app Browser control, pilot demonstration seed data, bundled Python runtime with `python-docx` and Pillow, LibreOffice-based DOCX renderer.

## Global Constraints

- Deliver only an editable Microsoft Word document (`.docx`) to the user.
- Target approximately 20 pages; modest expansion is permitted when required for complete coverage and readable screenshots.
- Include every public, authentication, student, parent, counsellor, school-administrator, and system-administrator route defined in `frontend/src/App.tsx`.
- Give substantial coverage to all five authenticated role dashboards.
- Use browser evidence from the live local application for every major page; do not document interface labels from source code alone.
- Use detailed numbered procedures, annotated screenshots, screenshot captions, and `Starting page -> Select control -> Destination page` navigation strips.
- Do not expose passwords, tokens, private notes, or unnecessary personal information in screenshots or prose.
- Use the approved institutional details from `docs/superpowers/specs/2026-08-03-smarta-shauri-user-manual-design.md` exactly.
- Use Smarta Shauri branding: forest green, gold, dark readable text, and the project logo at `frontend/public/logo.png`.
- Base document geometry on `compact_reference_guide`: US Letter portrait, 1-inch margins, 11-point body type, explicit heading/list/table styles, and consistent header/footer furniture.
- Keep browser screenshots, annotation intermediates, and builder scripts local-only; do not commit files under `output/` or filenames containing `-mockup`, `-wireframe`, or `-brainstorm`.
- Preserve all unrelated working-tree changes.

## File Structure

- Create: `output/user-manual/Smarta-Shauri-User-Manual.docx` - final editable deliverable.
- Create: `output/user-manual/assets/raw/<route-id>.png` - unannotated browser captures.
- Create: `output/user-manual/assets/annotated/<route-id>.png` - screenshots with arrows or numbered callouts.
- Create: `output/user-manual/route-inventory.json` - route, role, title, source URL, capture path, and navigation-note inventory.
- Create: `/private/tmp/build_smarta_shauri_manual.py` - local DOCX assembly script, not committed.
- Create: `/private/tmp/smarta-shauri-user-manual-render/` - rendered page PNGs and optional PDF used only for QA.
- Read: `frontend/src/App.tsx` and `frontend/src/components/shell/navItems.tsx` - route and navigation source of truth.
- Read: `docs/presentation/pilot-test-accounts.md` and `backend/accounts/management/commands/seed_pilot_demo.py` - safe role-specific demonstration states.
- Read: `docs/superpowers/specs/2026-08-03-smarta-shauri-user-manual-design.md` - approved content and cover specification.

---

### Task 1: Prepare and verify the live demonstration environment

**Files:**
- Read: `LOCAL_SETUP.md`
- Read: `docs/presentation/pilot-test-accounts.md`
- Read: `backend/accounts/management/commands/seed_pilot_demo.py`
- Create: `output/user-manual/route-inventory.json`

**Interfaces:**
- Consumes: existing presentation settings, pilot SQLite database, demo seed command, frontend route map.
- Produces: a reachable frontend at `http://localhost:5173`, backend at `http://localhost:8000`, safe role accounts, and a complete route inventory used by all capture tasks.

- [ ] **Step 1: Confirm configured runtime paths**

Call the workspace dependency loader and record the bundled Python executable and package paths for later DOCX work.

- [ ] **Step 2: Check the required route and account sources**

Run:

```bash
rg -n "<Route|path=|roles=" frontend/src/App.tsx
sed -n '1,240p' docs/presentation/pilot-test-accounts.md
```

Expected: every route in the approved specification is present and the demonstration account document lists student, parent, counsellor, school-admin, and system-admin users.

- [ ] **Step 3: Verify the backend database state without mutating it**

Run:

```bash
backend/venv/bin/python backend/manage.py check --settings=config.settings.presentation
backend/venv/bin/python backend/manage.py showmigrations --settings=config.settings.presentation
```

Expected: Django system check succeeds and required migrations are marked applied. If the current shell is not using the project root correctly, run the same commands from `backend/` as `venv/bin/python manage.py ...`.

- [ ] **Step 4: Start or reuse the backend and frontend**

Check ports first:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
lsof -nP -iTCP:5173 -sTCP:LISTEN
```

If a service is absent, start it in a persistent terminal session:

```bash
backend/venv/bin/python backend/manage.py runserver 127.0.0.1:8000 --settings=config.settings.presentation
```

```bash
npm run dev -- --host 127.0.0.1
```

Run the frontend command from `frontend/`. Expected: both URLs return a successful response.

- [ ] **Step 5: Seed demonstration data only if required**

If the account source or login check shows missing demo records, use the idempotent seed command with a temporary credential supplied through the environment, never written to the manual or inventory:

```bash
backend/venv/bin/python backend/manage.py seed_pilot_demo --settings=config.settings.presentation
```

Expected: five schools and all demonstration roles exist. Clear the temporary credential environment variable immediately afterward.

- [ ] **Step 6: Create the route inventory**

Create `output/user-manual/route-inventory.json` with one object per route using these required keys:

```json
{
  "id": "student-dashboard",
  "role": "student",
  "path": "/",
  "title": "Student Dashboard",
  "capture": "output/user-manual/assets/raw/student-dashboard.png",
  "navigation": "Sign in as a student -> Dashboard",
  "status": "pending"
}
```

Include all routes from sections 5.1 through 5.6 of the approved specification plus notification, mobile navigation, PWA prompt, report action, loading, empty, error, permission, and not-found states.

- [ ] **Step 7: Verify inventory completeness**

Compare the JSON paths and roles against `frontend/src/App.tsx` and `frontend/src/components/shell/navItems.tsx`. Expected: no frontend route or authenticated dashboard is missing.

### Task 2: Capture public, authentication, and shared-navigation pages

**Files:**
- Modify: `output/user-manual/route-inventory.json`
- Create: `output/user-manual/assets/raw/public-*.png`
- Create: `output/user-manual/assets/raw/auth-*.png`
- Create: `output/user-manual/assets/raw/shared-*.png`

**Interfaces:**
- Consumes: live frontend, signed-out browser state, route inventory.
- Produces: full-page or focused browser captures and verified visible labels for public/authentication/shared UI sections.

- [ ] **Step 1: Connect to the in-app browser and set the capture viewport**

Use the browser runtime, select the default browser for `http://localhost:5173/`, read its complete documentation, open or reuse one tab, and set a desktop viewport near 1440 x 1000 where supported.

- [ ] **Step 2: Capture public pages**

Open and capture `/`, `/about`, `/pathways`, `/how-it-works`, and `/for-schools`. For each route, verify the page heading, identify the control that leads to the next logical page, save the screenshot under `assets/raw/`, and change the inventory status to `captured`.

- [ ] **Step 3: Capture authentication pages**

Open and capture `/login`, `/register`, `/verify-email`, `/forgot-password`, `/reset-password`, and `/accept-invite`. Use empty or safe demonstration form states; never type a credential into a screenshot that will be retained.

- [ ] **Step 4: Record navigation instructions**

For every captured page, record the exact visible button or link labels and a concise navigation strip, for example:

```text
Landing page -> Select "Log in" -> Login page
Login page -> Select "Forgot password?" -> Password recovery page
```

- [ ] **Step 5: Capture shared authenticated controls**

After a safe student login, capture the sidebar, top bar, notification panel, user menu/sign-out control, mobile bottom navigation, and mobile additional-options sheet. If the PWA prompt is available, capture it; otherwise document the availability condition without inventing a screenshot.

- [ ] **Step 6: Verify files and inventory state**

Run:

```bash
find output/user-manual/assets/raw -type f -name '*.png' -size +10k -print
```

Expected: every public, auth, and shared item marked `captured` has a non-empty PNG.

### Task 3: Capture the complete student journey

**Files:**
- Modify: `output/user-manual/route-inventory.json`
- Create: `output/user-manual/assets/raw/student-*.png`

**Interfaces:**
- Consumes: ready-state pilot learner account, live student routes, shared-navigation captures.
- Produces: student dashboard and route evidence covering profile, academic evidence, assessment, exploration, comparison, planning, and parent access.

- [ ] **Step 1: Sign in as the ready-state learner**

Use the documented demonstration student account and keep the credential outside retained screenshots. Confirm that `/` displays the student dashboard and that the role-specific navigation matches `getBaseNavItems('student')`.

- [ ] **Step 2: Capture the student dashboard and profile**

Capture `/` and `/profile`, including the journey status, next action, profile form, and profile-photo control. Record how a student moves from the dashboard to the profile and back.

- [ ] **Step 3: Capture academic pages**

Capture `/grades` and `/education-goals` when the feature flag exposes it. Show the subject/grade history, progress summary, grade-entry entry point, target or goal controls, and successful-action result without changing verified demonstration evidence unnecessarily.

- [ ] **Step 4: Capture assessment pages**

Capture `/assessment` at a representative question and `/assessment/results` with score explanations and pathway recommendations. Document start, answer, next, submit, retake, and results navigation without submitting a destructive retake if existing results would be lost.

- [ ] **Step 5: Capture choice pages**

Capture `/explore` and `/compare`, including filters, offering cards, save/shortlist actions, selected-choice comparison, related routes, and the transitions between explorer and comparison.

- [ ] **Step 6: Capture planning and access pages**

Capture `/plan` and `/access`, including milestones, plan status, review state, parent-link invitation or approval controls, and privacy/permission guidance.

- [ ] **Step 7: Capture one recovery state**

Use a safe route or controlled unavailable state to capture a student-facing empty, error, or not-found screen with its recovery action. Do not alter source code or demonstration data solely to manufacture an error.

- [ ] **Step 8: Verify student coverage**

Compare the student inventory against the ten student navigation entries in `frontend/src/components/shell/navItems.tsx`. Expected: every available student navigation destination and the dashboard has a capture and navigation note.

### Task 4: Capture parent, counsellor, school-admin, and system-admin experiences

**Files:**
- Modify: `output/user-manual/route-inventory.json`
- Create: `output/user-manual/assets/raw/parent-*.png`
- Create: `output/user-manual/assets/raw/counsellor-*.png`
- Create: `output/user-manual/assets/raw/school-admin-*.png`
- Create: `output/user-manual/assets/raw/system-admin-*.png`

**Interfaces:**
- Consumes: role-specific pilot accounts and records.
- Produces: every non-student dashboard and management route required by the approved specification.

- [ ] **Step 1: Capture the parent experience**

Sign in as the pilot parent and capture the parent dashboard plus `/parent/child/:id`. Record how the parent selects a linked learner, interprets progress, views career/planning information, and returns to the dashboard.

- [ ] **Step 2: Capture the counsellor dashboard and caseload**

Sign in as the first pilot counsellor and capture `/`, `/counselor/students`, `/counselor/students/:id`, and `/counselor/notes`. Include attention reasons, filters, learner evidence, intervention notes, save outcomes, permissions, and return navigation.

- [ ] **Step 3: Capture the school-administrator experience**

Sign in as the pilot school administrator and capture `/`, `/admin/students`, `/admin/counselors`, `/admin/offerings`, and `/admin/school`. Include learner approval/status controls, counsellor management, school offerings, school identity/logo controls, and dashboard navigation.

- [ ] **Step 4: Capture the system-administrator experience**

Sign in as the pilot system administrator and capture `/`, `/system-admin/schools`, `/system-admin/users`, `/system-admin/catalogue`, and `/system-admin/audit-log`. Include search/filter controls, detail drawers, activation states, catalogue version/combinations, audit-event inspection, and dashboard navigation.

- [ ] **Step 5: Capture report entry points**

Where a learner detail or dashboard exposes a report view/download action, capture the initiating screen and record the expected file or browser outcome. Do not include a generated report containing sensitive information unless it is safe pilot data and necessary for the explanation.

- [ ] **Step 6: Verify all dashboard and role routes**

Expected capture count: five role dashboards plus every non-student role route from the approved specification. Cross-check the inventory against `frontend/src/App.tsx`; resolve every `pending` role-route item.

### Task 5: Annotate screenshots and draft the route-by-route content

**Files:**
- Read: `output/user-manual/route-inventory.json`
- Create: `output/user-manual/assets/annotated/<route-id>.png`
- Create: `/private/tmp/smarta-shauri-user-manual-content.md`

**Interfaces:**
- Consumes: raw screenshots, verified visible labels, approved document structure.
- Produces: annotated figures and complete manual copy ready for Word assembly.

- [ ] **Step 1: Select the screenshot set used in the manual**

Choose at least one screenshot for every dashboard and enough supporting screenshots to name every route. Prefer cropped, legible images over shrinking full-page captures. Record any route grouped with a related route in the content draft.

- [ ] **Step 2: Add arrows or numbered markers**

Use Pillow with high-contrast green/gold outlines, readable marker numbers, arrowheads, and a small legend when more than three controls are annotated. Save annotated copies without modifying raw captures.

- [ ] **Step 3: Draft public and account-access procedures**

Write the cover data, introduction, system requirements, public-page descriptions, registration, login, verification, invitation, password reset, shared navigation, notifications, and sign-out procedures.

- [ ] **Step 4: Draft student procedures**

For every student route, write purpose, how-to-reach strip, numbered steps, expected result, notes, and next destination. Use exact visible labels from browser evidence.

- [ ] **Step 5: Draft parent and counsellor procedures**

Explain linked-learner access, progress interpretation, caseload filtering, learner review, note creation/editing, attention handling, report access, and return navigation.

- [ ] **Step 6: Draft administration procedures**

Explain school administration and system administration pages, including safe management actions, permission boundaries, confirmation dialogs, search/filter use, detail drawers, and audit review.

- [ ] **Step 7: Draft quick-reference material**

Add common end-to-end flows, troubleshooting, a role-to-route navigation reference, glossary, privacy guidance, and help/escalation advice.

- [ ] **Step 8: Audit content completeness**

Search the draft for every route title and path from the inventory. Expected: every inventory item is resolved, every section is complete, and no unsupported feature claim remains.

### Task 6: Assemble the editable Word manual

**Files:**
- Create: `/private/tmp/build_smarta_shauri_manual.py`
- Create: `output/user-manual/Smarta-Shauri-User-Manual.docx`
- Read: `frontend/public/logo.png`
- Read: `output/user-manual/assets/annotated/*.png`
- Read: `/private/tmp/smarta-shauri-user-manual-content.md`

**Interfaces:**
- Consumes: approved copy, annotated figures, logo, compact-reference design tokens.
- Produces: complete editable DOCX with semantic styles, captions, navigation, and approximately 20 pages.

- [ ] **Step 1: Load the bundled document runtime**

Use the paths returned by the workspace dependency loader. Confirm imports for `docx` and `PIL` with that runtime; do not use system Python or repo-local package installations for document creation.

- [ ] **Step 2: Define exact document tokens in the builder**

Encode US Letter portrait, 1-inch margins, 11-point body type, heading sizes, paragraph rhythm, list indents, table cell margins, forest-green/gold brand overrides, footer distance, caption styling, and image-width limits before adding content.

- [ ] **Step 3: Build the cover and front matter**

Add the project logo, approved university hierarchy, manual title, subtitle, student/course/supervisor details, submission date, document-purpose statement, version line, and a table of contents or static contents list.

- [ ] **Step 4: Build role sections**

Convert the content draft into real Word Heading 1/2/3 styles, real numbered lists, navigation strips, figure captions, note/warning callouts, and route-reference tables. Keep each screenshot with its caption and nearby explanation.

- [ ] **Step 5: Add headers, footers, and internal navigation**

Add a restrained running title, section/role label where reliable, page number fields, and internal links from the contents list to role sections. Ensure the first-page cover has appropriate distinct furniture.

- [ ] **Step 6: Save and structurally audit the DOCX**

Run the document skill's heading, image, table-geometry, and accessibility audits. Expected: valid heading hierarchy, alt text for every screenshot, no fake bullets, consistent table widths, and no missing image relationships.

### Task 7: Render, inspect, revise, and deliver

**Files:**
- Modify: `output/user-manual/Smarta-Shauri-User-Manual.docx`
- Create: `/private/tmp/smarta-shauri-user-manual-render/page-*.png`

**Interfaces:**
- Consumes: assembled DOCX and document-skill renderer.
- Produces: final, visually verified editable manual.

- [ ] **Step 1: Render the DOCX to page images**

Run with the bundled Python runtime and stable macOS temporary directory:

```bash
env TMPDIR=/private/tmp <bundled-python> /Users/bensidney/.codex/plugins/cache/openai-primary-runtime/documents/26.802.11031/skills/documents/render_docx.py output/user-manual/Smarta-Shauri-User-Manual.docx --output_dir /private/tmp/smarta-shauri-user-manual-render --emit_pdf
```

Expected: one PNG per page and a non-empty PDF used only for QA.

- [ ] **Step 2: Verify the page count**

Run:

```bash
find /private/tmp/smarta-shauri-user-manual-render -name 'page-*.png' | wc -l
```

Expected: approximately 20 pages, with modest expansion allowed for readability and complete route coverage.

- [ ] **Step 3: Inspect every rendered page at full detail**

Open each page PNG and check cover hierarchy, contents, screenshot legibility, arrows, captions, heading consistency, list alignment, table wrapping, page breaks, headers, footers, and page numbers. Record every defect before editing.

- [ ] **Step 4: Revise and re-render**

Fix all clipping, overlap, cramped text, orphaned captions, oversized screenshots, blank gaps, or inconsistent spacing in the builder or DOCX. Regenerate the DOCX and repeat the render cycle after every meaningful batch until all pages pass.

- [ ] **Step 5: Run final structural and accessibility checks**

Run the document skill's accessibility audit and inspect the final archive for incomplete markers or leaked credentials. Expected: no incomplete marker, password, token, or internal citation marker; every figure has useful alt text; all dashboard sections are present.

- [ ] **Step 6: Verify the final deliverable**

Confirm that `output/user-manual/Smarta-Shauri-User-Manual.docx` opens, is non-empty, remains editable, and corresponds to the latest inspected render. Deliver only this DOCX unless the user later requests the QA PDF.
