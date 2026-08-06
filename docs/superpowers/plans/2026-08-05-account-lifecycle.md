# Account Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provision a school-admin login account automatically when a school is created, let every user manage their own name/password, let admins force-reset another user's password, and let a system admin transfer the school-admin role for a school to a different person — each notifying the relevant party by email.

**Architecture:** Backend additions live in the existing `accounts`, `school_admin`, and `system_admin` Django apps, reusing the `_success`/`_error` envelope, `log_action` audit trail, and Celery `@shared_task` email pattern already established. Frontend additions are one new shared page (`AccountSettingsPage`) plus new row actions on three existing admin management pages, following the existing `ManagementTable` / `ConfirmDialog` / React Query mutation pattern.

**Tech Stack:** Django REST Framework, Celery (eager in tests), React Query v5, react-hot-toast, Vitest + MSW 2, pytest-django + factory_boy.

## Global Constraints

- API envelope: `{ data, error, message }` success / `{ data: null, error: true, message }` failure — always via `_success`/`_error` from `accounts/response.py`, never a bare `Response(...)`.
- Every mutating admin action gets a `log_action(actor=..., action=..., target_type=..., target_id=..., details=..., request=request)` call (`system_admin/utils.py`).
- Every user-facing frontend action shows a `react-hot-toast` toast on success and failure, extracting `err.response?.data?.message` with a friendly fallback (CLAUDE.md §4).
- Never hardcode hex colors in new CSS — use existing `--color-*` variables (CLAUDE.md §3).
- Commit format: `feat|fix|test|refactor|docs(scope): description`, no `Co-Authored-By: Claude` line (CLAUDE.md §9).
- Backend tests: `cd backend && .\venv\Scripts\pytest tests/ -v`. Frontend tests: `cd frontend && npm test`.
- New endpoints require an MSW handler added to `frontend/src/test/msw/handlers.ts` before any frontend test exercises them (CLAUDE.md §7).

---

### Task 1: Move `_temporary_password()` to a shared module

**Files:**
- Create: `backend/accounts/utils.py`
- Modify: `backend/school_admin/views.py` (remove the local `_temporary_password` def at lines 51-61, import it instead)
- Test: `backend/tests/test_school_admin_views.py` (existing test, no changes needed — must still pass)

**Interfaces:**
- Produces: `accounts.utils._temporary_password() -> str` — a 12-character password guaranteed to contain at least one uppercase letter, one lowercase letter, and one digit. Every later task that generates a temp password imports this.

- [ ] **Step 1: Create the shared utility module**

```python
# backend/accounts/utils.py
import secrets
import string


def _temporary_password():
    """Return a readable password with a mix of character classes."""
    characters = string.ascii_letters + string.digits
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        *[secrets.choice(characters) for _ in range(9)],
    ]
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)
```

- [ ] **Step 2: Update `school_admin/views.py` to import instead of define**

Remove lines 51-61 (the `def _temporary_password():` block and its docstring/body) and the now-unused `import secrets` / `import string` at the top of the file (check nothing else in the file uses `secrets` or `string` before removing — grep first). Add:

```python
from accounts.utils import _temporary_password
```

near the other `from accounts...` imports (alongside `from accounts.permissions import ...`).

- [ ] **Step 3: Run the existing test suite to confirm nothing broke**

Run: `cd backend && .\venv\Scripts\pytest tests/test_school_admin_views.py -v -k temporary_password`
Expected: `test_import_students_creates_active_accounts_with_temporary_passwords` PASSES (same behavior, new import path).

- [ ] **Step 4: Commit**

```bash
git add backend/accounts/utils.py backend/school_admin/views.py
git commit -m "refactor(accounts): extract shared temp password generator"
```

---

### Task 2: School creation auto-provisions a school-admin account

**Files:**
- Modify: `backend/system_admin/views.py:421-478` (`SchoolListView.post`)
- Modify: `backend/accounts/emails.py` (add `send_school_admin_welcome_email` task)
- Test: `backend/tests/test_system_admin_views.py` (add new test class — check this file exists; if the school-creation test currently lives elsewhere, add it there instead — grep `SchoolListView` usage in `backend/tests/` first)

**Interfaces:**
- Consumes: `accounts.utils._temporary_password()` (Task 1).
- Produces: `accounts.emails.send_school_admin_welcome_email(user_id, email, first_name, temp_password, school_name)` — a Celery task, used nowhere else yet.

- [ ] **Step 1: Find the existing school-creation test file**

Run: `cd backend && grep -rn "system-admin/schools/'" tests/*.py | grep -i post`

Add the new test class to whichever file already covers `SchoolListView.post` (most likely `test_system_admin_views.py`).

- [ ] **Step 2: Write the failing tests**

```python
# add to the file found in Step 1
import pytest
from accounts.models import School
from django.contrib.auth import get_user_model
from tests.factories import SystemAdminFactory

User = get_user_model()


@pytest.mark.django_db
class TestSchoolCreationProvisionsAdmin:
    def setup_method(self):
        self.admin = SystemAdminFactory()

    def test_create_school_without_email_fails(self, client):
        client.force_authenticate(self.admin)
        response = client.post('/api/v1/system-admin/schools/', {
            'name': 'Kilimani Girls', 'county': 'kiambu', 'school_code': 'KIL-001',
        }, format='json')
        assert response.status_code == 400

    def test_create_school_with_taken_email_fails(self, client):
        client.force_authenticate(self.admin)
        User.objects.create_user(
            email='taken@kilimani.ac.ke', password='TestPass123!', role='counselor', county='kiambu',
        )
        response = client.post('/api/v1/system-admin/schools/', {
            'name': 'Kilimani Girls', 'county': 'kiambu', 'school_code': 'KIL-002',
            'email': 'taken@kilimani.ac.ke',
        }, format='json')
        assert response.status_code == 400
        assert 'already exists' in str(response.data['message'])

    def test_create_school_provisions_admin_account(self, client, mailoutbox):
        client.force_authenticate(self.admin)
        response = client.post('/api/v1/system-admin/schools/', {
            'name': 'Kilimani Girls', 'county': 'kiambu', 'school_code': 'KIL-003',
            'email': 'admin@kilimani.ac.ke',
        }, format='json')
        assert response.status_code == 201
        school = School.objects.get(school_code='KIL-003')
        user = User.objects.get(email='admin@kilimani.ac.ke')
        assert user.role == 'school_admin'
        assert user.school == school
        assert user.is_email_verified is True
        assert user.first_name == 'Kilimani Girls'
        assert user.last_name == 'Administrator'
        assert len(mailoutbox) == 1
        assert 'admin@kilimani.ac.ke' in mailoutbox[0].to
        assert user.check_password(_extract_temp_password(mailoutbox[0].body))


def _extract_temp_password(email_body):
    for line in email_body.splitlines():
        if line.strip() and not line.startswith(('Hi', 'A new', 'This', 'You can')):
            candidate = line.strip()
            if len(candidate) >= 8:
                return candidate
    raise AssertionError('Could not find temp password in email body')
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd backend && .\venv\Scripts\pytest tests/test_system_admin_views.py -v -k TestSchoolCreationProvisionsAdmin`
Expected: `test_create_school_without_email_fails` FAILS (email currently optional — creation succeeds with 201, not 400); the other two FAIL with `User.DoesNotExist` or similar.

- [ ] **Step 4: Add the email task**

In `backend/accounts/emails.py`, add:

```python
@shared_task
def send_school_admin_welcome_email(user_id, email, first_name, temp_password, school_name):
    send_mail(
        subject=f'Your Smarta Shauri admin account for {school_name}',
        message=(
            f"Hi {first_name},\n\n"
            f"A school administrator account has been created for {school_name} on Smarta Shauri.\n\n"
            f"Log in with:\n"
            f"Email: {email}\n"
            f"Temporary password: {temp_password}\n\n"
            f"{settings.FRONTEND_URL}/login\n\n"
            f"Please change your password after logging in."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )
```

- [ ] **Step 5: Implement `SchoolListView.post`**

In `backend/system_admin/views.py`, replace the `post` method body (lines 421-478) with:

