# Platform UI consistency and PWA redesign

**Status:** Design approved in conversation; written specification ready for user review

**Branch:** `codex/ui-ux-pwa-redesign`

**Scope:** Resolve the full UI, responsive-design, accessibility, navigation, table-action, catalogue-performance, and installed-PWA issues recorded in the July 31 audit and the August 1 screenshot review.

**Safety:** This specification does not authorize a commit, push, pull request, or merge. Implementation remains uncommitted until the user reviews each slice.

## 1. Product and design direction

Smarta Shauri will remain a warm, trustworthy Kenyan education platform rather than adopting a generic enterprise theme. The redesign is a targeted evolution of the existing product, not a framework migration or visual restart.

The authenticated management surfaces will use:

- `DESIGN_VARIANCE: 4`
- `MOTION_INTENSITY: 3`
- `VISUAL_DENSITY: 7`

The learner, parent, and public guidance surfaces will use:

- `DESIGN_VARIANCE: 6` for authenticated guidance
- `DESIGN_VARIANCE: 8` for public editorial pages
- `MOTION_INTENSITY: 4`
- `VISUAL_DENSITY: 5`

The existing forest green, gold, flame, cream, typography, logo, and semantic CSS variables remain the source of truth. Public and authenticated pages must use the same semantic tokens. No new hardcoded component colors will be introduced.

## 2. Core layout decision

The product will use a hybrid page system. Tables are not the correct structure for every screen.

1. **Overview dashboards** use three or four compact metrics followed by one or two operational tables. Large stacks of full-width metric cards are removed.
2. **Management pages** use a standard table shell on desktop and labeled responsive records on mobile.
3. **Detail workspaces** use a summary header and tabs or anchored sections.
4. **Settings pages** use grouped forms with one clear save region.
5. **Large catalogues** use server-side filtering and pagination with a persistent selection model.
6. **Guidance and exploration pages** retain cards or comparison layouts where visual comparison is meaningful.
7. **Reports** use summaries, structured evidence sections, and a clear download action.

The sidebar is the primary navigation source. Dashboard shortcut cards that merely repeat sidebar destinations will be removed. Contextual actions, such as approving a learner or saving a selection, remain inside the relevant page.

### 2.1 Approved dashboard reference pattern

The August 1 EasyTeam dashboard screenshot is the density and coordination reference for Smarta Shauri management dashboards. The product will adopt its information structure, not copy its blue palette, branding, employee content, or exact decoration.

The Smarta Shauri adaptation uses:

- a narrow role-aware sidebar with grouped destinations;
- a compact top bar with the page title, contextual search when useful, notifications, and account access;
- three or four small summary metrics in one row;
- one dominant operational table occupying most of the main column;
- one narrow secondary column only when it contains actionable supporting information;
- restrained dividers and low-elevation surfaces instead of stacking every value in a large card;
- row actions placed beside the record they affect;
- short status labels with consistent semantic colors;
- progressive disclosure for details instead of showing all metadata at once.

The goal is calm density. A user should understand the page at a glance without being confronted by dozens of equal-priority cards, large decorative heroes, repeated navigation actions, or raw technical data.

The approved role concept boards pair a desktop layout with an installed-PWA phone layout for the system administrator, school administrator, counsellor, student, and parent. They are visual references only and remain outside the repository. Implementation follows this specification rather than copying invented names, data, icons, or decoration from the concept imagery.

## 3. Shared application foundations

### 3.1 Page shell

Every authenticated page will use the same content container, header rhythm, breadcrumbs, primary heading, loading state, and error boundary.

- Exactly one meaningful `h1` per route.
- Shared maximum content width and page gutters.
- Content begins at a consistent vertical position.
- Desktop sidebars, tablet navigation, and phone navigation are mutually exclusive.
- Fixed navigation reserves content space and respects safe-area insets.
- Mobile pages avoid redundant breadcrumbs when a concise title and back action are clearer.

### 3.2 Standard data table

The existing responsive data-list primitive will be extended into a shared management-table system rather than replaced with a third-party visual framework.

The table shell includes:

- page title and results count;
- one primary page action;
- labeled search and filters;
- optional bulk selection and bulk action bar;
- quiet column headings and horizontal row dividers;
- status badges using semantic tokens;
- pagination with previous, next, current page, and total results;
- skeleton rows, empty state, error state, and retry;
- a single row-action menu where a row has more than one secondary action.

