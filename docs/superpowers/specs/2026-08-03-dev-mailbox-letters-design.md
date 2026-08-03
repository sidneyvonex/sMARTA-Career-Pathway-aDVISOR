# Dev Mailbox (`/letters`) — Design Spec

**Date:** 2026-08-03
**Status:** Approved — ready for implementation plan
**Applies to:** Local development only. This feature must never run in production.

---

## 1. Problem

In local development, the app cannot deliver a real email, so a newly registered
account cannot verify its email address (and password-reset / invite flows cannot be
exercised end-to-end).

The email backend differs per environment (`backend/config/settings/`):

| Env | `EMAIL_BACKEND` | Where email goes |
|-----|-----------------|------------------|
| Production | `anymail.backends.sendgrid.EmailBackend` | Real inbox via SendGrid |
| Development | `django.core.mail.backends.locmem.EmailBackend` | In-memory `mail.outbox` — invisible, discarded on reload |
| Test | `locmem.EmailBackend` | In-memory (asserted in tests) |

So in dev the verification email is generated correctly (link
`{FRONTEND_URL}/verify-email?token=…`) but vanishes into memory. The only current
workaround is flipping `is_email_verified = True` in the Django shell.

**Goal:** a dev-only in-app "mailbox" at `http://localhost:5173/letters` that captures
every outgoing email and renders it — subject, recipient, body, and a clickable link —
so a developer can complete verification / reset / invite flows exactly as a real user
would.

## 2. Feasibility note

Development runs Celery eagerly (`development.py`: `CELERY_TASK_ALWAYS_EAGER = True`),
so `send_verification_email.delay(...)` executes **synchronously inside the web
process** during the request. A custom capturing email backend therefore reliably
receives every message at send time. No worker or broker is required.

## 3. Scope

**In scope** — capture and display all four email types, which all flow through
`django.core.mail.send_mail()` in `backend/accounts/emails.py`:

- Email verification (`send_verification_email`)
- Password reset (`send_password_reset_email`)
- Staff invite (`send_staff_invite_email`)
- Parent invite (`send_parent_invite_email`)

**Out of scope (YAGNI):**

- HTML / multipart email rendering — all current bodies are plain text.
- Read/unread state, search, pagination, or filtering.
- Any authentication on the inbox (a developer is often logged-out / unverified when
  they need it).
- Any behaviour in production or test-prod environments.

## 4. Capture mechanism (decision)

A **custom dev email backend that persists each message to a DB table**. It sits at the
exact chokepoint every email already flows through (`send_mail` → backend
`send_messages`), so all four email types are captured **without any change** to
`emails.py` or the views. Rejected alternatives: filebased backend + RFC-822 parsing
(fiddly ordering/cleanup); monkeypatching `send_mail` (brittle, drifts from real code
path).

## 5. Architecture

### 5.1 Backend — new dev-only `devmail` app

Location: `backend/devmail/`.

**Model — `CapturedEmail`** (`devmail/models.py`)

| Field | Type | Notes |
|-------|------|-------|
| `to_email` | `CharField` | Comma-joined recipient list (`", ".join(message.to)`) |
| `from_email` | `CharField` | `message.from_email` |
| `subject` | `CharField` | `message.subject` |
| `body` | `TextField` | `message.body` (plain text) |
| `created_at` | `DateTimeField(auto_now_add=True)` | Ordering key |

`Meta.ordering = ['-created_at']` (newest first).

**Backend — `DevMailBackend`** (`devmail/backend.py`)

- Subclasses `django.core.mail.backends.base.BaseEmailBackend`.
- `send_messages(self, email_messages)`: for each message, create one `CapturedEmail`
  row; return the count of messages persisted. Never raises on capture (respects
  `fail_silently`).
- Wired via `EMAIL_BACKEND = 'devmail.backend.DevMailBackend'` in **`development.py`
  only**.

**App registration**

- Add `'devmail'` to `INSTALLED_APPS` in **`development.py` and `test.py` only** —
  never in `base.py` or `production.py`. This keeps the table (and its migration) out
  of production entirely while still letting the pytest suite exercise the app.
- `base.py` retains its production `EMAIL_BACKEND` (SendGrid). `development.py`
  overrides both `INSTALLED_APPS` (append `devmail`) and `EMAIL_BACKEND`.

**API — dev-only, mounted under `/api/dev/letters/`** (`devmail/views.py`, `devmail/urls.py`)

| Method + path | Response |
|---------------|----------|
| `GET /api/dev/letters/` | List, newest first: `[{id, to_email, subject, created_at}]` |
| `GET /api/dev/letters/{id}/` | Full email: `{id, to_email, from_email, subject, body, created_at}` |
| `DELETE /api/dev/letters/` | Delete all captured emails → `{deleted: <count>}` |

- Responses use the standard envelope helpers `from accounts.response import _success,
  _error` (`{data, error, message}`).
- Permission: `AllowAny` (no auth — deliberately, per scope).
- **Production guard:** every view first checks a dev-settings signal and returns
  HTTP 404 otherwise. Use `settings.DEBUG` as the guard. Confirmed values:
  `development.py` and `test.py` set `DEBUG = True` (endpoints work under both);
  `production.py` sets `DEBUG = False` (endpoints 404). Because `devmail` is not
  installed and its URLs are not mounted outside dev/test, this is defence-in-depth
  rather than the sole barrier.