```python
    def post(self, request):
        name = request.data.get('name', '').strip()
        county = request.data.get('county', '').strip()
        school_code = request.data.get('school_code', '').strip()
        phone = request.data.get('phone', '').strip()
        email = request.data.get('email', '').strip()

        if not name:
            return _error('School name is required.')
        if not county:
            return _error('County is required.')
        if county not in VALID_COUNTIES:
            return _error(f'County must be one of: {", ".join(sorted(VALID_COUNTIES))}.')
        if not school_code:
            return _error('School code is required.')
        if not email:
            return _error('Email is required.')
        if School.objects.filter(school_code=school_code).exists():
            return _error('A school with this code already exists.')
        if User.objects.filter(email=email).exists():
            return _error('An account with this email already exists.')

        school = School(
            name=name,
            county=county,
            school_code=school_code,
            phone=phone,
            email=email,
        )
        from django.core.exceptions import ValidationError
        try:
            school.full_clean()
        except ValidationError as e:
            messages = []
            for field_errors in e.message_dict.values():
                messages.extend(field_errors)
            return _error(messages[0] if messages else 'Invalid data.')

        temp_password = _temporary_password()
        with transaction.atomic():
            school.save()
            admin_user = User.objects.create_user(
                email=email,
                password=temp_password,
                first_name=name,
                last_name='Administrator',
                role='school_admin',
                school=school,
                county=county,
                is_email_verified=True,
            )

        send_school_admin_welcome_email.delay(
            user_id=admin_user.id,
            email=email,
            first_name=name,
            temp_password=temp_password,
            school_name=name,
        )

        log_action(
            actor=request.user,
            action='school_created',
            target_type='school',
            target_id=school.id,
            details={'name': name, 'county': county, 'school_code': school_code},
            request=request,
        )
        log_action(
            actor=request.user,
            action='school_admin_provisioned',
            target_type='user',
            target_id=admin_user.id,
            details={'school_id': school.id, 'email': email},
            request=request,
        )

        return _success(
            data={
                'id': school.id,
                'name': school.name,
                'county': school.county,
                'school_code': school.school_code,
                'phone': school.phone,
                'email': school.email,
                'logo_url': school.logo_url,
                'is_active': school.is_active,
            },
            message=f'{name} created.',
            status_code=status.HTTP_201_CREATED,
        )
```

Add the needed imports at the top of `backend/system_admin/views.py` if not already present: `from django.db import transaction`, `from accounts.utils import _temporary_password`, and add `send_school_admin_welcome_email` to the existing `from accounts.emails import ...` line (check what's already imported there first — grep `from accounts.emails import` in the file).

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && .\venv\Scripts\pytest tests/test_system_admin_views.py -v -k TestSchoolCreationProvisionsAdmin`
Expected: all 3 PASS.

- [ ] **Step 7: Run the full backend suite to check for regressions**

Run: `cd backend && .\venv\Scripts\pytest tests/ -v`
Expected: all pass. Pay attention to any existing test that creates a school via `POST /api/v1/system-admin/schools/` without an `email` — it will now need one added (fix the test, don't weaken the new validation).

- [ ] **Step 8: Commit**

```bash
git add backend/system_admin/views.py backend/accounts/emails.py backend/tests/test_system_admin_views.py
git commit -m "feat(system-admin): auto-provision school-admin account on school creation"
```

---

### Task 3: Frontend — require email on the create-school form

**Files:**
- Modify: `frontend/src/pages/system-admin/SystemAdminSchoolsPage.tsx:219-221` (email input), `:74-84` (success toast)
- Test: `frontend/src/test/system-admin/SystemAdmin.test.tsx`, `describe('SystemAdminSchoolsPage', ...)` block (lines 272-349)

**Interfaces:**
- Consumes: `systemAdminApi.createSchool` (`frontend/src/api/systemAdmin.ts:202-203`) — no signature change, `email` was already part of the payload type, just becomes functionally required via the form.

- [ ] **Step 1: Read the existing `SystemAdminSchoolsPage` test block**

Read `frontend/src/test/system-admin/SystemAdmin.test.tsx:272-349` — note the `renderPage()` helper (lines 284-292: `QueryClientProvider` + `MemoryRouter`) and the `'shows Create School button'` test (lines 325-330) as the closest existing pattern for interacting with the create form.

- [ ] **Step 2: Write the failing test**

Add after the `'shows Create School button'` test (after line 330's closing `})`):

```tsx
  it('requires an email to submit the create-school form', async () => {
    const user = userEvent.setup()
    renderPage()
    await user.click(await screen.findByRole('button', { name: 'Create school' }))
    const emailInput = await screen.findByLabelText('Email') as HTMLInputElement
    expect(emailInput).toBeRequired()
  })
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd frontend && npm test -- SystemAdmin`
Expected: FAIL — `emailInput` is not required today.

- [ ] **Step 4: Update the form**

In `SystemAdminSchoolsPage.tsx`, change the email input (around line 219-221) from:

```tsx
<input id="create-email" type="email" value={createData.email} onChange={event => setCreateData(value => ({ ...value, email: event.target.value }))} />
```

to:

```tsx
<input id="create-email" type="email" value={createData.email} onChange={event => setCreateData(value => ({ ...value, email: event.target.value }))} required />
```

Add a `form-hint` under it (matching the pattern used elsewhere, e.g. `SchoolProfilePage.tsx:120`):

```tsx
<p className="form-hint">Used to create the school's login account. A temporary password will be emailed here.</p>
```

Update the success toast in `createMutation.onSuccess` (around line 74-84) from `toast.success('School created successfully.')` to:

```tsx
toast.success(`${createData.name} created. Login details sent to ${createData.email}.`)
```

(Read `formData.email`/`createData.email` — note `createMutation`'s `onSuccess` callback doesn't currently receive the submitted `formData`; use the `createData` state captured in the closure, or thread it through via `mutationFn`'s return if the mutation is later changed to return the email — for now closure access to `createData` is correct since `setCreateData` reset happens after this line executes in the same synchronous callback... actually verify: the reset `setCreateData({...blank})` happens in the same `onSuccess` — so read `createData.email` into a local `const submittedEmail = createData.email` **before** calling `setCreateData` if there's any risk of it already being blank. Since React state updates within the same handler don't take effect until re-render, `createData` in this closure is still the submitted value — safe to use directly.)

- [ ] **Step 5: Run test to verify it passes**

Run: `cd frontend && npm test -- SystemAdmin`
Expected: PASS.

- [ ] **Step 6: Manually verify in the browser**

Run `cd backend && .\venv\Scripts\Activate.ps1 && python manage.py runserver` and `cd frontend && npm run dev` in separate terminals. Log in as a system admin, go to Schools, click Create school, try submitting without an email — confirm the browser's native required-field validation blocks it. Submit with an email — confirm the toast reads "… created. Login details sent to …".

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/system-admin/SystemAdminSchoolsPage.tsx frontend/src/test/
git commit -m "feat(system-admin): require email on create-school form"
```

---

### Task 4: Self-service name edit (`MeView.patch`)

**Files:**
- Modify: `backend/accounts/views.py:151-155` (`MeView`)
- Test: `backend/tests/test_accounts_views.py`

**Interfaces:**
- Produces: `PATCH /api/v1/auth/me/` accepting `{first_name?, last_name?}`, returning `_success(data={'user': UserSerializer(...).data})`. Ignores any other key in the body, including `email`.

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/test_accounts_views.py`:

```python
@pytest.mark.django_db
class TestMeViewPatch:
    def test_updates_first_and_last_name(self, client):
        user = VerifiedUserFactory(first_name='Old', last_name='Name')
        client.force_authenticate(user)
        response = client.patch('/api/v1/auth/me/', {
            'first_name': 'New', 'last_name': 'Person',
        }, format='json')
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.first_name == 'New'
        assert user.last_name == 'Person'

    def test_ignores_email_in_body(self, client):
        user = VerifiedUserFactory(email='original@test.com')
        client.force_authenticate(user)
        response = client.patch('/api/v1/auth/me/', {
            'first_name': 'New', 'email': 'hijacked@test.com',
        }, format='json')
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.email == 'original@test.com'

    def test_rejects_blank_first_name(self, client):
        user = VerifiedUserFactory(first_name='Old')
        client.force_authenticate(user)
        response = client.patch('/api/v1/auth/me/', {'first_name': '  '}, format='json')
        assert response.status_code == 400
        user.refresh_from_db()
        assert user.first_name == 'Old'
```

Add `VerifiedUserFactory` to this file's imports from `tests.factories` if not already imported (check the top of the file first).

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .\venv\Scripts\pytest tests/test_accounts_views.py -v -k TestMeViewPatch`
Expected: FAIL — `MeView` has no `patch` method (405).

- [ ] **Step 3: Implement `MeView.patch`**

In `backend/accounts/views.py`, replace the `MeView` class:

```python
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return _success(data={'user': UserSerializer(request.user).data})

    def patch(self, request):
        user = request.user
        updated = []
        for field in ('first_name', 'last_name'):
            if field in request.data:
                value = request.data[field]
                if not isinstance(value, str) or not value.strip():
                    return _error(f'{field.replace("_", " ").title()} is required.')
                setattr(user, field, value.strip())
                updated.append(field)
        if updated:
            user.save(update_fields=updated)
        return _success(data={'user': UserSerializer(user).data}, message='Profile updated.')
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .\venv\Scripts\pytest tests/test_accounts_views.py -v -k TestMeViewPatch`
Expected: all 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/accounts/views.py backend/tests/test_accounts_views.py
git commit -m "feat(accounts): allow self-service name edit via PATCH /auth/me/"
```

---

### Task 5: Self-service password change (`ChangePasswordView`)

**Files:**
- Modify: `backend/accounts/views.py` (add `ChangePasswordView` class near `PasswordResetConfirmView`)
- Modify: `backend/accounts/urls.py:9` (add route after `me/`)
- Test: `backend/tests/test_accounts_views.py`

**Interfaces:**
- Produces: `POST /api/v1/auth/me/password/` (name `auth-me-password`) accepting `{current_password, new_password}`.

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/test_accounts_views.py`:

