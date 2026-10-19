# Smarta Shauri 17-Page User Manual Revision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce an editable, visually verified 17-page Smarta Shauri user manual containing the approved project description, objectives, complete dashboard coverage, and expanded institution/programme navigation screenshots.

**Architecture:** Reuse the verified 42-screen image set and deterministic DOCX builder, add focused evidence for the implemented Education Goals states, then reflow the document into the approved 17-page structure. Render the DOCX to images and revise until page count and visual checks pass.

**Tech Stack:** React/Vite interface evidence, in-app Browser control where a new live state is required, Python `python-docx`, Pillow, LibreOffice/Poppler document rendering.

## Global Constraints

- Deliver an editable Microsoft Word `.docx`.
- Produce exactly 17 pages.
- Put the project description and all three approved objectives on page 2.
- Preserve all five role dashboards and every implemented frontend route.
- Keep screenshots large and readable, with one-line explanations and navigation/action callouts.
- Add focused institution search, programme catalogue, programme detail, entry requirement, and save-goal evidence from the implemented Education Goals workflow.
- Do not expose passwords, tokens, private notes, or unnecessary personal information.
- Do not modify application source code or unrelated working-tree files.
- Keep generated output and capture assets local-only under `output/user-manual/` or `/private/tmp`.

---

### Task 1: Produce focused institution and programme evidence

**Files:**
- Read: `frontend/src/pages/EducationGoalsPage.tsx`
- Read: `frontend/src/components/students/ProgrammeReferenceDetail.tsx`
- Read: `output/user-manual/assets/raw/student-education-goals.png`
- Create: `output/user-manual/assets/raw/student-institution-search.png`
- Create: `output/user-manual/assets/raw/student-programme-catalogue.png`
- Create: `output/user-manual/assets/raw/student-programme-detail.png`

**Interfaces:**
- Consumes: implemented Education Goals page and existing safe demonstration state.
- Produces: three focused, legible screenshots for pages 9 and 10.

- [ ] **Step 1: Confirm visible controls and supported claims**

Run:

```bash
rg -n "Find an institution|Search institutions|Explore programmes|Search programmes|entry|requirement|Save" frontend/src/pages/EducationGoalsPage.tsx frontend/src/components/students/ProgrammeReferenceDetail.tsx
```

Expected: the interface supports institution filters, programme selection, sourced programme detail, entry-requirement information, and goal saving.

- [ ] **Step 2: Capture or derive the institution-search figure**

Use the live page if a safe selected state is available; otherwise create a focused crop from the existing verified full-page screenshot. The figure must show the page title, search field, county/framework/cycle/status filters, and institution-result region.

- [ ] **Step 3: Capture the selected-institution programme catalogue**

Open Education Goals, select a safe demonstration institution, and capture the selected source, programme search, and programme-list controls without exposing credentials.

- [ ] **Step 4: Capture programme detail and entry requirements**

Select a safe demonstration programme and capture the programme detail, sourced criteria/entry-requirement content, and save-goal control.

- [ ] **Step 5: Verify screenshot geometry**

Run:

```bash
sips -g pixelWidth -g pixelHeight output/user-manual/assets/raw/student-institution-search.png output/user-manual/assets/raw/student-programme-catalogue.png output/user-manual/assets/raw/student-programme-detail.png
```

Expected: all three PNGs are non-empty and have enough pixels to remain legible at approximately 4.9 inches wide.

### Task 2: Rebuild the manual to the approved 17-page layout

**Files:**
- Read: `docs/superpowers/specs/2026-08-04-smarta-shauri-17-page-manual-revision-design.md`
- Read: `output/user-manual/assets/raw/*.png`
- Modify: `/private/tmp/build_smarta_shauri_large_image_manual.py`
- Create: `output/user-manual/Smarta-Shauri-17-Page-User-Manual-With-Objectives.docx`

**Interfaces:**
- Consumes: approved page structure and verified screenshots.
- Produces: editable 17-page Word manual.

- [ ] **Step 1: Add page 2 project overview**

Create a landscape page titled `Project Description and Objectives`, use the approved description verbatim, and place the three objectives in large numbered brand-colour panels.

- [ ] **Step 2: Re-number and reflow the existing screenshot pages**

Move the original public introduction to page 3, retain three large figures per page through page 16, and keep each figure's one-line purpose, route path, and action callout.

- [ ] **Step 3: Add pages 9 and 10**

Use the new institution and programme figures with numbered callouts showing the sequence:

```text
Education Goals -> Search/filter institution -> Select institution -> Search/select programme -> Review entry requirements -> Save education goal
```

- [ ] **Step 4: Consolidate system administration on page 17**

Use a legible two-column grid for System Dashboard, Schools, Users, Catalogue, Audit Log, and Page Not Found. Preserve a readable caption and navigation/action label for every figure.

- [ ] **Step 5: Save and structurally inspect the DOCX**

Confirm the document opens through `python-docx`, contains the expected image relationships, and includes page-2 objective text exactly once.

### Task 3: Render and verify every page

**Files:**
- Read: `output/user-manual/Smarta-Shauri-17-Page-User-Manual-With-Objectives.docx`
- Create: `/private/tmp/smarta-shauri-17-page-manual-render/page-*.png`

**Interfaces:**
- Consumes: rebuilt DOCX.
- Produces: a final visually verified editable manual.

- [ ] **Step 1: Render the DOCX**

Use the bundled document runtime and `render_docx.py`, emitting one PNG per page and a QA PDF.

- [ ] **Step 2: Verify exact page count**

Run:

```bash
find /private/tmp/smarta-shauri-17-page-manual-render -name 'page-*.png' | wc -l
```

Expected: `17`.

- [ ] **Step 3: Inspect all rendered pages**

Create contact sheets for pages 1-9 and 10-17, inspect them, then open any questionable page individually at original detail. Check page 2 text, screenshot size, captions, callouts, clipping, overlap, blank pages, and footer numbering.

- [ ] **Step 4: Revise and re-render**

Correct every detected layout defect in the builder and repeat rendering until all 17 pages pass.

- [ ] **Step 5: Run final content checks**

Extract DOCX text and verify the project description, all three objectives, the five dashboard titles, institution/programme terms, and every page heading are present. Confirm no credential-like content is included.

- [ ] **Step 6: Deliver the editable Word document**

Return the final DOCX path and identify that it contains exactly 17 visually verified pages.

