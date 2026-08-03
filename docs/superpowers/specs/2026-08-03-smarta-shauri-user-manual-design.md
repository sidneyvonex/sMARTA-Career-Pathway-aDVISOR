# Smarta Shauri User Manual Design Specification

**Date:** 3 August 2026  
**Status:** Approved for production  
**Deliverable:** Editable Microsoft Word document (`.docx`)

## 1. Purpose

Create a comprehensive, illustrated user manual for Smarta Shauri that explains how the complete system works and how users navigate between pages. The manual must be suitable both as a senior-project submission artefact and as a practical operating guide for real users.

The document must prioritize detailed instructions over brief page descriptions. Screenshots, navigation strips, numbered steps, captions, arrows, and numbered callouts will connect written instructions to the live interface.

## 2. Audience and scope

The manual covers the entire system for all supported audiences:

1. Visitors using public and authentication pages.
2. Students managing their profile, academic evidence, career assessment, choices, plan, and parent access.
3. Parents viewing approved learner information.
4. Counsellors monitoring learners and recording intervention notes.
5. School administrators managing the school, learners, counsellors, and offered combinations.
6. System administrators managing schools, users, the framework catalogue, and audit records.

All role dashboards must receive substantial coverage. Every route exposed by the frontend application must be catalogued, although closely related forms or transient states may share a page when that improves readability.

## 3. Cover-page content

The cover page will display:

**UNIVERSITY OF EASTERN AFRICA, BARATON**  
**SCHOOL OF BUSINESS**  
**DEPARTMENT OF INFORMATION SYSTEMS AND COMPUTING**

**Course:** INSY492 - Senior Project  
**Student name:** BENSIDNEY NDUNG'U  
**Student ID:** SNDUBE2311  
**Course instructor:** OMARI DICKSON  
**Supervisor:** OMARI DICKSON  
**Submission date:** 17 March 2026

The document title will be **SMARTA SHAURI USER MANUAL**, with **CBC Career Guidance System** as the descriptive subtitle. The Smarta Shauri logo will appear on the cover.

## 4. Document structure

The target length is approximately 20 pages. The page count may increase modestly when necessary to preserve readable screenshots and detailed procedures. The proposed sequence is:

1. Cover page and document information.
2. Table of contents and system overview.
3. Getting started and public pages.
4. Registration, sign-in, email verification, invitations, and password recovery.
5. Shared authenticated layout, navigation, notifications, responsive controls, and sign-out.
6. Student dashboard and profile.
7. Academic progress, subjects, grades, and education goals.
8. Career assessment and results.
9. Exploring and comparing choices.
10. Learner plan and parent access.
11. Parent dashboard and learner detail.
12. Counsellor dashboard and caseload.
13. Counsellor learner detail and notes.
14. School administrator dashboard.
15. School learners, counsellors, offerings, and profile.
16. System administrator dashboard.
17. School and user management.
18. Framework catalogue and audit log.
19. Reports, common end-to-end navigation flows, and troubleshooting.
20. Quick-reference navigation map, glossary, and support guidance.

## 5. Page coverage

### 5.1 Public and authentication

- Landing page (`/` when signed out)
- About (`/about`)
- Pathways (`/pathways`)
- How it works (`/how-it-works`)
- For schools (`/for-schools`)
- Login (`/login`)
- Registration (`/register`)
- Email verification (`/verify-email`)
- Forgot password (`/forgot-password`)
- Reset password (`/reset-password`)
- Accept invitation (`/accept-invite`)

### 5.2 Student

- Student dashboard (`/` when signed in as a student)
- Profile (`/profile`)
- Academic progress or grades (`/grades`)
- Education goals (`/education-goals`, when enabled)
- Career quiz (`/assessment`)
- Career profile/results (`/assessment/results`)
- Explore choices (`/explore`)
- Compare choices (`/compare`)
- My plan (`/plan`)
- Parent access (`/access`)

### 5.3 Parent

- Parent dashboard (`/` when signed in as a parent)
- Linked learner detail (`/parent/child/:id`)

### 5.4 Counsellor

- Counsellor dashboard (`/` when signed in as a counsellor)
- My students (`/counselor/students`)
- Student detail (`/counselor/students/:id`)
- Notes (`/counselor/notes`)

### 5.5 School administrator