```python
@pytest.mark.django_db
class TestChangePasswordView:
    def test_rejects_wrong_current_password(self, client):
        user = VerifiedUserFactory()
        user.set_password('CorrectPass123!')
        user.save()
        client.force_authenticate(user)
        response = client.post('/api/v1/auth/me/password/', {
            'current_password': 'WrongPass123!', 'new_password': 'NewPass456!',
        }, format='json')
        assert response.status_code == 400
        user.refresh_from_db()
        assert user.check_password('CorrectPass123!')

    def test_rejects_weak_new_password(self, client):
        user = VerifiedUserFactory()
        user.set_password('CorrectPass123!')
        user.save()
        client.force_authenticate(user)
        response = client.post('/api/v1/auth/me/password/', {
            'current_password': 'CorrectPass123!', 'new_password': '123',
        }, format='json')
        assert response.status_code == 400

    def test_changes_password_on_success(self, client):
        user = VerifiedUserFactory()
        user.set_password('CorrectPass123!')
        user.save()
        client.force_authenticate(user)
        response = client.post('/api/v1/auth/me/password/', {
            'current_password': 'CorrectPass123!', 'new_password': 'BrandNewPass789!',
        }, format='json')
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.check_password('BrandNewPass789!')
        assert not user.check_password('CorrectPass123!')

    def test_requires_authentication(self, client):
        response = client.post('/api/v1/auth/me/password/', {
            'current_password': 'a', 'new_password': 'b',
        }, format='json')
        assert response.status_code == 401
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .\venv\Scripts\pytest tests/test_accounts_views.py -v -k TestChangePasswordView`
Expected: FAIL — 404, route doesn't exist.

- [ ] **Step 3: Implement `ChangePasswordView`**

In `backend/accounts/views.py`, add near `PasswordResetConfirmView`:

```python
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_password = request.data.get('current_password', '')
        new_password = request.data.get('new_password', '')
        user = request.user

        if not user.check_password(current_password):
            return _error('Current password is incorrect.')

        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            return _error(e.messages[0] if e.messages else 'Invalid password.')

        user.set_password(new_password)
        user.save(update_fields=['password'])

        log_action(
            actor=user, action='password_changed_self', target_type='user',
            target_id=user.id, request=request,
        )
        return _success(message='Password updated.')
```

(`validate_password` and `DjangoValidationError` are already imported at the top of this file — lines 6 and 8.)

- [ ] **Step 4: Add the URL route**

In `backend/accounts/urls.py`, add after the `me/` line:

```python
    path('me/password/', views.ChangePasswordView.as_view(), name='auth-me-password'),
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && .\venv\Scripts\pytest tests/test_accounts_views.py -v -k TestChangePasswordView`
Expected: all 4 PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/accounts/views.py backend/accounts/urls.py backend/tests/test_accounts_views.py
git commit -m "feat(accounts): add self-service password change endpoint"
```

---

### Task 6: Frontend — `AccountSettingsPage`

**Files:**
- Modify: `frontend/src/api/auth.ts` (add `updateMe`, `changePassword`)
- Create: `frontend/src/pages/AccountSettingsPage.tsx`
- Modify: `frontend/src/App.tsx` (add `/account` route)
- Modify: `frontend/src/components/shell/Topbar.tsx` (add link to `/account`)
- Modify: `frontend/src/test/msw/handlers.ts` (add handlers for the two new endpoints)
- Test: `frontend/src/test/account-settings.test.tsx`

**Interfaces:**
- Consumes: `authApi.me()` (existing, `frontend/src/api/auth.ts:28`), `useAuthStore` (existing, used by `Topbar.tsx`).
- Produces: `authApi.updateMe(data: {first_name?: string; last_name?: string}) -> Promise<{data:{data:{user: User}}}>`, `authApi.changePassword(data: {current_password: string; new_password: string}) -> Promise<...>`.

- [ ] **Step 1: Add API functions**

In `frontend/src/api/auth.ts`, add to the `authApi` object (after `me:`):

```ts
  updateMe: (data: { first_name?: string; last_name?: string }) =>
    api.patch<{ data: { user: User } }>('/auth/me/', data),
  changePassword: (data: { current_password: string; new_password: string }) =>
    api.post('/auth/me/password/', data),
