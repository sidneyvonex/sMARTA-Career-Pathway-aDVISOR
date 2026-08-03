# Dev Mailbox (`/letters`) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give local development an in-app mailbox at `http://localhost:5173/letters` that captures every outgoing email (verification, password reset, staff invite, parent invite) and renders it with a clickable link, so a developer can complete email-verification and other link flows without a real inbox.

**Architecture:** A dev-only Django app `devmail` provides a `DevMailBackend` (set as `EMAIL_BACKEND` in development) that persists every `send_mail()` call to a `CapturedEmail` table, plus a dev-guarded API under `/api/v1/dev/letters/`. A React `/letters` page — registered only under `import.meta.env.DEV` — fetches and renders the captured emails. Three independent barriers keep it out of production (app not installed, URLs not mounted, route tree-shaken).

**Tech Stack:** Django 4.2 + DRF (backend), pytest-django (tests), React + TypeScript + React Query + axios (frontend), Vitest + React Testing Library + MSW 2 (frontend tests).

## Global Constraints

- Response envelope: `{ data, error, message }`; use `from accounts.response import _success, _error` — never construct `Response(...)` manually. (`error: true` on errors.)
- API URL prefix is `/api/v1/`; frontend axios `baseURL` is `/api/v1`, so frontend paths omit that prefix (e.g. `/dev/letters/`).
- Development runs Celery eagerly (`CELERY_TASK_ALWAYS_EAGER = True`), so `.delay(...)` email tasks execute synchronously in-process.
- Tests: backend uses `config.settings.test` (SQLite in-memory, `DEBUG = True`); use `factory_boy` factories — never build models directly. Frontend adds an MSW handler for every new endpoint.
- Frontend: use CSS variables and existing classes — never hardcode colors/spacing/fonts. Every button has a `disabled` state during async and `min-height: var(--min-touch-target)`. Every user action shows a toast (`react-hot-toast`).
- No "Co-Authored-By: Claude" lines in commits. Commit format: `type(scope): description`, one logical change per commit.
- `devmail` MUST NOT be installed or reachable in production (`base.py` / `production.py`).
- The frontend page is built following the mandated page workflow — `taste-skill:taste-skill` → `figma:figma-generate-design` → `frontend-design:frontend-design` — before/while writing `LettersPage.tsx` (see Task 6).

---

### Task 1: `devmail` app, `CapturedEmail` model, settings registration, factory

**Files:**
- Create: `backend/devmail/__init__.py` (empty)
- Create: `backend/devmail/apps.py`
- Create: `backend/devmail/models.py`
- Create: `backend/devmail/migrations/__init__.py` (empty)
- Create: `backend/devmail/migrations/0001_initial.py` (generated)
- Modify: `backend/config/settings/test.py` — add `'devmail'` to `INSTALLED_APPS`
- Modify: `backend/config/settings/development.py` — add `devmail` to `INSTALLED_APPS`
- Modify: `backend/tests/factories.py` — add `CapturedEmailFactory`
- Test: `backend/tests/test_devmail.py`

**Interfaces:**
- Produces: `devmail.models.CapturedEmail` with fields `to_email: str`, `from_email: str`, `subject: str`, `body: str`, `created_at: datetime`; `Meta.ordering = ['-created_at']`.
- Produces: `tests.factories.CapturedEmailFactory` (DjangoModelFactory for `CapturedEmail`).

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_devmail.py`:

```python
import pytest

from devmail.models import CapturedEmail
from tests.factories import CapturedEmailFactory

pytestmark = pytest.mark.django_db


def test_captured_email_orders_newest_first():
    older = CapturedEmailFactory(subject='Older')
    newer = CapturedEmailFactory(subject='Newer')
    # created_at is auto_now_add; force a deterministic order.
    CapturedEmail.objects.filter(pk=older.pk).update(
        created_at='2026-08-01T09:00:00Z'
    )
    CapturedEmail.objects.filter(pk=newer.pk).update(
        created_at='2026-08-02T09:00:00Z'
    )

    subjects = list(CapturedEmail.objects.values_list('subject', flat=True))

    assert subjects == ['Newer', 'Older']
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .\venv\Scripts\pytest tests/test_devmail.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'devmail'`.

- [ ] **Step 3: Create the app package and model**

`backend/devmail/__init__.py`: empty file.

`backend/devmail/apps.py`:

```python
from django.apps import AppConfig


class DevmailConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'devmail'
```

`backend/devmail/models.py`:

```python
from django.db import models


class CapturedEmail(models.Model):
    """A single outgoing email captured for the local dev mailbox.

    Only written by DevMailBackend under development settings. This table
    does not exist in production (the app is not installed there).
    """

    to_email = models.CharField(max_length=500)
    from_email = models.CharField(max_length=255)
    subject = models.CharField(max_length=500)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subject} -> {self.to_email}'
```

`backend/devmail/migrations/__init__.py`: empty file.

- [ ] **Step 4: Register the app in test and development settings**

In `backend/config/settings/test.py`, add `'devmail',` to the end of the `INSTALLED_APPS` list (after `'tertiary',`):

```python
    'guidance',
    'tertiary',
    'devmail',
]
```

In `backend/config/settings/development.py`, append `devmail` to the inherited `INSTALLED_APPS` (it is imported via `from .base import *`). Add this line after the imports:

```python
INSTALLED_APPS = [*INSTALLED_APPS, 'devmail']  # noqa: F405
```

- [ ] **Step 5: Generate the migration**

Run: `cd backend && .\venv\Scripts\python.exe manage.py makemigrations devmail --settings=config.settings.development`
Expected: creates `backend/devmail/migrations/0001_initial.py` with the `CapturedEmail` model.

- [ ] **Step 6: Add the factory**

In `backend/tests/factories.py`, add the model import near the other model imports:

```python
from devmail.models import CapturedEmail
```

And add the factory at the end of the file:

```python
class CapturedEmailFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CapturedEmail

    to_email = 'learner@test.com'
    from_email = 'noreply@cbcguidance.co.ke'
    subject = factory.Sequence(lambda n: f'Test email {n}')
    body = 'Hello from Smarta Shauri.'
```

- [ ] **Step 7: Run test to verify it passes**

Run: `cd backend && .\venv\Scripts\pytest tests/test_devmail.py -v`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/devmail backend/config/settings/test.py backend/config/settings/development.py backend/tests/factories.py backend/tests/test_devmail.py
git commit -m "feat(devmail): add CapturedEmail model and dev-only app registration"
```

---

### Task 2: `DevMailBackend` capturing email backend

**Files:**
- Create: `backend/devmail/backend.py`
- Modify: `backend/config/settings/development.py` — set `EMAIL_BACKEND`
- Test: `backend/tests/test_devmail.py` (add tests)

**Interfaces:**
- Consumes: `devmail.models.CapturedEmail` (Task 1).
- Produces: `devmail.backend.DevMailBackend` — a `BaseEmailBackend` whose `send_messages(email_messages) -> int` persists one `CapturedEmail` per message and returns the count.

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/test_devmail.py`:

```python
from django.core import mail
from django.test import override_settings


@override_settings(EMAIL_BACKEND='devmail.backend.DevMailBackend')
def test_dev_mail_backend_persists_sent_email():
    sent = mail.send_mail(
        subject='Verify your CBC Guidance account',
        message='Click http://localhost:5173/verify-email?token=abc',
        from_email='noreply@cbcguidance.co.ke',
        recipient_list=['new.learner@test.com'],
    )

    assert sent == 1
    captured = CapturedEmail.objects.get()
    assert captured.to_email == 'new.learner@test.com'
    assert captured.from_email == 'noreply@cbcguidance.co.ke'
    assert captured.subject == 'Verify your CBC Guidance account'
    assert 'verify-email?token=abc' in captured.body


@override_settings(EMAIL_BACKEND='devmail.backend.DevMailBackend')
def test_dev_mail_backend_joins_multiple_recipients():
    mail.send_mail(
        subject='Invite',
        message='Body',
        from_email='noreply@cbcguidance.co.ke',
        recipient_list=['a@test.com', 'b@test.com'],
    )

    captured = CapturedEmail.objects.get()
    assert captured.to_email == 'a@test.com, b@test.com'
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .\venv\Scripts\pytest tests/test_devmail.py -k dev_mail_backend -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'devmail.backend'`.

- [ ] **Step 3: Implement the backend**

`backend/devmail/backend.py`:

```python
from django.core.mail.backends.base import BaseEmailBackend

