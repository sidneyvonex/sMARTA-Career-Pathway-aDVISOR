# Smarta Shauri Project Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce an editable, visually verified 17-page Smarta Shauri project documentation report that explains the project in accessible language and ends with selected system screenshots.

**Architecture:** Build the report deterministically with `python-docx`, using six concise narrative pages followed by eleven screenshot-led pages. Reuse only verified screenshots from the existing manual assets, then render the finished Word document and revise it until the page count, typography, image legibility, and content checks all pass.

**Tech Stack:** Microsoft Word `.docx`, Python `python-docx`, Pillow, LibreOffice/Poppler rendering, existing PNG screenshot evidence.

## Global Constraints

- Deliver an editable Microsoft Word `.docx` with exactly 17 pages.
- Use US Letter portrait pages with 1-inch margins.
- Use Times New Roman 12 pt for body text, 1.5 line spacing, and justified paragraphs.
- Use Times New Roman bold for headings; captions and screenshot explanations remain 12 pt.
- Keep the report non-technical: no source code, API detail, database schema, or deployment commands.
- Limit narrative discussion to pages 2-6; place the selected system screenshots on pages 7-17.
- Cover the student, parent, counsellor, school-administrator, and system-administrator roles.
- Use no more than 22 verified screenshots, normally one or two large screenshots per page.
- Include the approved institutional cover details and the date `17 March 2026`.
- Preserve unrelated working-tree files and keep generated output local-only under `output/project-documentation/`.

---

### Task 1: Prepare the document builder and narrative content

**Files:**
- Read: `docs/superpowers/specs/2026-08-04-smarta-shauri-project-documentation-design.md`
- Read: `docs/superpowers/specs/2026-06-14-cbc-career-guidance-system-design.md`
- Read: `output/user-manual/assets/raw/*.png`
- Create: `/private/tmp/build_smarta_shauri_project_documentation.py`

**Interfaces:**
- Consumes: the approved 17-page specification, verified project facts, and existing screenshot inventory.
- Produces: a deterministic builder containing the complete page structure, prose, styles, image mappings, headers, footers, and explicit page breaks.

- [ ] **Step 1: Confirm the approved source material**

Run:

```bash
test -f docs/superpowers/specs/2026-08-04-smarta-shauri-project-documentation-design.md
test -f output/user-manual/assets/raw/student-dashboard.png
test -f output/user-manual/assets/raw/system-admin-dashboard.png
```

Expected: all commands exit successfully.

- [ ] **Step 2: Define the Word styles and page helpers**

Create helpers that set US Letter portrait geometry, 1-inch margins, Times New Roman body styles, 12 pt body/caption text, 1.5 line spacing, justified paragraphs, heading hierarchy, image sizing, figure captions, page breaks, and a footer containing `Smarta Shauri Project Documentation` plus the page number.

- [ ] **Step 3: Write pages 1-6**

Encode the approved content as:

```text
Page 1: Formal university cover and student details
Page 2: Project overview and three objectives
Page 3: Problem statement and justification
Page 4: Scope and key features
Page 5: User roles and responsibilities
Page 6: Simple system/database overview, development approach, testing, limitations, and conclusion
```

The database description must state that the web interface connects to a Django application and MySQL database, which stores accounts, profiles, grades, assessment responses/results, institution and programme information, learner plans, notifications, and audit records; role permissions protect access.

- [ ] **Step 4: Map the selected screenshots to pages 7-17**

Use this fixed mapping:

```text
7  public-home.png + auth-register.png
8  student-dashboard.png + student-profile.png
9  student-grades.png + student-progress-enabled.png
10 student-assessment.png + student-assessment-results.png
11 student-institution-search.png + student-programme-detail.png
12 student-explore.png + student-compare.png
13 student-plan.png + student-access.png
14 parent-dashboard.png + parent-child.png
15 counsellor-dashboard.png + counsellor-student-detail.png
16 school-admin-dashboard.png + school-admin-offerings.png
17 system-admin-dashboard.png + system-admin-catalogue.png
```

Each image receives a descriptive figure caption and one short paragraph explaining what the user sees and the main navigation action.

- [ ] **Step 5: Run a builder syntax check**

Run:

```bash
/Users/bensidney/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m py_compile /private/tmp/build_smarta_shauri_project_documentation.py
```

Expected: no output and exit code 0.

### Task 2: Generate and structurally audit the editable DOCX

**Files:**
- Read: `/private/tmp/build_smarta_shauri_project_documentation.py`
- Create: `output/project-documentation/Smarta-Shauri-Project-Documentation.docx`

**Interfaces:**
- Consumes: the deterministic builder and selected screenshots.
- Produces: the editable project documentation Word file and machine-readable audit evidence.

- [ ] **Step 1: Generate the document**

Run the builder with the bundled Python runtime and save the output to `output/project-documentation/Smarta-Shauri-Project-Documentation.docx`.

- [ ] **Step 2: Sanitize the Google Docs title metadata**

Run `google_docs_title_sanitize.py` against the finished DOCX so an upload uses the clean document title without changing the visible cover.

- [ ] **Step 3: Audit typography and paragraph spacing**

Open the document with `python-docx` and assert that the Normal style uses Times New Roman 12 pt, line spacing is 1.5, body alignment is justified, and the heading styles use Times New Roman bold.

- [ ] **Step 4: Audit content and image relationships**

Extract document text and assert that it includes the three approved objectives, all five user roles, `Django`, `MySQL`, the five Central Kenya counties, the advisory limitation, all eleven screenshot-page headings, and exactly 22 image relationships.

- [ ] **Step 5: Confirm editability**

Reopen the output with `python-docx`, verify it is not corrupted, and confirm the paragraphs and tables remain editable Word content rather than a flattened full-page image.

### Task 3: Render, visually inspect, and deliver the report

**Files:**
- Read: `output/project-documentation/Smarta-Shauri-Project-Documentation.docx`
- Create: `/private/tmp/smarta-shauri-project-documentation-render/page-*.png`

**Interfaces:**
- Consumes: the generated Word document.
- Produces: exactly 17 rendered page images and a final verified DOCX.

- [ ] **Step 1: Render the DOCX**

Use the bundled `render_docx.py` workflow to render every page to PNG under `/private/tmp/smarta-shauri-project-documentation-render/`.

- [ ] **Step 2: Verify exact page count**

Run:

```bash
find /private/tmp/smarta-shauri-project-documentation-render -name 'page-*.png' | wc -l
```

Expected: `17`.

- [ ] **Step 3: Inspect every rendered page**

Create contact sheets for pages 1-9 and 10-17, inspect both, and open any questionable page at original detail. Check for clipping, overlap, blank pages, orphan headings, footer placement, readable 12 pt captions, image legibility, and the intended one-page-per-section structure.

- [ ] **Step 4: Revise and re-render until clean**

Adjust paragraph lengths, table spacing, image heights, or page-break controls in the builder for every detected issue, regenerate the DOCX, sanitize it again, and repeat all structural and visual checks.

- [ ] **Step 5: Run final acceptance checks**

Confirm the final document has exactly 17 pages; pages 2-6 contain concise non-technical project discussion; pages 7-17 contain the selected screenshots; the body uses Times New Roman 12 pt with 1.5 spacing; and no credentials, secrets, or unnecessary personal data appear.

- [ ] **Step 6: Deliver the editable Word document**

Return the verified `.docx` path and summarize its exact page count, formatting, narrative coverage, role coverage, database overview, and screenshot section.