At widths below the table breakpoint, each row becomes a labeled record. Essential fields remain visible. Secondary fields may use disclosure, but essential names, status, assignments, and actions cannot be truncated. Horizontal scrolling is allowed only for data that cannot be meaningfully reflowed, such as a comparison matrix.

Table information is coordinated in this order:

1. identity or record name;
2. the two or three fields needed for the current decision;
3. status;
4. the next relevant date or owner when applicable;
5. actions.

Administrative metadata that does not support the immediate task moves into a details drawer. Tables will normally show five to seven columns at desktop rather than exposing every available API field. Numeric columns use tabular figures and align consistently. Names and primary record labels receive the strongest weight. Supporting text uses one quieter line beneath the primary value only when it prevents another column.

Each operational row exposes one clear primary action, such as `Review` or `View`, followed by one overflow menu for secondary actions. The overflow trigger uses the accessible label `More actions for {record name}`. Secondary actions may include Edit, Assign, Download, Activate, or Deactivate. Destructive actions appear last, use the danger treatment, and require confirmation that names the affected record.

Actions will not appear as full-height repeated buttons. Color communicates meaning but is never the only indicator. Every icon-only control includes a tooltip and accessible label.

At phone widths, standard tables become labeled records. Identity and status appear first, decision fields remain visible, and the primary action plus overflow menu appear at the bottom. Contained horizontal scrolling is permitted only when reflow would destroy a meaningful comparison. In that case, the identifying column remains sticky and the page itself must not scroll horizontally.

### 3.3 Action hierarchy

- One primary action appears in the page header or save region.
- Search and filters never resemble primary actions.
- Rows with one dominant task may expose one text action.
- Rows with multiple tasks use a labeled actions menu.
- Destructive actions appear inside the menu or confirmation dialog, not as repeated large red buttons.
- Destructive actions require explicit confirmation that names the affected record.
- Buttons remain at least 44 by 44 CSS pixels and show disabled/loading states.
- Successful and failed user actions use the existing toast catalogue.

### 3.4 Standard management-page composition

Management pages use this order:

1. page title and concise purpose;
2. one page-level primary action;
3. search and filters;
4. result count and optional bulk-action toolbar;
5. table or responsive records;
6. pagination;
7. loading, empty, filtered-empty, error, and retry states.

Page-level creation and invitation actions open a bounded form region or accessible drawer. They must not become oversized full-width action bars. Controls do not float over content.

### 3.5 Forms

- Labels remain above fields and are programmatically associated.
- Related fields use consistent two-column desktop and one-column mobile layouts.
- Helper and validation messages appear directly below their field.
- Submit actions remain visible without floating over content.
- Buttons disable during submission and retain their width while loading.
- Long email addresses, school names, and combination titles wrap without clipping.

### 3.6 Terminology

Navigation and headings will use consistent Kenyan English:

- `Dashboard` rather than mixing `Home` and `Dashboard`.
- `Learners` for student records managed by staff.
- `Students` only where the school context explicitly requires it in existing API or policy language.
- `Counsellor` in user-facing copy.
- `Smarta Shauri` as the product name.

Changing a stable primary navigation label will be covered by route and accessibility tests. URL slugs remain unchanged unless this specification explicitly introduces a new route.

## 4. Role navigation and page definitions

### 4.1 Public and authentication pages

Routes:

- `/`
- `/about`
- `/pathways`
- `/how-it-works`
- `/for-schools`
- `/login`
- `/register`
- `/verify-email`
- `/forgot-password`
- `/reset-password`
- `/accept-invite`

Public pages retain their editorial layouts but use the same green, gold, flame, neutral, typography, radius, focus, and button tokens as the product. Authentication cards share one width, field rhythm, error presentation, and mobile gutter. No authenticated sidebar or bottom navigation appears on public routes.

### 4.2 System administrator

Sidebar order:

1. Dashboard
2. Schools
3. Users
4. Catalogue
5. Audit log

Pages:

- **Dashboard:** compact rollout metrics, county coverage table, framework summary, and recent activity table. Hero actions are retained only when they start a real workflow.
- **Schools:** `School | County and code | Learners | Counsellors | Evidence | Status | View | More`. Filters, result count, pagination, create-school action, and overflow actions support edit and activation changes.
- **Users:** `User | Role | School or county | Verification | Joined | Status | View | More`. PDF download and activation controls move into the overflow menu.
- **Catalogue:** `Combination | Pathway and track | Subjects | School availability | Learner choices | Status | View | More`. The table is server-filtered and paginated.
- **Audit log:** `Time | Actor | Event | Affected record | Summary | View details`. Raw structured details open in an accessible drawer instead of being printed as truncated JSON in the table.