from .models import CapturedEmail


class DevMailBackend(BaseEmailBackend):
    """Persist outgoing email into CapturedEmail for the local dev mailbox.

    Wired as EMAIL_BACKEND under development settings only. Every send_mail()
    call flows through send_messages(), so all email types are captured with
    no changes to the sending code.
    """

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        count = 0
        for message in email_messages:
            try:
                CapturedEmail.objects.create(
                    to_email=', '.join(message.to),
                    from_email=message.from_email,
                    subject=message.subject,
                    body=message.body,
                )
                count += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return count
```

- [ ] **Step 4: Wire the backend in development settings**

In `backend/config/settings/development.py`, replace the existing line:

```python
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
```

with:

```python
EMAIL_BACKEND = 'devmail.backend.DevMailBackend'
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && .\venv\Scripts\pytest tests/test_devmail.py -v`
Expected: PASS (all tests so far).

- [ ] **Step 6: Commit**

```bash
git add backend/devmail/backend.py backend/config/settings/development.py backend/tests/test_devmail.py
git commit -m "feat(devmail): capture outgoing email via DevMailBackend in development"
```

---

### Task 3: Dev-only API — list, detail, clear, and production guard

**Files:**
- Create: `backend/devmail/serializers.py`
- Create: `backend/devmail/views.py`
- Create: `backend/devmail/urls.py`
- Modify: `backend/config/urls.py` — conditionally include `devmail.urls`
- Test: `backend/tests/test_devmail.py` (add tests)

**Interfaces:**
- Consumes: `CapturedEmail` (Task 1), `CapturedEmailFactory` (Task 1), `_success` / `_error` (`accounts.response`).
- Produces: endpoints mounted at `/api/v1/dev/`:
  - `GET /api/v1/dev/letters/` → `_success(data=[{id, to_email, subject, created_at}])` newest-first
  - `GET /api/v1/dev/letters/<int:pk>/` → `_success(data={id, to_email, from_email, subject, body, created_at})`
  - `DELETE /api/v1/dev/letters/` → `_success(data={'deleted': <int>}, message='Inbox cleared.')`
  - All return HTTP 404 when `settings.DEBUG` is False.

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/test_devmail.py`:

```python
from rest_framework.test import APIClient


def _api():
    return APIClient()


def test_letter_list_returns_newest_first():
    older = CapturedEmailFactory(subject='Older')
    newer = CapturedEmailFactory(subject='Newer')
    CapturedEmail.objects.filter(pk=older.pk).update(created_at='2026-08-01T09:00:00Z')
    CapturedEmail.objects.filter(pk=newer.pk).update(created_at='2026-08-02T09:00:00Z')

    response = _api().get('/api/v1/dev/letters/')

    assert response.status_code == 200
    body = response.json()
    assert body['error'] is None
    assert [row['subject'] for row in body['data']] == ['Newer', 'Older']
    assert set(body['data'][0].keys()) == {'id', 'to_email', 'subject', 'created_at'}


def test_letter_detail_returns_full_body():
    letter = CapturedEmailFactory(
        subject='Reset your CBC Guidance password',
        body='Reset link: http://localhost:5173/reset-password?token=xyz',
    )

    response = _api().get(f'/api/v1/dev/letters/{letter.pk}/')

    assert response.status_code == 200
    data = response.json()['data']
    assert data['subject'] == 'Reset your CBC Guidance password'
    assert 'reset-password?token=xyz' in data['body']
    assert 'from_email' in data


def test_letter_detail_missing_returns_404():
    response = _api().get('/api/v1/dev/letters/999999/')

    assert response.status_code == 404
    assert response.json()['error'] is True


def test_clear_inbox_deletes_all_letters():
    CapturedEmailFactory.create_batch(3)

    response = _api().delete('/api/v1/dev/letters/')

    assert response.status_code == 200
    assert response.json()['data']['deleted'] == 3
    assert CapturedEmail.objects.count() == 0


@override_settings(DEBUG=False)
def test_endpoints_return_404_in_production_mode():
    CapturedEmailFactory()

    assert _api().get('/api/v1/dev/letters/').status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .\venv\Scripts\pytest tests/test_devmail.py -k "letter or clear or production" -v`