- School administrator dashboard (`/` when signed in as a school administrator)
- Learners (`/admin/students`)
- Counsellors (`/admin/counselors`)
- Offerings (`/admin/offerings`)
- School profile (`/admin/school`)

### 5.6 System administrator

- System administrator dashboard (`/` when signed in as a system administrator)
- Schools (`/system-admin/schools`)
- Users (`/system-admin/users`)
- Catalogue (`/system-admin/catalogue`)
- Audit log (`/system-admin/audit-log`)

### 5.7 Shared and exceptional states

- Notifications panel and unread indicators.
- Mobile bottom navigation and additional-options sheet.
- Progressive Web App installation prompt where available.
- Loading, empty, error, permission-denied, and page-not-found states where they materially affect user recovery.
- Report viewing or download actions exposed through dashboards and learner-detail screens.

## 6. Instruction pattern

Each major page entry will use a consistent pattern:

1. **Purpose:** what the page helps the user accomplish.
2. **How to reach it:** a navigation strip in the form `Starting page -> Select control -> Destination page`.
3. **Screen guide:** an annotated screenshot with a descriptive caption.
4. **How to use it:** detailed, numbered instructions written with action verbs.
5. **Expected result:** the visible outcome after a successful action, including toast notifications where relevant.
6. **Important notes:** permissions, prerequisites, privacy cautions, validation rules, or recovery guidance.
7. **Where to go next:** links to the next logical task in the workflow.

Related pages may share a spread, but every route will still be named and its navigation path explained.

## 7. Screenshot and annotation policy

- Screenshots will be captured from the live local application at a desktop viewport that keeps labels and controls legible.
- Each major dashboard and route will be opened in the browser rather than documented from source code alone.
- Arrows or numbered markers will identify the controls referenced in nearby steps.
- Annotation colours will use high-contrast Smarta Shauri green and gold, with restrained red only for warnings.
- Screenshots will be cropped to the relevant interface region when a full-screen image would make controls too small.
- Captions will identify the role, page name, and the action being demonstrated.
- Passwords, authentication tokens, private notes, and unnecessary personally identifiable information will not appear.
- Safe demonstration data already present in the project may be shown where records are required to explain a workflow.

## 8. Visual design

The document is a branded operating manual, using the `compact_reference_guide` document preset as its structural baseline with named Smarta Shauri brand overrides.

- Page size: US Letter, portrait.
- Margins: 1 inch on all sides.
- Body type: 11-point professional sans-serif with comfortable line spacing.
- Primary accent: Smarta Shauri forest green.
- Secondary accent: Smarta Shauri gold.
- Text: dark neutral ink with accessible contrast.
- Heading hierarchy: numbered Heading 1, Heading 2, and Heading 3 styles.
- Footer: document title, role/section context where appropriate, and page number.
- Tables: used only for route references, troubleshooting, or genuinely comparable information.
- Callouts: restrained note, warning, prerequisite, and expected-result boxes.
- Navigation: Word heading structure, table of contents, and internal navigation links where reliable.

The cover will use the project logo and a formal university-project hierarchy. Subsequent pages will favor usable procedures and readable screenshots over decorative elements.

## 9. Accuracy and verification

Production will use three evidence sources:

1. The live application interface for visible controls, wording, and navigation behavior.
2. Frontend route and navigation definitions for route completeness.
3. Current project specification and implementation files for permissions, role boundaries, and expected outcomes.

The final Word document will be rendered to page images and every page visually inspected. The document will be revised until screenshots, arrows, tables, headings, captions, headers, footers, and page breaks are readable and free of clipping or overlap.

## 10. Acceptance criteria

The manual is complete when:

- The editable `.docx` opens successfully.
- The cover contains all approved institutional and learner information.
- Every system role and every role dashboard is documented.
- All frontend routes are named or intentionally grouped with an explicit route reference.
- Navigation between pages is shown using steps and visual navigation aids.
- Instructions are detailed enough for a first-time user to follow without source-code knowledge.
- Screenshots correspond to the implemented interface.
- Sensitive credentials and private information are excluded.
- The table of contents and heading hierarchy are consistent.
- The final rendered pages contain no clipped, overlapping, or unreadable content.
- The document is approximately 20 pages, with limited expansion allowed for readability and completeness.

## 11. Out of scope

- Developer installation, deployment, database administration, and API reference documentation.
- Source-code explanations intended for programmers.
- Invented screens or features that are not present in the current application.
- Capturing real passwords, authentication secrets, or private production records.