### 4.3 School administrator

Sidebar order:

1. Dashboard
2. Learners
3. Counsellors
4. Offerings
5. School profile

Pages:

- **Dashboard:** four compact metrics for approved learners, pending access, unassigned learners, and counsellors; a learner-progress table; and a narrow supporting column for counsellor workload and offering readiness. Navigation-only quick-action cards are removed.
- **Learners:** pending requests and approved learners use tabs within one route. Approved learners use `Learner | Journey stage | Counsellor | Last activity | Status | Review | More`, plus search, status filters, selection, bulk assignment, and overflow actions for report download and access management.
- **Counsellors:** the invite action opens a compact bounded form or drawer. The table uses `Counsellor | Contact | Assigned learners | Follow-ups due | Joined | View | More`. Remove is confirmed through the overflow menu.
- **Offerings:** the full catalogue becomes a server-filtered and paginated selectable table using `Select | Combination | Pathway and track | Subjects | Availability | Status | View`. Selection persists across pages. A non-floating selected-count tray shows total selected, pending additions, pending removals, Save offering set, and Discard changes.
- **School profile:** logo, school identity, and contact information use grouped settings sections with a clear save/cancel region.

### 4.4 Counsellor

Sidebar order:

1. Dashboard
2. My learners
3. Interventions
4. Notes

Pages:

- **Dashboard:** use four compact metrics for assigned learners, learners needing attention, follow-ups due, and plans reviewed. The priority-learner table is dominant; upcoming follow-ups and assessment coverage form the supporting column. Duplicate direct-action cards are removed.
- **My learners:** use `Learner | Grade and school | Journey stage | Attention reason | Last contact | Review | More`, with attention, assessment, and search filters.
- **Learner workspace:** retain `/counselor/students/:id` and reorganize it into Overview, Grades, Assessment, Plan, Interventions, and Notes tabs. RIASEC values, pathway recommendations, and explanatory text receive structured labels and visual hierarchy instead of raw stacked output.
- **Interventions:** add `/counselor/interventions` as the only new primary route. It uses `Learner | Category | Agreed action | Due date | Visibility | Status | Review | More` for open, due, and completed follow-ups.
- **Notes:** use `Learner | Note preview | Updated | Visibility | Edit | More`. Delete remains in the overflow menu and requires confirmation.

### 4.5 Student

Sidebar order:

1. Dashboard
2. My grades
3. Explore choices
4. Compare choices
5. My plan
6. Career quiz
7. Career profile
8. Parent access
9. My profile

Pages:

- **Dashboard:** next action, compact progress, recent grades, saved combination, and relevant support. It remains learner-facing rather than adopting admin density.
- **My grades:** enrolled subjects use `Subject | Type | Latest term | Latest level | Trend | Add grade | More`. Selecting a subject reveals its grade history and a focused entry form rather than a large empty panel.
- **Explore choices:** retain combination cards because the content is exploratory. Add bounded results, pagination, consistent filters, and a persistent comparison tray.
- **Compare choices:** use an aligned comparison matrix for pathway, track, subjects, verified school availability, and provisional status.
- **My plan:** choice summary, reasoning, milestone table, review status, and counsellor feedback use a structured workspace.
- **Career quiz and profile:** keep the guided assessment and visual results. Only the current route is marked active in navigation.
- **Parent access and profile:** use standard form, status, table-action, and save patterns.

### 4.6 Parent or guardian

Sidebar structure:

1. Dashboard
2. Linked learner entries, when available

Pages:

- **Dashboard:** linked-learner selector, four compact progress summaries, learner-progress table, counsellor update, pending invitations, and report action.
- **Learner progress:** `/parent/child/:id` uses Overview, Grades, Career profile, Plan, Shared follow-ups, and Report sections. Only data approved for parent visibility is rendered.

## 5. Adaptive installed-PWA navigation

Desktop retains the role-aware sidebar and top bar. Tablet uses the compact sidebar or drawer according to available width. Authenticated phones and standalone PWA mode use a persistent bottom navigation with four primary destinations plus `More`.

Primary phone destinations:

- **Student:** Dashboard, My grades, Explore, My plan, More.
- **Counsellor:** Dashboard, My learners, Interventions, Notes, More.
- **School administrator:** Dashboard, Learners, Offerings, Counsellors, More.
- **System administrator:** Dashboard, Schools, Catalogue, Users, More.
- **Parent:** Dashboard, first linked learner when present, More. Unused slots are not filled with invented destinations.