Expected: FAIL — 404 for all (URLs not mounted yet).

- [ ] **Step 3: Implement the serializers**

`backend/devmail/serializers.py`:

```python
from rest_framework import serializers

from .models import CapturedEmail


class CapturedEmailListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CapturedEmail
        fields = ['id', 'to_email', 'subject', 'created_at']


class CapturedEmailDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CapturedEmail
        fields = ['id', 'to_email', 'from_email', 'subject', 'body', 'created_at']
```

- [ ] **Step 4: Implement the views**

`backend/devmail/views.py`:

```python
from django.conf import settings
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from accounts.response import _error, _success

from .models import CapturedEmail
from .serializers import CapturedEmailDetailSerializer, CapturedEmailListSerializer


class _DevOnlyView(APIView):
    """Base view for the dev mailbox. Unauthenticated by design (developers
    are often logged out), and hidden (404) whenever DEBUG is off."""

    permission_classes = [AllowAny]

    def dispatch(self, request, *args, **kwargs):
        if not settings.DEBUG:
            raise Http404()
        return super().dispatch(request, *args, **kwargs)


class LetterListView(_DevOnlyView):
    def get(self, request):
        letters = CapturedEmail.objects.all()  # Meta.ordering = -created_at
        return _success(data=CapturedEmailListSerializer(letters, many=True).data)

    def delete(self, request):
        deleted, _ = CapturedEmail.objects.all().delete()
        return _success(data={'deleted': deleted}, message='Inbox cleared.')


class LetterDetailView(_DevOnlyView):
    def get(self, request, pk):
        try:
            letter = CapturedEmail.objects.get(pk=pk)
        except CapturedEmail.DoesNotExist:
            return _error('Letter not found.', status.HTTP_404_NOT_FOUND)
        return _success(data=CapturedEmailDetailSerializer(letter).data)
```

- [ ] **Step 5: Wire the URLs**

`backend/devmail/urls.py`:

```python
from django.urls import path

from .views import LetterDetailView, LetterListView

urlpatterns = [
    path('letters/', LetterListView.as_view(), name='dev-letter-list'),
    path('letters/<int:pk>/', LetterDetailView.as_view(), name='dev-letter-detail'),
]
```

In `backend/config/urls.py`, add the import at the top:

```python
from django.conf import settings
```

and append this block after the `urlpatterns = [...]` list (so the route is only mounted when the app is installed — i.e. never in production):

```python
if 'devmail' in settings.INSTALLED_APPS:
    urlpatterns += [path('api/v1/dev/', include('devmail.urls'))]
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && .\venv\Scripts\pytest tests/test_devmail.py -v`
Expected: PASS (all).

- [ ] **Step 7: Commit**

```bash
git add backend/devmail/serializers.py backend/devmail/views.py backend/devmail/urls.py backend/config/urls.py backend/tests/test_devmail.py
git commit -m "feat(devmail): dev-only letters API with production guard"
```

---

### Task 4: Backend integration — real verification email is captured

**Files:**
- Test: `backend/tests/test_devmail.py` (add one integration test)

**Interfaces:**
- Consumes: `accounts.emails.send_verification_email` (existing Celery `@shared_task`), `DevMailBackend`, `CapturedEmail`.

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_devmail.py`:

```python
from accounts.emails import send_verification_email
from tests.factories import UserFactory


@override_settings(EMAIL_BACKEND='devmail.backend.DevMailBackend')
def test_verification_email_flows_into_the_mailbox():
    user = UserFactory(email='new.grad@test.com', first_name='Njeri')

    # Eager Celery in test settings runs this synchronously.
    send_verification_email(user.id, user.email, user.first_name)

    captured = CapturedEmail.objects.get()
    assert captured.to_email == 'new.grad@test.com'
    assert captured.subject == 'Verify your CBC Guidance account'
    assert '/verify-email?token=' in captured.body