```

- [ ] **Step 2: Add MSW handlers**

In `frontend/src/test/msw/handlers.ts`, there is already a `http.get(\`${BASE}/me/\`, ...)` handler at line 187 (it returns 401 by default — individual test files override it per-test with `useAuthStore.setState` for auth state and `server.use(...)` where a specific `/auth/me/` response body matters). Add two new handlers directly after it, using the same `BASE` constant (`const BASE = '/api/v1/auth'` at the top of the file):

```ts
  http.patch(`${BASE}/me/`, async ({ request }) => {
    const body = await request.json() as { first_name?: string; last_name?: string }
    return HttpResponse.json({
      data: { user: { id: 1, email: 'jane@test.com', first_name: body.first_name ?? 'Jane', last_name: body.last_name ?? 'Doe', role: 'student', county: 'kiambu', is_email_verified: true } },
      error: null,
      message: 'Profile updated.',
    })
  }),

  http.post(`${BASE}/me/password/`, () => {
    return HttpResponse.json({ data: null, error: null, message: 'Password updated.' })
  }),
```

- [ ] **Step 3: Write the failing test**

Create `frontend/src/test/account-settings.test.tsx`. Follow the exact pattern used throughout this codebase's page tests (see `frontend/src/test/school-admin.test.tsx` lines 1-59 and `frontend/src/test/system-admin/SystemAdmin.test.tsx`): a local `renderPage()` wrapping the page in `QueryClientProvider` + `MemoryRouter`, auth seeded via `useAuthStore.setState(...)` in `beforeEach`, `react-hot-toast` mocked with `vi.mock` so success/failure is asserted by checking the mocked `toast.success`/`toast.error` calls (not by finding rendered toast text — there is no toast host mounted in these page-only tests), and per-test MSW overrides via `server.use(...)` from `'./msw/server'`:

```tsx
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import toast from 'react-hot-toast'
import { useAuthStore } from '../store/authStore'
import { server } from './msw/server'
import AccountSettingsPage from '../pages/AccountSettingsPage'

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn(), loading: vi.fn() },
}))

const makeClient = () => new QueryClient({ defaultOptions: { queries: { retry: false } } })

function setStudent() {
  useAuthStore.setState({
    user: {
      id: 1, email: 'jane@test.com', first_name: 'Jane', last_name: 'Doe',
      role: 'student' as any, county: 'kiambu', is_email_verified: true,
    },
    isAuthenticated: true, isEmailVerified: true, isLoading: false,
  })
}

describe('AccountSettingsPage', () => {
  let qc: QueryClient

  beforeEach(() => {
    qc = makeClient()
    setStudent()
  })

  afterEach(() => {
    qc.clear()
  })

  function renderPage() {
    return render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <AccountSettingsPage />
        </MemoryRouter>
      </QueryClientProvider>,
    )
  }

  it('submits updated name', async () => {
    renderPage()
    const firstNameInput = await screen.findByLabelText('First name')
    await userEvent.clear(firstNameInput)
    await userEvent.type(firstNameInput, 'Amina')
    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }))
    await waitFor(() => expect(toast.success).toHaveBeenCalledWith('Profile updated.'))
  })

  it('shows an error when current password is wrong', async () => {
    server.use(
      http.post('/api/v1/auth/me/password/', () => HttpResponse.json(
        { data: null, error: true, message: 'Current password is incorrect.' },
        { status: 400 },
      )),
    )
    renderPage()
    await userEvent.type(await screen.findByLabelText('Current password'), 'WrongPass1!')
    await userEvent.type(screen.getByLabelText('New password'), 'NewPass456!')
    await userEvent.type(screen.getByLabelText('Confirm new password'), 'NewPass456!')
    await userEvent.click(screen.getByRole('button', { name: 'Update password' }))
    await waitFor(() => expect(toast.error).toHaveBeenCalledWith('Current password is incorrect.'))
  })

  it('blocks submit when new password confirmation does not match', async () => {
    renderPage()
    await userEvent.type(await screen.findByLabelText('Current password'), 'CorrectPass123!')
    await userEvent.type(screen.getByLabelText('New password'), 'NewPass456!')
    await userEvent.type(screen.getByLabelText('Confirm new password'), 'Mismatch1!')
    await userEvent.click(screen.getByRole('button', { name: 'Update password' }))
    expect(await screen.findByText('Passwords do not match.')).toBeInTheDocument()
  })
})
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd frontend && npm test -- account-settings`
Expected: FAIL — module doesn't exist.

- [ ] **Step 5: Build the page**

Create `frontend/src/pages/AccountSettingsPage.tsx`:

```tsx
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { authApi } from '../api/auth'
import { useAuthStore } from '../store/authStore'
import '../styles/auth.css'

export default function AccountSettingsPage() {
  const { user, setUser } = useAuthStore()
  const queryClient = useQueryClient()

  const [firstName, setFirstName] = useState(user?.first_name ?? '')
  const [lastName, setLastName] = useState(user?.last_name ?? '')

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [confirmError, setConfirmError] = useState('')

  const nameMutation = useMutation({
    mutationFn: () => authApi.updateMe({ first_name: firstName, last_name: lastName }),
    onSuccess: (response) => {
      setUser(response.data.data.user)
      queryClient.invalidateQueries({ queryKey: ['me'] })
      toast.success('Profile updated.')
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message ?? 'Something went wrong. Please try again.')
    },
  })

  const passwordMutation = useMutation({
    mutationFn: () => authApi.changePassword({ current_password: currentPassword, new_password: newPassword }),
    onSuccess: () => {
      toast.success('Password updated.')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message ?? 'Something went wrong. Please try again.')
    },
  })

  function handleNameSubmit(event: React.FormEvent) {
    event.preventDefault()
    nameMutation.mutate()
  }

  function handlePasswordSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (newPassword !== confirmPassword) {
      setConfirmError('Passwords do not match.')
      return
    }
    setConfirmError('')
    passwordMutation.mutate()
  }

  return (
    <div className="auth-page">
      <section className="auth-card">
        <h1 className="auth-heading">Your name</h1>
        <form onSubmit={handleNameSubmit} className="auth-form">
          <div className="form-field">
            <label htmlFor="account-first-name">First name</label>
            <input id="account-first-name" value={firstName} onChange={e => setFirstName(e.target.value)} required />
          </div>
          <div className="form-field">
            <label htmlFor="account-last-name">Last name</label>
            <input id="account-last-name" value={lastName} onChange={e => setLastName(e.target.value)} required />
          </div>
          <button type="submit" className="btn-primary" disabled={nameMutation.isPending}>
            {nameMutation.isPending ? 'Saving…' : 'Save changes'}
          </button>
        </form>
      </section>

      <section className="auth-card">
        <h1 className="auth-heading">Change password</h1>
        <form onSubmit={handlePasswordSubmit} className="auth-form">
          <div className="form-field">
            <label htmlFor="account-current-password">Current password</label>
            <input id="account-current-password" type="password" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} required />
          </div>
          <div className="form-field">
            <label htmlFor="account-new-password">New password</label>
            <input id="account-new-password" type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} required />
          </div>
          <div className="form-field">
            <label htmlFor="account-confirm-password">Confirm new password</label>
            <input id="account-confirm-password" type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required />
          </div>
          {confirmError && <p className="auth-status error">{confirmError}</p>}
          <button type="submit" className="btn-primary" disabled={passwordMutation.isPending}>
            {passwordMutation.isPending ? 'Updating…' : 'Update password'}
          </button>
        </form>
      </section>
    </div>
  )
}
```

Check `useAuthStore` actually exposes a `setUser` action (`frontend/src/store/authStore.ts`) before relying on it — if the store instead only sets user at login/me-fetch time, use `queryClient.invalidateQueries` on whatever query key `authApi.me()` is registered under app-wide (grep `authApi.me()` usage) so the next read picks up the new name, and drop the `setUser` call if no such setter exists.

- [ ] **Step 6: Add the route**

In `frontend/src/App.tsx`, inside the `<Route element={<ProtectedRoute />}>` / `<Shell />` block, add a route available to every role — place it right after the opening of that block, before the role-specific `<Route element={<ProtectedRoute roles={[...]} />}>` groups:

```tsx
          <Route path="/account" element={<AccountSettingsPage />} />
```

Add the import near the other page imports: `import AccountSettingsPage from './pages/AccountSettingsPage'`.

- [ ] **Step 7: Add a nav entry point**

In `frontend/src/components/shell/Topbar.tsx`, add a link next to the existing avatar link (inside `.topbar__actions`, after the `<Link className="topbar__account-link" ...>` block):

```tsx
        <Link className="topbar__account-link" to="/account" aria-label="Account settings">
          Settings
        </Link>
```

Also add a case to `getPageContext` so the breadcrumb title is correct: `if (pathname === '/account') return { title: 'Account settings' }`.

- [ ] **Step 8: Run tests to verify they pass**

Run: `cd frontend && npm test -- account-settings`
Expected: all 3 PASS.

- [ ] **Step 9: Run full frontend suite for regressions**

Run: `cd frontend && npm test`
Expected: all pass (watch for any `Topbar` snapshot/structure test that now needs updating for the new link).

- [ ] **Step 10: Manually verify in the browser**

With both dev servers running, log in as any role, click the new "Settings" link in the topbar, change your name and save (confirm toast + name updates), then change your password with the wrong current password (confirm error) and then correctly (confirm success toast).

- [ ] **Step 11: Commit**

```bash
git add frontend/src/api/auth.ts frontend/src/pages/AccountSettingsPage.tsx frontend/src/App.tsx frontend/src/components/shell/Topbar.tsx frontend/src/test/
git commit -m "feat(frontend): add self-service account settings page"
```

---

### Task 7: Admin-initiated password reset — system admin (any user)

**Files:**
- Modify: `backend/system_admin/views.py` (add `UserPasswordResetView` near `UserDeactivateView`)
- Modify: `backend/system_admin/urls.py` (add route)
- Modify: `backend/accounts/emails.py` (add `send_password_reset_temp_email`)
- Test: `backend/tests/test_system_admin_views.py`

**Interfaces:**
- Consumes: `accounts.utils._temporary_password()` (Task 1).
- Produces: `POST /api/v1/system-admin/users/<id>/reset-password/` (name `system-admin-user-reset-password`); `accounts.emails.send_password_reset_temp_email(user_id, email, first_name, temp_password)` — a new Celery task, reused unchanged by Task 8.

- [ ] **Step 1: Write the failing tests**

```python
@pytest.mark.django_db
class TestSystemAdminUserPasswordReset:
    def setup_method(self):
        self.admin = SystemAdminFactory()

    def test_resets_any_users_password(self, client, mailoutbox):
        client.force_authenticate(self.admin)
        target = VerifiedUserFactory(role='counselor', email='counselor@test.com')
        old_hash = target.password
        response = client.post(f'/api/v1/system-admin/users/{target.id}/reset-password/')
        assert response.status_code == 200
        target.refresh_from_db()
        assert target.password != old_hash
        assert len(mailoutbox) == 1
        assert 'counselor@test.com' in mailoutbox[0].to

    def test_returns_404_for_missing_user(self, client):
        client.force_authenticate(self.admin)
        response = client.post('/api/v1/system-admin/users/999999/reset-password/')
        assert response.status_code == 404

    def test_non_system_admin_cannot_reset(self, client):
        target = VerifiedUserFactory(role='counselor')
        counselor = CounselorFactory()
        client.force_authenticate(counselor)
        response = client.post(f'/api/v1/system-admin/users/{target.id}/reset-password/')
        assert response.status_code == 403
```

(Import `CounselorFactory` if not already imported in this file.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .\venv\Scripts\pytest tests/test_system_admin_views.py -v -k TestSystemAdminUserPasswordReset`
Expected: FAIL — 404 route not found for all.

- [ ] **Step 3: Add the email task**

In `backend/accounts/emails.py`:

```python
@shared_task
def send_password_reset_temp_email(user_id, email, first_name, temp_password):
    send_mail(
        subject='Your Smarta Shauri password has been reset',
        message=(
            f"Hi {first_name},\n\n"
            f"An administrator has reset your Smarta Shauri password.\n\n"
            f"New temporary password: {temp_password}\n\n"
            f"{settings.FRONTEND_URL}/login\n\n"
            f"Please change your password after logging in. "
            f"If you did not expect this, contact your school or system administrator."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )
```

- [ ] **Step 4: Implement `UserPasswordResetView`**

In `backend/system_admin/views.py`, add near `UserDeactivateView`:

```python
class UserPasswordResetView(APIView):
    permission_classes = SYSTEM_ADMIN_PERMS

    def post(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return _error('User not found.', status.HTTP_404_NOT_FOUND)

        temp_password = _temporary_password()
        user.set_password(temp_password)
        user.save(update_fields=['password'])

        send_password_reset_temp_email.delay(
            user_id=user.id, email=user.email, first_name=user.first_name,
            temp_password=temp_password,
        )

        log_action(
            actor=request.user, action='password_reset_by_admin', target_type='user',
            target_id=user.id, details={'reset_by': request.user.id}, request=request,
        )
        return _success(message=f'Password reset. New credentials sent to {user.email}.')
```

Add `send_password_reset_temp_email` to the existing `from accounts.emails import ...` line and `from accounts.utils import _temporary_password` if not already present from Task 2.

- [ ] **Step 5: Add the URL route**

In `backend/system_admin/urls.py`, add after the `users/<int:user_id>/activate/` line:

```python
    path('users/<int:user_id>/reset-password/', views.UserPasswordResetView.as_view(), name='system-admin-user-reset-password'),
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && .\venv\Scripts\pytest tests/test_system_admin_views.py -v -k TestSystemAdminUserPasswordReset`
Expected: all 3 PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/system_admin/views.py backend/system_admin/urls.py backend/accounts/emails.py backend/tests/test_system_admin_views.py
git commit -m "feat(system-admin): add admin-initiated password reset for any user"
```

---

### Task 8: Admin-initiated password reset — school admin (scoped to own school)

**Files:**
- Modify: `backend/school_admin/views.py` (add `CounselorPasswordResetView`, `StudentPasswordResetView`)
- Modify: `backend/school_admin/urls.py` (add two routes)
- Test: `backend/tests/test_school_admin_views.py`

**Interfaces:**
- Consumes: `accounts.emails.send_password_reset_temp_email` (Task 7), `accounts.utils._temporary_password()` (Task 1).
- Produces: `POST /api/v1/school-admin/counselors/<id>/reset-password/`, `POST /api/v1/school-admin/students/<id>/reset-password/`.

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/test_school_admin_views.py` (adapt fixture names — `self.admin`, `self.school` — to match whatever setup this file's existing test classes use; check `setup_method` on an existing class like the one containing `test_import_students_creates_active_accounts_with_temporary_passwords` first):

```python
@pytest.mark.django_db
class TestSchoolAdminPasswordReset:
    def setup_method(self):
        self.school = SchoolFactory()
        self.admin = SchoolAdminFactory(school=self.school)
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_resets_own_school_counselor(self, mailoutbox):
        counselor = CounselorFactory(school=self.school)
        old_hash = counselor.password
        response = self.client.post(f'/api/v1/school-admin/counselors/{counselor.id}/reset-password/')
        assert response.status_code == 200
        counselor.refresh_from_db()
        assert counselor.password != old_hash
        assert len(mailoutbox) == 1

    def test_cannot_reset_counselor_at_another_school(self):
        other_counselor = CounselorFactory(school=SchoolFactory())
        response = self.client.post(f'/api/v1/school-admin/counselors/{other_counselor.id}/reset-password/')
        assert response.status_code == 404

    def test_resets_own_school_student(self, mailoutbox):
        profile = StudentProfileFactory(school=self.school, mode='school_linked')
        old_hash = profile.user.password
        response = self.client.post(f'/api/v1/school-admin/students/{profile.user.id}/reset-password/')
        assert response.status_code == 200
        profile.user.refresh_from_db()
        assert profile.user.password != old_hash
        assert len(mailoutbox) == 1

    def test_cannot_reset_student_at_another_school(self):
        other_profile = StudentProfileFactory(school=SchoolFactory(), mode='school_linked')
        response = self.client.post(f'/api/v1/school-admin/students/{other_profile.user.id}/reset-password/')
        assert response.status_code == 404
```

Check the file's existing imports already cover `SchoolFactory`, `SchoolAdminFactory`, `CounselorFactory`, `StudentProfileFactory`, `APIClient` — add whichever are missing.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .\venv\Scripts\pytest tests/test_school_admin_views.py -v -k TestSchoolAdminPasswordReset`
Expected: FAIL — 404 route not found for the reset attempts.

- [ ] **Step 3: Implement both views**

In `backend/school_admin/views.py`, add near `SchoolCounselorRemoveView`:

```python
class CounselorPasswordResetView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def post(self, request, counselor_id):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)
        try:
            counselor = User.objects.get(pk=counselor_id, role='counselor', school=school)
        except User.DoesNotExist:
            return _error('Counselor not found at your school.', status.HTTP_404_NOT_FOUND)

        temp_password = _temporary_password()
        counselor.set_password(temp_password)
        counselor.save(update_fields=['password'])

        send_password_reset_temp_email.delay(
            user_id=counselor.id, email=counselor.email, first_name=counselor.first_name,
            temp_password=temp_password,
        )
        log_action(
            actor=request.user, action='password_reset_by_admin', target_type='user',
            target_id=counselor.id, details={'reset_by': request.user.id}, request=request,
        )
        return _success(message=f'Password reset. New credentials sent to {counselor.email}.')


class StudentPasswordResetView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def post(self, request, student_id):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)
        try:
            profile = StudentProfile.objects.select_related('user').get(
                user_id=student_id, school=school,
            )
        except StudentProfile.DoesNotExist:
            return _error('Learner not found at your school.', status.HTTP_404_NOT_FOUND)
        student = profile.user

        temp_password = _temporary_password()
        student.set_password(temp_password)
        student.save(update_fields=['password'])

        send_password_reset_temp_email.delay(
            user_id=student.id, email=student.email, first_name=student.first_name,
            temp_password=temp_password,
        )
        log_action(
            actor=request.user, action='password_reset_by_admin', target_type='user',
            target_id=student.id, details={'reset_by': request.user.id}, request=request,
        )
        return _success(message=f'Password reset. New credentials sent to {student.email}.')
```

Add `from accounts.emails import send_password_reset_temp_email` to this file's imports.

- [ ] **Step 4: Add URL routes**

In `backend/school_admin/urls.py`, add:

```python
    path('counselors/<int:counselor_id>/reset-password/', views.CounselorPasswordResetView.as_view(), name='school-admin-counselor-reset-password'),
    path('students/<int:student_id>/reset-password/', views.StudentPasswordResetView.as_view(), name='school-admin-student-reset-password'),
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && .\venv\Scripts\pytest tests/test_school_admin_views.py -v -k TestSchoolAdminPasswordReset`
Expected: all 4 PASS.

- [ ] **Step 6: Run full backend suite**

Run: `cd backend && .\venv\Scripts\pytest tests/ -v`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add backend/school_admin/views.py backend/school_admin/urls.py backend/tests/test_school_admin_views.py
git commit -m "feat(school-admin): add scoped admin-initiated password reset for counselors and students"
```

---

### Task 9: Frontend — reset-password action on `SystemAdminUsersPage`

**Files:**
- Modify: `frontend/src/api/systemAdmin.ts` (add `resetUserPassword`)
- Modify: `frontend/src/pages/system-admin/SystemAdminUsersPage.tsx`
- Modify: `frontend/src/test/msw/handlers.ts`
- Test: `frontend/src/test/system-admin/SystemAdmin.test.tsx` (the `describe('SystemAdminUsersPage', ...)` block, lines 351-432)

**Interfaces:**
- Consumes: `systemAdminApi.deactivateUser`/`activateUser` pattern (existing, `systemAdmin.ts:223`) as the template.
- Produces: `systemAdminApi.resetUserPassword(id: number) -> Promise<{data:{message:string}}>`.

- [ ] **Step 1: Add the API function**

In `frontend/src/api/systemAdmin.ts`, add near `deactivateUser`/`activateUser`:

```ts
  resetUserPassword: (id: number) =>
    api.post<{ message: string }>(`/system-admin/users/${id}/reset-password/`),
```

- [ ] **Step 2: Add the MSW handler**

In `frontend/src/test/msw/handlers.ts`, add directly after the `http.post(/\/api\/v1\/system-admin\/users\/\d+\/activate\//, ...)` handler (around line 1914-1916):

```ts
  http.post(/\/api\/v1\/system-admin\/users\/\d+\/reset-password\//, () => {
    return HttpResponse.json({ data: null, error: null, message: 'Password reset. New credentials sent to jane@test.com.' })
  }),
```

- [ ] **Step 3: Extend the existing test**

In `frontend/src/test/system-admin/SystemAdmin.test.tsx`, inside the `describe('SystemAdminUsersPage', ...)` block (lines 351-432), the seeded fixture user is "Jane Doe" / `jane@test.com` (from the `http.get('/api/v1/system-admin/users/', ...)` handler). Add a new test after `'coordinates users with decision fields, details, overflow actions, and confirmation'` (after line 431's closing `})`), following that test's exact `More actions for Jane Doe` → `menuitem` → `ConfirmDialog` interaction shape, but asserting on the mocked `toast.success` call (per the `vi.mock('react-hot-toast', ...)` at the top of this file) rather than DOM text, since no toast host is mounted in these page-only tests:

```tsx
  it('resets a user password after confirmation', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.click(await screen.findByRole('button', { name: 'More actions for Jane Doe' }))
    await user.click(screen.getByRole('menuitem', { name: 'Reset password' }))
    expect(screen.getByRole('dialog', { name: 'Reset password for Jane Doe?' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Reset password' }))

    await waitFor(() => expect(toast.success).toHaveBeenCalledWith(
      'Password reset. New credentials sent to jane@test.com.',
    ))
  })
```

Add `import toast from 'react-hot-toast'` to this file's imports if not already present (check the top of the file first — it may already import `toast` for other assertions).

- [ ] **Step 4: Run test to verify it fails**

Run: `cd frontend && npm test -- SystemAdmin`
Expected: FAIL — no "Reset password" action exists yet.

- [ ] **Step 5: Add the mutation and action**

In `SystemAdminUsersPage.tsx`, add state and a mutation alongside `statusMutation`:

```tsx
  const [resetUser, setResetUser] = useState<UserItem | null>(null)

  const resetPasswordMutation = useMutation({
    mutationFn: (user: UserItem) => systemAdminApi.resetUserPassword(user.id),
    onSuccess: (response) => {
      toast.success(response.data.message)
      setResetUser(null)
    },
    onError: (error: any) => {
      const message = error.response?.data?.message
      toast.error(typeof message === 'string' ? message : 'Failed to reset password.')
    },
  })
```

Add a new secondary action to `getSecondaryActions` (in the `ManagementTable` props):

```tsx
          getSecondaryActions={user => [
            ...(user.role === 'student' ? [{
              id: 'download',
              label: 'Download PDF',
              disabled: downloadingId === user.id,
              onSelect: () => downloadStudentReport(user.id),
            }] : []),
            {
              id: 'reset-password',
              label: 'Reset password',
              disabled: resetPasswordMutation.isPending,
              onSelect: () => setResetUser(user),
            },
            {
              id: 'status',
              label: user.is_active ? 'Deactivate' : 'Activate',
              tone: user.is_active ? 'danger' as const : 'default' as const,
              disabled: statusMutation.isPending,
              onSelect: () => setStatusUser(user),
            },
          ]}
```

Add a second `ConfirmDialog` after the existing one:

```tsx
      <ConfirmDialog
        open={resetUser !== null}
        title={resetUser ? `Reset password for ${userName(resetUser)}?` : 'Reset password?'}
        description={resetUser
          ? `${userName(resetUser)} will receive a new temporary password by email and should sign in with it.`
          : 'A new temporary password will be emailed to this user.'}
        confirmLabel={resetPasswordMutation.isPending ? 'Resetting…' : 'Reset password'}
        pending={resetPasswordMutation.isPending}
        onClose={() => setResetUser(null)}
        onConfirm={() => { if (resetUser) resetPasswordMutation.mutate(resetUser) }}
      />
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd frontend && npm test -- SystemAdminUsersPage`
Expected: PASS.

- [ ] **Step 7: Manually verify in the browser**

Log in as system admin, go to Users, open a row's actions, click "Reset password", confirm — check the success toast appears.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/api/systemAdmin.ts frontend/src/pages/system-admin/SystemAdminUsersPage.tsx frontend/src/test/
git commit -m "feat(system-admin): add reset-password action to users table"
```

---

### Task 10: Frontend — reset-password action on `CounselorManagementPage`

**Files:**
- Modify: `frontend/src/api/schoolAdmin.ts` (add `resetCounselorPassword`)
- Modify: `frontend/src/pages/admin/CounselorManagementPage.tsx`
- Modify: `frontend/src/test/msw/handlers.ts`
- Test: file covering `CounselorManagementPage` — grep first

**Interfaces:**
- Consumes: `schoolAdminApi.removeCounselor` pattern (existing, `schoolAdmin.ts:180-181`) as the template.
- Produces: `schoolAdminApi.resetCounselorPassword(id: number) -> Promise<{data:{message:string}}>`.

- [ ] **Step 1: Add the API function**

In `frontend/src/api/schoolAdmin.ts`, add near `removeCounselor`:

```ts
  resetCounselorPassword: (counselorId: number) =>
    api.post<{ message: string }>('/school-admin/counselors/' + counselorId + '/reset-password/'),
```

- [ ] **Step 2: Add the MSW handler**

In `frontend/src/test/msw/handlers.ts`, find the existing `http.post('/api/v1/school-admin/counselors/:id/remove/', ...)` handler (grep for `school-admin/counselors` to locate it) and add directly after it:

```ts
  http.post('/api/v1/school-admin/counselors/:id/reset-password/', () => {
    return HttpResponse.json({ data: null, error: null, message: 'Password reset. New credentials sent to alice@school.co.ke.' })
  }),
```

- [ ] **Step 3: Extend the existing test**

The test file is `frontend/src/test/school-admin.test.tsx`. Its `describe('CounselorManagementPage', ...)` block (starting line 167) already has a seeded counsellor "Alice Wanjiku" with id `10` (see the `'removes a counsellor only after named confirmation'` test at lines 217-233, which posts to `/api/v1/school-admin/counselors/10/remove/`). This file mocks `react-hot-toast` (line 15-17) the same way `SystemAdmin.test.tsx` does, so assert on the mock rather than DOM text. Add a new test after the `'cancels counsellor removal without sending a request'` test (after line 251's closing `})`):

```tsx
  it('resets a counsellor password after confirmation', async () => {
    let resetCalled = false
    server.use(
      http.post('/api/v1/school-admin/counselors/10/reset-password/', () => {
        resetCalled = true
        return HttpResponse.json({ data: null, error: null, message: 'Password reset. New credentials sent to alice@school.co.ke.' })
      }),
    )
    renderPage()
    await screen.findByText('Alice Wanjiku')

    await userEvent.click(screen.getByRole('button', { name: 'More actions for Alice Wanjiku' }))
    await userEvent.click(screen.getByRole('menuitem', { name: 'Reset password' }))
    expect(screen.getByRole('dialog', { name: 'Reset password for Alice Wanjiku?' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Reset password' }))
    await waitFor(() => expect(resetCalled).toBe(true))
  })
```

(This mirrors the existing `removed`-flag pattern from the remove test at lines 217-233 rather than asserting on `toast` directly — either is valid in this file since `toast` is already mocked at the top; the flag approach needs no extra import.)

- [ ] **Step 4: Run test to verify it fails**

Run: `cd frontend && npm test -- school-admin`
Expected: FAIL.

- [ ] **Step 5: Add the mutation and action**

In `CounselorManagementPage.tsx`, add state and mutation alongside `removeMutation`:

```tsx
  const [resettingCounsellor, setResettingCounsellor] = useState<SchoolCounselor | null>(null)

  const resetPasswordMutation = useMutation({
    mutationFn: (id: number) => schoolAdminApi.resetCounselorPassword(id),
    onSuccess: (response) => {
      toast.success(response.data.message)
      setResettingCounsellor(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message ?? 'Failed to reset password.')
    },
  })
```

Update `getSecondaryActions` to add a second action:

```tsx
          getSecondaryActions={counsellor => [
            {
              id: 'reset-password',
              label: 'Reset password',
              disabled: resetPasswordMutation.isPending,
              onSelect: () => setResettingCounsellor(counsellor),
            },
            {
              id: 'remove',
              label: 'Remove',
              tone: 'danger',
              disabled: removeMutation.isPending,
              onSelect: () => setRemovingCounsellor(counsellor),
            },
          ]}
```

Add a second `ConfirmDialog` after the existing one (after the closing `/>` of the `removingCounsellor` dialog, before the closing `</>`):

```tsx
      <ConfirmDialog
        open={resettingCounsellor !== null}
        title={resettingCounsellor ? `Reset password for ${getCounsellorName(resettingCounsellor)}?` : 'Reset password?'}
        description={resettingCounsellor
          ? `${getCounsellorName(resettingCounsellor)} will receive a new temporary password by email.`
          : 'A new temporary password will be emailed to this counsellor.'}
        confirmLabel={resetPasswordMutation.isPending ? 'Resetting…' : 'Reset password'}
        pending={resetPasswordMutation.isPending}
        onClose={() => setResettingCounsellor(null)}
        onConfirm={() => { if (resettingCounsellor) resetPasswordMutation.mutate(resettingCounsellor.id) }}
      />
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd frontend && npm test -- school-admin`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/api/schoolAdmin.ts frontend/src/pages/admin/CounselorManagementPage.tsx frontend/src/test/
git commit -m "feat(school-admin): add reset-password action to counsellor table"
```

---

### Task 11: Frontend — reset-password action on `SchoolStudentsPage`

**Files:**
- Modify: `frontend/src/api/schoolAdmin.ts` (add `resetStudentPassword`)
- Modify: `frontend/src/pages/admin/SchoolStudentsPage.tsx`
- Modify: `frontend/src/test/msw/handlers.ts`
- Test: file covering `SchoolStudentsPage` — grep first

**Interfaces:**
- Consumes: `useDownloadReport`'s per-row button pattern already in this file (`SchoolStudentsPage.tsx:384-399`, the "report" column) as the template.
- Produces: `schoolAdminApi.resetStudentPassword(id: number) -> Promise<{data:{message:string}}>`.

- [ ] **Step 1: Add the API function**

In `frontend/src/api/schoolAdmin.ts`, add near `setGradeVerification`:

```ts
  resetStudentPassword: (studentId: number) =>
    api.post<{ message: string }>(`/school-admin/students/${studentId}/reset-password/`),
```

- [ ] **Step 2: Add the MSW handler**

In `frontend/src/test/msw/handlers.ts`, find the existing `http.get('/api/v1/school-admin/students/', ...)` handler (grep `school-admin/students` — the fixture there includes a student "Jane Muthoni", per `school-admin.test.tsx:298`) and add a new handler after the students-related block:

```ts
  http.post(/\/api\/v1\/school-admin\/students\/\d+\/reset-password\//, () => {
    return HttpResponse.json({ data: null, error: null, message: 'Password reset. New credentials sent to jane@school.test.' })
  }),
```

(Check the actual seeded email for "Jane Muthoni" in the `/school-admin/students/` handler's fixture data and use that exact email in the message, for consistency with the test assertion below.)

- [ ] **Step 3: Extend the existing test**

The test file is `frontend/src/test/school-admin.test.tsx`, `describe('SchoolStudentsPage', ...)` block (starting line ~272, `renderPage()` defined at line 285). The seeded fixture includes "Jane Muthoni" (line 298) and "Kevin Otieno" (line 299). This file mocks `react-hot-toast` at the top (lines 15-17). Add a new test after `'renders student list from MSW data'` (after line 300's closing `})`), using the same request-flag pattern as the counsellor-remove test in this same file:

```tsx
  it('resets a student password after confirmation', async () => {
    let resetCalled = false
    server.use(
      http.post(/\/api\/v1\/school-admin\/students\/\d+\/reset-password\//, () => {
        resetCalled = true
        return HttpResponse.json({ data: null, error: null, message: 'Password reset.' })
      }),
    )
    renderPage()
    await screen.findByText('Jane Muthoni')

    await userEvent.click(screen.getByRole('button', { name: 'Reset password for Jane Muthoni' }))
    expect(screen.getByRole('dialog', { name: 'Reset password for Jane Muthoni?' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Reset password' }))
    await waitFor(() => expect(resetCalled).toBe(true))
  })
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd frontend && npm test -- school-admin`
Expected: FAIL.

- [ ] **Step 5: Add a confirm dialog, mutation, and table column**

`SchoolStudentsPage.tsx` doesn't use `ConfirmDialog` today (its other actions are direct, like the report download) — add one for this action since resetting a password is more consequential. Add the import: `import ConfirmDialog from '../../components/common/management/ConfirmDialog'`.

Add state and mutation alongside `verificationMutation`:

```tsx
  const [resettingStudent, setResettingStudent] = useState<SchoolStudent | null>(null)

  const resetPasswordMutation = useMutation({
    mutationFn: (studentId: number) => schoolAdminApi.resetStudentPassword(studentId),
    onSuccess: (response) => {
      toast.success(response.data.message)
      setResettingStudent(null)
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message ?? 'Failed to reset password.')
    },
  })
```

Add a new column after the `report` column (around line 384-399):

```tsx
    {
      key: 'reset-password',
      label: 'Password',
      align: 'end',
      render: student => (
        <button
          type="button"
          className="btn-ghost"
          onClick={() => setResettingStudent(student)}
          disabled={resetPasswordMutation.isPending}
          aria-label={`Reset password for ${student.first_name} ${student.last_name}`}
        >
          Reset password
        </button>
      ),
    },
```

Add the dialog near the end of the JSX returned by the component (alongside the other modals — find where `importResult`/`marksPreview` panels are rendered and add after them, still inside the outermost `<div className="school-students-page">`):

```tsx
      <ConfirmDialog
        open={resettingStudent !== null}
        title={resettingStudent ? `Reset password for ${resettingStudent.first_name} ${resettingStudent.last_name}?` : 'Reset password?'}
        description={resettingStudent
          ? `${resettingStudent.first_name} ${resettingStudent.last_name} will receive a new temporary password by email.`
          : 'A new temporary password will be emailed to this learner.'}
        confirmLabel={resetPasswordMutation.isPending ? 'Resetting…' : 'Reset password'}
        pending={resetPasswordMutation.isPending}
        onClose={() => setResettingStudent(null)}
        onConfirm={() => { if (resettingStudent) resetPasswordMutation.mutate(resettingStudent.id) }}
      />
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd frontend && npm test -- school-admin`
Expected: PASS.

- [ ] **Step 7: Run full frontend suite**

Run: `cd frontend && npm test`
Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/api/schoolAdmin.ts frontend/src/pages/admin/SchoolStudentsPage.tsx frontend/src/test/
git commit -m "feat(school-admin): add reset-password action to learner table"
```

---

### Task 12: School-admin ownership transfer — backend

**Files:**
- Modify: `backend/system_admin/views.py` (add `SchoolAdminTransferView`)
- Modify: `backend/system_admin/urls.py`
- Modify: `backend/accounts/emails.py` (add `send_school_admin_transfer_email`)
- Test: `backend/tests/test_system_admin_views.py`

**Interfaces:**
- Produces: `POST /api/v1/system-admin/schools/<id>/transfer-admin/` body `{new_admin_user_id: number}`; `accounts.emails.send_school_admin_transfer_email(user_id, email, first_name, school_name, is_incoming)`.

- [ ] **Step 1: Write the failing tests**

```python
@pytest.mark.django_db
class TestSchoolAdminTransfer:
    def setup_method(self):
        self.admin = SystemAdminFactory()
        self.school = SchoolFactory()
        self.old_admin = SchoolAdminFactory(school=self.school)

    def test_transfers_admin_role(self, client, mailoutbox):
        new_admin = CounselorFactory(school=None)
        client.force_authenticate(self.admin)
        response = client.post(
            f'/api/v1/system-admin/schools/{self.school.id}/transfer-admin/',
            {'new_admin_user_id': new_admin.id}, format='json',
        )
        assert response.status_code == 200

        self.old_admin.refresh_from_db()
        assert self.old_admin.school is None
        assert self.old_admin.role == 'school_admin'

        new_admin.refresh_from_db()
        assert new_admin.school == self.school
        assert new_admin.role == 'school_admin'

        assert len(mailoutbox) == 2
        recipients = {email for message in mailoutbox for email in message.to}
        assert self.old_admin.email in recipients
        assert new_admin.email in recipients

    def test_rejects_nonexistent_target_user(self, client):
        client.force_authenticate(self.admin)
        response = client.post(
            f'/api/v1/system-admin/schools/{self.school.id}/transfer-admin/',
            {'new_admin_user_id': 999999}, format='json',
        )
        assert response.status_code == 400

    def test_rejects_nonexistent_school(self, client):
        client.force_authenticate(self.admin)
        new_admin = CounselorFactory(school=None)
        response = client.post(
            '/api/v1/system-admin/schools/999999/transfer-admin/',
            {'new_admin_user_id': new_admin.id}, format='json',
        )
        assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .\venv\Scripts\pytest tests/test_system_admin_views.py -v -k TestSchoolAdminTransfer`
Expected: FAIL — 404, route doesn't exist.

- [ ] **Step 3: Add the email task**

In `backend/accounts/emails.py`:

```python
@shared_task
def send_school_admin_transfer_email(user_id, email, first_name, school_name, is_incoming):
    if is_incoming:
        subject = f'You are now the school admin for {school_name}'
        message = (
            f"Hi {first_name},\n\n"
            f"You have been made the school administrator for {school_name} on Smarta Shauri.\n\n"
            f"{settings.FRONTEND_URL}/login"
        )
    else:
        subject = f'You are no longer the school admin for {school_name}'
        message = (
            f"Hi {first_name},\n\n"
            f"You are no longer the school administrator for {school_name} on Smarta Shauri. "
            f"If you believe this is a mistake, contact your system administrator."
        )
    send_mail(
        subject=subject, message=message,
        from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[email],
    )
```

- [ ] **Step 4: Implement `SchoolAdminTransferView`**

In `backend/system_admin/views.py`, add near `SchoolDetailView`:

```python
class SchoolAdminTransferView(APIView):
    permission_classes = SYSTEM_ADMIN_PERMS

    def post(self, request, school_id):
        try:
            school = School.objects.get(pk=school_id)
        except School.DoesNotExist:
            return _error('School not found.', status.HTTP_404_NOT_FOUND)

        new_admin_id = request.data.get('new_admin_user_id')
        try:
            new_admin = User.objects.get(pk=new_admin_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return _error('The selected user could not be found.')

        with transaction.atomic():
            old_admins = list(User.objects.filter(school=school, role='school_admin'))
            for old_admin in old_admins:
                old_admin.school = None
                old_admin.save(update_fields=['school'])

            new_admin.school = school
            new_admin.role = 'school_admin'
            new_admin.save(update_fields=['school', 'role'])

        send_school_admin_transfer_email.delay(
            user_id=new_admin.id, email=new_admin.email, first_name=new_admin.first_name,
            school_name=school.name, is_incoming=True,
        )
        for old_admin in old_admins:
            send_school_admin_transfer_email.delay(
                user_id=old_admin.id, email=old_admin.email, first_name=old_admin.first_name,
                school_name=school.name, is_incoming=False,
            )

        log_action(
            actor=request.user, action='school_admin_transferred', target_type='school',
            target_id=school.id,
            details={'old_admin_ids': [a.id for a in old_admins], 'new_admin_id': new_admin.id},
            request=request,
        )
        return _success(message=f'{school.name} admin transferred to {new_admin.email}.')
```

Add `send_school_admin_transfer_email` to the `from accounts.emails import ...` line.

- [ ] **Step 5: Add the URL route**

In `backend/system_admin/urls.py`, add after `schools/<int:school_id>/activate/`:

```python
    path('schools/<int:school_id>/transfer-admin/', views.SchoolAdminTransferView.as_view(), name='system-admin-school-transfer-admin'),
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && .\venv\Scripts\pytest tests/test_system_admin_views.py -v -k TestSchoolAdminTransfer`
Expected: all 3 PASS.

- [ ] **Step 7: Run full backend suite**

Run: `cd backend && .\venv\Scripts\pytest tests/ -v`
Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add backend/system_admin/views.py backend/system_admin/urls.py backend/accounts/emails.py backend/tests/test_system_admin_views.py
git commit -m "feat(system-admin): add school-admin ownership transfer endpoint"
```

---

### Task 13: School-admin ownership transfer — frontend

**Files:**
- Modify: `frontend/src/api/systemAdmin.ts` (add `transferSchoolAdmin`, `getUsers` reuse)
- Modify: `frontend/src/pages/system-admin/SystemAdminSchoolsPage.tsx`
- Modify: `frontend/src/test/msw/handlers.ts`
- Test: `frontend/src/test/system-admin/SystemAdmin.test.tsx` (the `describe('SystemAdminSchoolsPage', ...)` block, lines 272-349)

**Interfaces:**
- Consumes: `systemAdminApi.getUsers` (existing, `systemAdmin.ts:217-218`) to look up the target user by email.
- Produces: `systemAdminApi.transferSchoolAdmin(schoolId: number, newAdminUserId: number) -> Promise<{data:{message:string}}>`.

- [ ] **Step 1: Add the API function**

In `frontend/src/api/systemAdmin.ts`:

```ts
  transferSchoolAdmin: (schoolId: number, newAdminUserId: number) =>
    api.post<{ message: string }>(`/system-admin/schools/${schoolId}/transfer-admin/`, {
      new_admin_user_id: newAdminUserId,
    }),
```

- [ ] **Step 2: Add the MSW handler**

In `frontend/src/test/msw/handlers.ts`, add directly after the `http.post(/\/api\/v1\/system-admin\/schools\/\d+\/activate\//, ...)` handler (around line 1880-1882):

```ts
  http.post(/\/api\/v1\/system-admin\/schools\/\d+\/transfer-admin\//, () => {
    return HttpResponse.json({ data: null, error: null, message: 'Starehe Boys Centre admin transferred to bob@test.com.' })
  }),
```

The transfer flow first calls `GET /api/v1/system-admin/users/` (via `getUsers({ search: email })`) to resolve the typed email to a user id — the existing handler at line 1884 already returns a fixture including `{ id: 2, first_name: 'Bob', last_name: 'Smith', email: 'bob@test.com', ... }`, which the new test (Step 3) will use as the transfer target.

- [ ] **Step 3: Extend the existing test**

In `frontend/src/test/system-admin/SystemAdmin.test.tsx`, inside `describe('SystemAdminSchoolsPage', ...)` (lines 272-349), the seeded fixture school is "Starehe Boys Centre" (id 1) and the existing `'coordinates school records with view, overflow, details, and confirmed status actions'` test (lines 332-348) already shows how to open its detail drawer. Add a new test after it (after line 348's closing `})`):

```tsx
  it('transfers the school admin to a new user', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.click(await screen.findByRole('button', { name: 'View Starehe Boys Centre' }))
    await user.click(screen.getByRole('button', { name: 'Transfer admin' }))
    await user.type(screen.getByLabelText('New admin email'), 'bob@test.com')
    await user.click(screen.getByRole('button', { name: 'Transfer' }))

    await waitFor(() => expect(toast.success).toHaveBeenCalledWith(
      'Starehe Boys Centre admin transferred to bob@test.com.',
    ))
  })
```

Add `import toast from 'react-hot-toast'` to this file's imports if Task 9 didn't already add it.

- [ ] **Step 4: Run test to verify it fails**

Run: `cd frontend && npm test -- SystemAdmin`
Expected: FAIL — no "Transfer admin" button exists yet.

- [ ] **Step 5: Add the transfer form to the detail drawer**

In `SystemAdminSchoolsPage.tsx`, add state:

```tsx
  const [transferSchool, setTransferSchool] = useState<SchoolItem | null>(null)
  const [transferEmail, setTransferEmail] = useState('')
```

Add a mutation that first looks up the user by email via `getUsers`, then calls `transferSchoolAdmin`:

```tsx
  const transferMutation = useMutation({
    mutationFn: async ({ schoolId, email }: { schoolId: number; email: string }) => {
      const lookup = await systemAdminApi.getUsers({ search: email })
      const match = lookup.data.data.results.find(u => u.email.toLowerCase() === email.toLowerCase())
      if (!match) throw new Error('NOT_FOUND')
      return systemAdminApi.transferSchoolAdmin(schoolId, match.id)
    },
    onSuccess: (response) => {
      invalidateSchools()
      toast.success(response.data.message)
      setTransferSchool(null)
      setTransferEmail('')
    },
    onError: (error: any) => {
      if (error?.message === 'NOT_FOUND') {
        toast.error('No user found with that email.')
        return
      }
      const message = error.response?.data?.message
      toast.error(typeof message === 'string' ? message : 'Failed to transfer admin.')
    },
  })
```

Add a "Transfer admin" button inside the `DetailDrawer` (after the existing `<dl>`, still inside `{detailSchool && (...)}`):

```tsx
            <button type="button" className="btn-ghost" onClick={() => { setTransferSchool(detailSchool); setTransferEmail('') }}>
              Transfer admin
            </button>
```

Add a small inline form rendered when `transferSchool` is set (place it as a sibling to the `DetailDrawer`, e.g. right after it, reusing `.sysadmin-create-form` styling):

```tsx
      {transferSchool && (
        <form
          className="sysadmin-create-form"
          onSubmit={(event: FormEvent) => {
            event.preventDefault()
            transferMutation.mutate({ schoolId: transferSchool.id, email: transferEmail })
          }}
        >
          <div className="sysadmin-create-form__heading">
            <div>
              <h2>Transfer admin for {transferSchool.name}</h2>
              <p>Enter the email of the existing account to make the new school admin. They'll be promoted if needed, and the outgoing admin will be unlinked from this school.</p>
            </div>
            <button type="button" className="btn-ghost" onClick={() => setTransferSchool(null)}>Close form</button>
          </div>
          <div className="form-field">
            <label htmlFor="transfer-admin-email">New admin email</label>
            <input id="transfer-admin-email" type="email" value={transferEmail} onChange={event => setTransferEmail(event.target.value)} required />
          </div>
          <div className="sysadmin-create-form__actions">
            <button type="submit" className="btn-primary" disabled={transferMutation.isPending}>
              {transferMutation.isPending ? 'Transferring…' : 'Transfer'}
            </button>
          </div>
        </form>
      )}
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd frontend && npm test -- SystemAdmin`
Expected: PASS.

- [ ] **Step 7: Run full frontend suite**

Run: `cd frontend && npm test`
Expected: all pass.

- [ ] **Step 8: Manually verify in the browser**

Log in as system admin, open a school's detail drawer, click "Transfer admin", enter an existing user's email, submit — confirm the success toast and that the school's counselor/admin count updates on refetch.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/api/systemAdmin.ts frontend/src/pages/system-admin/SystemAdminSchoolsPage.tsx frontend/src/test/
git commit -m "feat(system-admin): add school-admin ownership transfer UI"
```

---

## Post-implementation

- [ ] Run `coderabbit:code-review` on the full diff per CLAUDE.md §8 before merging.
- [ ] Run `superpowers:verification-before-completion` before declaring the branch done.