- URL wiring: include `devmail.urls` in `config/urls.py` **guarded** so it is only
  added when `'devmail' in settings.INSTALLED_APPS`, keeping the route absent from
  production URL resolution.

### 5.2 Frontend — `/letters` route (dev-only)

- **Route registration:** `/letters` is added to the router **only when
  `import.meta.env.DEV` is true**, so Vite tree-shakes the page and its imports out of
  production builds. No nav-menu entry — it is reached by typing the URL.
- **API module:** `frontend/src/api/devMail.ts` — typed functions `listLetters()`,
  `getLetter(id)`, `clearLetters()`, all through the shared `axios` instance.
- **MSW:** add handlers for the three endpoints in
  `frontend/src/test/msw/handlers.ts`.
- **Page:** `frontend/src/pages/LettersPage.tsx` — two-pane inbox:
  - Left: newest-first list of captured emails (subject, recipient, relative time).
    Selecting an item loads its detail. Empty state when the inbox is empty.
  - Right: selected email — subject, `to`, `from`, timestamp, and the **plain-text body
    rendered with URLs auto-linked** (`target="_blank"`) so the verification / reset /
    invite link is clickable. Clicking a link runs the normal
    `/verify-email?token=…` (etc.) flow.
  - A **"Clear inbox"** button (calls `clearLetters()`), with a success toast per the
    project toast rules.
  - React Query for fetching; loading and error states; existing design-system CSS
    variables and classes — no hardcoded colors/spacing.
- Built following the mandated page workflow: `taste-skill` → `figma:figma-generate-design`
  → `frontend-design`.

## 6. Data flow (verification example)

```
Register in UI
  → POST /api/auth/register/
  → view calls send_verification_email.delay(user.id, email, first_name)
  → runs EAGERLY in-process (CELERY_TASK_ALWAYS_EAGER)
  → send_mail(subject, body-with-link, DEFAULT_FROM_EMAIL, [email])
  → DevMailBackend.send_messages() writes one CapturedEmail row
Developer opens http://localhost:5173/letters
  → GET /api/dev/letters/  → list
  → GET /api/dev/letters/{id}/ → body with clickable link
  → click link → /verify-email?token=… → normal verify flow → is_email_verified = True
```

## 7. Testing

**Backend (pytest, `backend/tests/`)**

1. `DevMailBackend.send_messages()` persists a `CapturedEmail` with correct
   `to_email` / `subject` / `body` and returns the message count.
2. `GET /api/dev/letters/` returns captured emails newest-first.
3. `GET /api/dev/letters/{id}/` returns the full body.
4. `DELETE /api/dev/letters/` empties the table and reports the deleted count.
5. Production guard: with `DEBUG = False`, the endpoints return 404.
6. Integration: calling `send_verification_email` (eager) results in exactly one
   captured row whose body contains a `/verify-email?token=` link.

Tests run under `config.settings.test` (which includes `devmail` in `INSTALLED_APPS`).
Use `factory_boy` factories; do not construct models directly.

**Frontend (Vitest + RTL + MSW, `frontend/src/test/`)**

1. List renders captured emails newest-first.
2. Selecting an email shows its body with a clickable (`href`) link.
3. "Clear inbox" empties the list and shows a success toast.
4. The `/letters` route is not registered when not in dev mode.

## 8. Production-safety summary

Three independent barriers ensure this never reaches production:

1. `devmail` is absent from `INSTALLED_APPS` outside development/test — the model,
   migration, and table do not exist in production.
2. `config/urls.py` mounts `devmail.urls` only when the app is installed — the routes
   do not resolve in production.
3. The frontend `/letters` route registers only under `import.meta.env.DEV` — the page
   is tree-shaken from production bundles.

(The per-view `DEBUG` 404 check is defence-in-depth on top of the above.)

## 9. Files touched

**Backend (new)**
- `backend/devmail/__init__.py`
- `backend/devmail/apps.py`
- `backend/devmail/models.py`
- `backend/devmail/backend.py`
- `backend/devmail/views.py`
- `backend/devmail/urls.py`
- `backend/devmail/serializers.py`
- `backend/devmail/migrations/0001_initial.py`
- `backend/tests/test_devmail.py`
- `backend/tests/factories.py` (add `CapturedEmailFactory`)

**Backend (edit)**
- `backend/config/settings/development.py` — append `devmail` to `INSTALLED_APPS`,
  set `EMAIL_BACKEND = 'devmail.backend.DevMailBackend'`.
- `backend/config/settings/test.py` — append `devmail` to `INSTALLED_APPS`.
- `backend/config/urls.py` — conditionally include `devmail.urls`.

**Frontend (new)**
- `frontend/src/api/devMail.ts`
- `frontend/src/pages/LettersPage.tsx`
- `frontend/src/test/letters-page.test.tsx`

**Frontend (edit)**
- `frontend/src/App.tsx` (or router file) — register `/letters` under
  `import.meta.env.DEV`.
- `frontend/src/test/msw/handlers.ts` — add the three dev-letters handlers.
- Page-specific CSS under `frontend/src/styles/` if new classes are needed.