```

> Note: call `send_verification_email(...)` directly (not `.delay(...)`) — invoking the task function runs its body synchronously, which is exactly what eager Celery does in dev/test. This keeps the test independent of Celery configuration.

- [ ] **Step 2: Run test to verify it passes (or fails meaningfully)**

Run: `cd backend && .\venv\Scripts\pytest tests/test_devmail.py::test_verification_email_flows_into_the_mailbox -v`
Expected: PASS — the whole capture chain works end-to-end with the real email template.

- [ ] **Step 3: Run the full backend suite (no regressions)**

Run: `cd backend && .\venv\Scripts\pytest tests/ -q`
Expected: PASS — existing email tests still pass (they set their own `EMAIL_BACKEND` / use `mail.outbox`; the dev backend is only active under development settings or when explicitly overridden).

> If any existing test relied on `django.core.mail.backends.locmem.EmailBackend` being the *development* default, it will still pass because tests run under `config.settings.test`, which keeps `locmem`. Only `development.py` changed its backend.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_devmail.py
git commit -m "test(devmail): verify real verification email is captured end-to-end"
```

---

### Task 5: Frontend API module + MSW handlers

**Files:**
- Create: `frontend/src/api/devMail.ts`
- Modify: `frontend/src/test/msw/handlers.ts` — add three dev-letters handlers to the exported `handlers` array
- Test: `frontend/src/test/devmail-api.test.ts`

**Interfaces:**
- Produces: `devMailApi.list()`, `devMailApi.get(id: number)`, `devMailApi.clear()` returning axios responses whose `.data` is the standard envelope.
- Produces: TypeScript types `LetterSummary { id, to_email, subject, created_at }` and `LetterDetail extends LetterSummary { from_email, body }`.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/test/devmail-api.test.ts`:

```typescript
import { describe, expect, it } from 'vitest'

import { devMailApi } from '../api/devMail'