The More surface exposes all destinations for the role, account/profile access, notifications, install/update status, and logout. It closes on navigation, Escape, and outside interaction, traps focus while modal, and restores focus to the trigger.

One role-navigation configuration is the source of truth for sidebar destinations, bottom-navigation destinations, More contents, breadcrumbs, and page titles. A destination cannot be added to only one navigation surface. The top bar may provide contextual search, notifications, and account access, but it must not repeat primary sidebar links.

Responsive layout modes are:

- `1280px` and above: full sidebar, complete operational table, and optional supporting column;
- `1024px` through `1279px`: compact sidebar and reduced secondary table information;
- `768px` through `1023px`: collapsed sidebar or accessible drawer, with tables or two-column labeled records according to available width;
- below `768px`: bottom navigation plus More and single-column labeled records.

Bottom navigation requirements:

- respects all safe-area inset environment variables;
- reserves content and toast clearance;
- provides an active icon and text label, not color alone;
- uses 44px minimum targets;
- never appears alongside the desktop sidebar;
- supports browser back, deep links, refresh, and standalone launch;
- honors reduced motion;
- does not cache private API responses for offline replay.

## 6. Large-catalogue data design

UI-005, UI-007, and UI-009 require API and rendering changes rather than CSS patches.

### 6.1 System catalogue

`GET /api/v1/system-admin/catalogue/` will accept:

- `page`
- `page_size`, with a bounded maximum
- `search`
- `status`
- `pathway`
- `track`

The response retains framework metadata and returns a paginated combinations object with `results`, `total`, `page`, and `page_size`. Filters are applied in the database before serialization.

The default page size is `25`. The interface offers `10`, `25`, and `50`, while the API enforces a maximum of `100`. Search input is debounced. Filter changes return to page one.

### 6.2 School offering catalogue

The selectable combination source will use the same bounded query model. The current saved offering endpoint continues to return the selected combination IDs for the school. The client stores selected IDs independently of the visible page, so paging or filtering never discards a selection.

Saving continues to send the complete selected ID set because the established API intentionally replaces the full offering set. The confirmation summary shows added and removed counts before mutation. Existing audit logging remains intact.

### 6.3 Student exploration

The learner combination catalogue uses bounded results with the same search and pathway concepts where practical. Saved comparison IDs remain stable across result pages.

## 7. Data and interaction behavior

- URL query parameters hold table search, filters, and page when a user may navigate back to the same result set.
- React Query keys include all server filters and pagination values.
- Page changes preserve filters and clear only invalid selections.
- Mutations update or invalidate the smallest relevant cache set.
- Loading states preserve the final layout shape.
- Empty states distinguish between no data and no filter matches.
- Network failures retain unsaved local selection and provide retry.
- 403, 404, 500, and connection errors use the existing friendly toast catalogue.
- Destructive actions cannot run twice while pending.
- Focus moves into dialogs/drawers and returns to the initiating control.
- Initial table loads use layout-matching skeletons. Background refreshes use a smaller progress treatment without replacing visible records.
- Existing content remains visible when a background refresh fails.
- Page actions, row actions, and form submissions cannot run twice while pending.

## 8. Accessibility requirements

The redesign targets WCAG 2.2 AA.

- Exactly one meaningful `h1` on every route.
- Logical heading order and semantic landmarks.
- Skip link remains the first keyboard destination.
- Visible focus on cream, green, gold, white, and tinted surfaces.
- Accessible names for icon-only and menu controls.
- Correct table headings, row labels, dialogs, menus, tabs, and live regions.
- No keyboard traps.
- Error identification in text, not color alone.
- Charts include text summaries.
- Content reflows at 200% zoom without loss of function.
- Touch targets are at least 44px.
- Motion respects `prefers-reduced-motion`.

## 9. Responsive acceptance matrix

Chromium coverage:

- 320 by 568
- 360 by 800
- 390 by 844
- 412 by 915
- 768 by 1024
- 820 by 1180
- 1024 by 768
- 1280 by 800
- 1440 by 900
- 1920 by 1080

Critical public, authentication, navigation, form, table, and PWA flows also receive WebKit or iPhone emulation. Manual checks include keyboard-only navigation, 200% zoom, reduced motion, online, slow, and offline behavior.

No route may introduce unexplained document-level horizontal overflow. No fixed or sticky element may obscure the final row, form action, toast, install prompt, or active input.

### 9.1 Audit finding acceptance matrix