describe('devMailApi', () => {
  it('lists captured letters newest-first', async () => {
    const res = await devMailApi.list()
    expect(res.data.error).toBeNull()
    expect(res.data.data[0].subject).toBe('Verify your CBC Guidance account')
  })

  it('fetches a single letter with its body', async () => {
    const res = await devMailApi.get(2)
    expect(res.data.data.body).toContain('/verify-email?token=')
  })

  it('clears the inbox', async () => {
    const res = await devMailApi.clear()
    expect(res.data.data.deleted).toBeGreaterThanOrEqual(0)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- devmail-api`
Expected: FAIL — cannot resolve `../api/devMail`.

- [ ] **Step 3: Implement the API module**

`frontend/src/api/devMail.ts`:

```typescript
import api from '../lib/axios'

export interface LetterSummary {
  id: number
  to_email: string
  subject: string
  created_at: string
}

export interface LetterDetail extends LetterSummary {
  from_email: string
  body: string
}

type Envelope<T> = { data: T; error: null; message: string }

export const devMailApi = {
  list: () => api.get<Envelope<LetterSummary[]>>('/dev/letters/'),
  get: (id: number) => api.get<Envelope<LetterDetail>>(`/dev/letters/${id}/`),
  clear: () => api.delete<Envelope<{ deleted: number }>>('/dev/letters/'),
}
```

- [ ] **Step 4: Add MSW handlers**

In `frontend/src/test/msw/handlers.ts`, add these three handlers to the exported `handlers` array (find `export const handlers = [` and add inside it):

```typescript
  http.get('/api/v1/dev/letters/', () =>
    HttpResponse.json({
      data: [
        { id: 2, to_email: 'new@test.com', subject: 'Verify your CBC Guidance account', created_at: '2026-08-03T10:05:00Z' },
        { id: 1, to_email: 'old@test.com', subject: 'Reset your CBC Guidance password', created_at: '2026-08-03T10:00:00Z' },
      ],
      error: null,
      message: '',
    }),
  ),
  http.get('/api/v1/dev/letters/:id/', ({ params }) =>
    HttpResponse.json({
      data: {
        id: Number(params.id),
        to_email: 'new@test.com',
        from_email: 'noreply@cbcguidance.co.ke',
        subject: 'Verify your CBC Guidance account',
        body: 'Hi Njeri,\n\nPlease verify your email address by clicking the link below:\n\nhttp://localhost:5173/verify-email?token=abc123\n\nThis link expires in 24 hours.',
        created_at: '2026-08-03T10:05:00Z',
      },
      error: null,
      message: '',
    }),
  ),
  http.delete('/api/v1/dev/letters/', () =>
    HttpResponse.json({ data: { deleted: 2 }, error: null, message: 'Inbox cleared.' }),
  ),
```

> If `handlers.ts` does not already import `http` and `HttpResponse` from `msw`, they are imported at the top of the file (line 1: `import { delay, http, HttpResponse } from 'msw'`) — reuse those.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd frontend && npm test -- devmail-api`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api/devMail.ts frontend/src/test/msw/handlers.ts frontend/src/test/devmail-api.test.ts
git commit -m "feat(devmail): frontend dev-letters API client and MSW handlers"
```

---

### Task 6: `/letters` page, dev-only route, and page tests

> **REQUIRED before coding the UI:** run the mandated page workflow — `taste-skill:taste-skill` (declare design read + dials), `figma:figma-generate-design` (wireframe), then `frontend-design:frontend-design` (build). The reference implementation below defines the **functional contract the tests depend on** (headings, roles, button labels, auto-linked body); the visual treatment (layout, classes, spacing) is refined through those skills using the design-system CSS variables. Do not change the test-facing names below without updating the tests.

**Files:**
- Create: `frontend/src/pages/LettersPage.tsx`
- Create: `frontend/src/test/letters-page.test.tsx`
- Create: `frontend/src/test/letters-route.test.tsx`
- Modify: `frontend/src/App.tsx` — lazy-import `LettersPage`, register `/letters` under `import.meta.env.DEV`
- Modify (optional): `frontend/src/styles/` — add a page CSS file if new classes are needed

**Interfaces:**
- Consumes: `devMailApi` (Task 5), `react-hot-toast`, React Query.
- Produces: default-exported `LettersPage` React component. Test-facing contract:
  - An `<h1>` with accessible name **"Dev Mailbox"**.
  - A list where each captured email is a `button` whose accessible name contains the email subject; clicking it loads that email's detail.
  - A detail region showing the subject, `to`/`from`, and the body rendered with any URL as an `<a>` (`role="link"`, `target="_blank"`, `rel="noreferrer"`).
  - A `button` named **"Clear inbox"** that calls `devMailApi.clear()` and, on success, shows `toast.success('Inbox cleared.')` and empties the list.
  - An empty state with the text **"No emails captured yet"** when the list is empty.

- [ ] **Step 1: Write the failing page tests**

Create `frontend/src/test/letters-page.test.tsx`:

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Toaster } from 'react-hot-toast'
import { describe, expect, it } from 'vitest'

import LettersPage from '../pages/LettersPage'
import { server } from './msw/server'

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <LettersPage />
      <Toaster />
    </QueryClientProvider>,
  )
}

describe('LettersPage', () => {
  it('lists captured emails newest-first', async () => {
    renderPage()
    const items = await screen.findAllByRole('button', { name: /account|password/i })
    expect(items[0]).toHaveAccessibleName(/Verify your CBC Guidance account/i)
  })

  it('shows the selected email body with a clickable link', async () => {
    renderPage()
    const item = await screen.findByRole('button', { name: /Verify your CBC Guidance account/i })
    await userEvent.click(item)
    const link = await screen.findByRole('link', { name: /verify-email\?token=/i })
    expect(link).toHaveAttribute('href', expect.stringContaining('/verify-email?token='))
  })

  it('clears the inbox and shows a toast', async () => {
    renderPage()
    await screen.findByRole('button', { name: /Verify your CBC Guidance account/i })

    // After clearing, the list is empty.
    server.use(
      http.get('/api/v1/dev/letters/', () =>
        HttpResponse.json({ data: [], error: null, message: '' }),
      ),
    )
    await userEvent.click(screen.getByRole('button', { name: /Clear inbox/i }))

    expect(await screen.findByText(/Inbox cleared\./i)).toBeInTheDocument()
    expect(await screen.findByText(/No emails captured yet/i)).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npm test -- letters-page`
Expected: FAIL — cannot resolve `../pages/LettersPage`.

- [ ] **Step 3: Implement the page**

`frontend/src/pages/LettersPage.tsx` (reference implementation — refine visuals via the design skills, keep the contract):

```tsx
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import toast from 'react-hot-toast'

import { devMailApi } from '../api/devMail'

const URL_RE = /(https?:\/\/[^\s]+)/g

function LinkifiedBody({ body }: { body: string }) {
  const parts = body.split(URL_RE)
  return (
    <pre className="letters-body">
      {parts.map((part, i) =>
        URL_RE.test(part) ? (
          <a key={i} href={part} target="_blank" rel="noreferrer">
            {part}
          </a>
        ) : (
          <span key={i}>{part}</span>
        ),
      )}
    </pre>
  )
}

export default function LettersPage() {
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const listQuery = useQuery({
    queryKey: ['dev-letters'],
    queryFn: async () => (await devMailApi.list()).data.data,
  })

  const detailQuery = useQuery({
    queryKey: ['dev-letter', selectedId],
    queryFn: async () => (await devMailApi.get(selectedId as number)).data.data,
    enabled: selectedId !== null,
  })

  const clearMutation = useMutation({
    mutationFn: () => devMailApi.clear(),
    onSuccess: () => {
      toast.success('Inbox cleared.')
      setSelectedId(null)
      queryClient.invalidateQueries({ queryKey: ['dev-letters'] })
    },
    onError: () => toast.error('Could not clear the inbox.'),
  })

  const letters = listQuery.data ?? []

  return (
    <main className="letters-page">
      <header className="letters-header">
        <h1>Dev Mailbox</h1>
        <button
          type="button"
          className="btn-ghost"
          onClick={() => clearMutation.mutate()}
          disabled={clearMutation.isPending || letters.length === 0}
        >
          Clear inbox
        </button>
      </header>

      <div className="letters-layout">
        <ul className="letters-list">
          {letters.length === 0 && <li className="letters-empty">No emails captured yet</li>}
          {letters.map((letter) => (
            <li key={letter.id}>
              <button type="button" onClick={() => setSelectedId(letter.id)}>
                <span className="letters-subject">{letter.subject}</span>
                <span className="letters-to">{letter.to_email}</span>
                <time dateTime={letter.created_at}>
                  {new Date(letter.created_at).toLocaleString()}
                </time>
              </button>
            </li>
          ))}
        </ul>

        <section className="letters-detail">
          {selectedId === null && <p>Select an email to read it.</p>}
          {detailQuery.data && (
            <>
              <h2>{detailQuery.data.subject}</h2>
              <p>To: {detailQuery.data.to_email}</p>
              <p>From: {detailQuery.data.from_email}</p>
              <LinkifiedBody body={detailQuery.data.body} />
            </>
          )}
        </section>
      </div>
    </main>
  )
}
```

Add minimal styles (create `frontend/src/styles/letters.css` and import it in the page, or extend an existing page CSS file) using design-system variables — two-column `letters-layout` on wide screens, single column on mobile; `.letters-body` uses `white-space: pre-wrap`; list buttons meet `min-height: var(--min-touch-target)`. No hardcoded colors — use `var(--color-*)`, `var(--space-*)`, `var(--radius-*)`.

- [ ] **Step 4: Run page tests to verify they pass**

Run: `cd frontend && npm test -- letters-page`
Expected: PASS.

- [ ] **Step 5: Register the dev-only route**

In `frontend/src/App.tsx`:

Add the lazy import alongside the other `lazy(...)` page imports (after line ~49):

```typescript
const LettersPage = lazy(() => import('./pages/LettersPage'))
```

Add the route among the **public** routes (right after the `/accept-invite` route, ~line 91), gated so it is stripped from production builds:

```tsx
      {import.meta.env.DEV && (
        <Route
          path="/letters"
          element={(
            <Suspense fallback={<LoadingSkeleton label="Loading mailbox" rows={4} />}>
              <LettersPage />
            </Suspense>
          )}
        />
      )}
```

- [ ] **Step 6: Write the route-guard tests**

Create `frontend/src/test/letters-route.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import App from '../App'
import { useAuthStore } from '../store/authStore'

describe('dev mailbox route gating', () => {
  afterEach(() => {
    vi.unstubAllEnvs()
    window.history.pushState({}, '', '/')
    useAuthStore.setState({ isLoading: false })
  })

  it('serves /letters in development mode', async () => {
    window.history.pushState({}, '', '/letters')
    render(<App />)
    expect(await screen.findByRole('heading', { name: 'Dev Mailbox' })).toBeInTheDocument()
  })

  it('does not serve /letters when not in dev mode', async () => {
    vi.stubEnv('DEV', false)
    window.history.pushState({}, '', '/letters')
    render(<App />)
    // Give the router a tick; the mailbox heading must never appear.
    await new Promise((r) => setTimeout(r, 0))
    expect(screen.queryByRole('heading', { name: 'Dev Mailbox' })).not.toBeInTheDocument()
  })
})
```

> `import.meta.env.DEV` is `true` by default under Vitest, so the first test needs no stub. `vi.stubEnv('DEV', false)` flips it for the negative test. The `/letters` route is public, so no authenticated user is required.

- [ ] **Step 7: Run route tests to verify they pass**

Run: `cd frontend && npm test -- letters-route`
Expected: PASS.

- [ ] **Step 8: Run the full frontend suite and build**

Run: `cd frontend && npm test`
Expected: PASS (no regressions).
Run: `cd frontend && npm run build`
Expected: build succeeds; production bundle excludes the `/letters` route (tree-shaken via `import.meta.env.DEV`).

- [ ] **Step 9: Commit**

```bash
git add frontend/src/pages/LettersPage.tsx frontend/src/test/letters-page.test.tsx frontend/src/test/letters-route.test.tsx frontend/src/App.tsx frontend/src/styles
git commit -m "feat(devmail): add /letters dev mailbox page with dev-only routing"
```

---

### Task 7: Manual verification and docs

**Files:**
- Modify: `LOCAL_SETUP.md` — document the dev mailbox (this file is git-ignored / local-only; update it but do not commit)

- [ ] **Step 1: Manually verify the full flow**

1. Ensure backend and frontend dev servers are running (backend on `:8000` under `config.settings.development`, frontend on `:5173`).
2. Register a brand-new account at `http://localhost:5173/register`.
3. Open `http://localhost:5173/letters` — the "Verify your CBC Guidance account" email appears in the list.
4. Open it and click the verification link in the body → it opens `/verify-email?token=…` and the account becomes verified.
5. Trigger a password reset from `http://localhost:5173/forgot-password` and confirm that email is captured too.

- [ ] **Step 2: Document it locally**

Add a short "Verifying email in local dev" section to `LOCAL_SETUP.md` pointing developers to `http://localhost:5173/letters`. (Do not commit — `LOCAL_SETUP.md` is git-ignored.)

- [ ] **Step 3: Run the code review**

Per project rules, run `coderabbit:code-review` on the branch diff before finishing. Address findings via `superpowers:receiving-code-review`.

---

## Self-Review

**Spec coverage:**
- Capture mechanism (`DevMailBackend` → `CapturedEmail`) → Tasks 1–2. ✅
- All four email types captured (single chokepoint) → covered structurally in Task 2, exercised for verification in Task 4. ✅
- DB persistence / newest-first → Task 1 (model `ordering`) + Task 3 (list test). ✅
- Dev-only API (list/detail/clear) + envelope → Task 3. ✅
- Production guard (DEBUG 404) → Task 3. ✅
- URLs mounted only when app installed → Task 3 (config/urls.py conditional). ✅
- App installed dev/test only → Task 1 (settings). ✅
- Frontend API + MSW → Task 5. ✅
- `/letters` two-pane page, auto-linked bodies, clear button, toast → Task 6. ✅
- Route registered only under `import.meta.env.DEV` (tree-shaken) → Task 6. ✅
- Testing (pytest + Vitest/MSW, incl. prod guard + route gating) → Tasks 3, 4, 5, 6. ✅
- Mandated page workflow (taste → figma → frontend-design) → Task 6 note. ✅

**Placeholder scan:** No TBD/TODO; every code step has concrete content. ✅

**Type consistency:** `CapturedEmail` fields (`to_email`, `from_email`, `subject`, `body`, `created_at`) are consistent across model, serializers, factory, API types (`LetterSummary`/`LetterDetail`), and MSW fixtures. `devMailApi.list/get/clear` names match between module, tests, and page. Endpoint paths (`/api/v1/dev/letters/`, frontend `/dev/letters/`) are consistent. ✅