| Finding | Required result |
|---|---|
| UI-001 inherited drawer | Logout and role changes reset every transient navigation surface. |
| UI-002 missing phone navigation | Every authenticated role receives the approved bottom navigation and More surface. |
| UI-003 and UI-006 missing headings | Every route contains exactly one meaningful `h1`. |
| UI-004 clipped emails | Long content wraps at `320px` without document overflow. |
| UI-005 long offering page | Server pagination keeps responses and rendered records bounded. |
| UI-007 long catalogue page | Server pagination keeps responses and rendered records bounded. |
| UI-008 router warnings | Router future behavior is configured and the development console remains clean. |
| UI-009 multi-megabyte responses | Page-size limits are enforced and verified by API tests. |
| Raw audit details | The table shows a readable summary and an accessible drawer contains complete metadata. |
| Floating or overlapping controls | No control, toast, prompt, input, or final record is obscured at any required viewport. |
| Public and authenticated color drift | All pages consume the shared semantic brand tokens. |
| Installed-PWA gaps | Install, update, offline, deep-link, standalone-launch, safe-area, navigation, and logout checks pass. |

## 10. Delivery slices

The scope is intentionally decomposed so each change remains testable and reviewable.

1. **Shared foundations:** tokens, page container, headings, forms, buttons, tables, menus, dialogs, states, and terminology.
2. **Adaptive navigation and PWA shell:** desktop/tablet/phone modes, bottom navigation, More surface, safe areas, install, update, offline, and session cleanup.
3. **Catalogue performance:** paginated backend APIs and bounded system-admin, school-offering, and learner-exploration clients.
4. **System and school administration:** dashboards, management tables, profiles, actions, and responsive states.
5. **Counsellor workspace:** dashboard, learner list, tabbed learner detail, interventions, and notes.
6. **Student workspace:** dashboard, grades, exploration, comparison, plan, assessment, access, and profile.
7. **Parent and public surfaces:** parent dashboard/detail, public color alignment, and authentication consistency.
8. **Accessibility and final visual QA:** full viewport matrix, keyboard, zoom, reduced motion, error states, browser evidence, and remaining P2/P3 polish.

Each slice follows test-driven development. It receives focused automated tests, production build verification, browser checks at the original failing viewport, CodeRabbit review, and a user checkpoint. No slice is committed or pushed without explicit approval.

## 11. Automated test strategy

- Role-aware desktop, tablet, and phone navigation contents.
- Exactly one navigation mode visible per breakpoint.
- Bottom-navigation clearance and safe-area rules.
- More-surface focus trap, Escape behavior, outside close, and restoration.
- Logout clears transient layout and user-scoped state.
- Table search, filters, query parameters, pagination, selection, actions, empty, loading, error, and retry states.
- Mobile record labels and long-content wrapping.
- Catalogue API pagination, filtering, bounded page size, query count, and permissions.
- Persistent selections across catalogue pages.
- Form validation, disabled/loading behavior, API envelopes, and toasts.
- One `h1`, ordered headings, labels, accessible names, dialog/menu/tab semantics, and chart summaries.
- Manifest, update, install, offline fallback, deep-link, and private-cache exclusions.
- Existing core learner, counsellor, school, parent, and system-admin flows remain green.

## 12. Completion criteria

The redesign is complete only when:

- every route and seeded role state has been visited in the running app;
- every route has required representative viewport evidence;
- all important controls and failure states have been exercised;
- no P0 or P1 issue remains;
- the extreme catalogue page heights and multi-megabyte unbounded request are eliminated;
- tables, actions, headings, filters, and forms use shared patterns;
- every role has complete sidebar and phone navigation;
- public and authenticated pages use one tokenized brand language;
- no unexplained overflow, clipping, overlap, or floating content remains from 320px to 1920px;
- installed-PWA launch, navigation, safe area, update, offline, deep link, refresh, and logout behavior pass;
- critical WCAG 2.2 AA checks pass manually and automatically;
- frontend tests and production build pass;
- relevant backend tests pass;
- CodeRabbit reports no unresolved blocker;
- before-and-after evidence exists for every fixed finding;
- the user approves the exact changed files before any commit and approves again before any push.

## 13. Explicit exclusions

- No migration to a new frontend framework.
- No replacement of the Smarta Shauri brand, logo, or core palette.
- No silent URL changes to existing routes.
- No caching of private authenticated API payloads for offline replay.
- No unrelated backend refactoring.
- No commit, push, pull request, or merge without the required user checkpoint.
