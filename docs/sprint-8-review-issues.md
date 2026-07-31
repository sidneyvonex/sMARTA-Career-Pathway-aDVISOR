# Sprint 8: Parent Access — Code Review Issues

> **Audit provenance (2026-07-31):** This review record existed as an untracked
> workspace file when the audit branch was created from `main`. Its findings
> refer to earlier work and must be reproduced against the current code before
> they are accepted or fixed.

> Found by CodeRabbit code review on 2026-06-19.
> These issues should be opened on GitHub once repo write access is available.

---

## Issue 1: ChildProfileSerializer crashes on null/blank profile fields

**Role:** parent (authenticated, email verified)
**Page / URL:** `GET /api/v1/parents/children/:id/`
**Browser:** any (API-level bug)
**Mode:** both

**Type:** bug
**Severity:** high

**What happens**

When a parent views their child's profile via the child detail endpoint, the API returns a **500 Internal Server Error** if the child has not filled in optional profile fields (`date_of_birth`, `photo_url`, `bio`, `career_interests`).

The `ChildProfileSerializer` in `backend/parents/serializers.py:73-84` declares these fields without `allow_null=True` or `allow_blank=True`:

```python
class ChildProfileSerializer(serializers.Serializer):
    bio = serializers.CharField()           # crashes on empty string ''
    date_of_birth = serializers.DateField()  # crashes on None
    career_interests = serializers.CharField()  # crashes on empty string ''
    photo_url = serializers.URLField()       # crashes on None
```

But the database model (`accounts/models.py:68-71`) allows these values:

```python
bio = models.TextField(blank=True, default='')        # can be ''
date_of_birth = models.DateField(null=True, blank=True)  # can be None
career_interests = models.TextField(blank=True, default='')  # can be ''
photo_url = models.URLField(max_length=500, null=True, blank=True)  # can be None
```

**Database evidence:**
When a student registers and creates a profile via `POST /api/v1/students/profile/`, they only provide `mode` and `grade`. The remaining fields take these database defaults:
- `bio = ''` (empty string via `default=''`)
- `date_of_birth = NULL` (via `null=True`)
- `career_interests = ''` (empty string via `default=''`)
- `photo_url = NULL` (via `null=True, blank=True`)

DRF's `CharField()` without `allow_blank=True` rejects empty strings during serialization. DRF's `DateField()` and `URLField()` without `allow_null=True` reject `None`. Since `ChildProfileSerializer` is used for **read-only output serialization** (not input validation), these constraints are unnecessary and actively cause 500 errors.

**Why this is wrong:**
DRF serializers validate on both input (deserialization) AND output (serialization) by default. A `CharField()` that encounters `''` will raise `"This field may not be blank."` even when serializing — meaning the API crashes trying to **return** data that the database legitimately stores. This mismatch between the DB schema (which allows null/blank) and the serializer (which doesn't) is a classic DRF gotcha.

**Steps to reproduce**

1. Register a student account and create a profile with only `mode=self_guided` and `grade=9`
2. Do NOT fill in `date_of_birth`, `bio`, `career_interests`, or `photo_url`
3. Create a parent account linked to this student via the invite flow
4. Log in as the parent
5. Navigate to the child detail page → triggers `GET /api/v1/parents/children/:id/`
6. **Result:** 500 Internal Server Error

**Expected**

API returns the child's profile with `null` for unset date/URL fields and `""` for empty text fields, matching what the database stores. Parent sees their child's profile without errors.

**Proposed fix**

Add null/blank tolerance to optional fields in `backend/parents/serializers.py`:

```python
class ChildProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='user.id')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email')
    county = serializers.CharField(source='user.county', allow_null=True)
    grade = serializers.IntegerField()
    mode = serializers.CharField()
    bio = serializers.CharField(allow_blank=True)
    date_of_birth = serializers.DateField(allow_null=True)
    career_interests = serializers.CharField(allow_blank=True)
    photo_url = serializers.URLField(allow_null=True)
```

Also add a test: create a student with a bare profile (no bio, no date_of_birth, etc.), link a parent, and assert `GET /api/v1/parents/children/:id/` returns 200 with null/empty fields.

**Screenshot / recording:** N/A — API-level bug, no UI involved in root cause.

---

## Issue 2: N+1 query duplication in LinkedChildSerializer (get_top_pathway + get_fit_pct)

**Role:** parent (authenticated, email verified)
**Page / URL:** `GET /api/v1/parents/children/`
**Browser:** any (performance — API-level)
**Mode:** both

**Type:** performance
**Severity:** medium

**What happens**

The `LinkedChildSerializer` in `backend/parents/serializers.py:8-70` fires **duplicate database queries** for every child. Both `get_top_pathway()` (line 52-60) and `get_fit_pct()` (line 62-70) independently:

1. Query `RIASECAssessment.objects.filter(student_profile=p).order_by('-submitted_at').first()`
2. Query `Recommendation.objects.filter(assessment=assessment, rank=1)...first()`

This means for **every single child**, the same assessment lookup runs **twice** and the same recommendation lookup runs **twice**. On top of that, `get_quiz_status()`, `get_subject_count()`, and `get_counselor_assigned()` each fire their own queries per child.

**Database query analysis per child:**

| Method | Queries fired |
|--------|--------------|
| `get_quiz_status` | 1x `RIASECAssessment.filter().exists()` |
| `get_subject_count` | 1x `StudentSubject.filter().count()` |
| `get_counselor_assigned` | 1x `CounselorAssignment.filter().exists()` |
| `get_top_pathway` | 1x `RIASECAssessment.filter().first()` + 1x `Recommendation.filter().first()` |
| `get_fit_pct` | 1x `RIASECAssessment.filter().first()` + 1x `Recommendation.filter().first()` (DUPLICATE) |
| **Total per child** | **7 queries** |

For a parent with 3 children: **21 queries** + 1 for the link list = **22 queries** for a single API call. The `get_top_pathway` and `get_fit_pct` duplication alone accounts for 2 wasted queries per child.

**Why this is wrong:**
The view already does `select_related('student__student_profile')` which resolves the profile in 1 query. But each `SerializerMethodField` reaches back into the DB independently because serializers don't share state between methods. The two assessment lookups in `get_top_pathway` and `get_fit_pct` are the most egregious — identical queries returning the same row, just to read different columns.

**Steps to reproduce**

1. Log in as a parent with 3 linked children (each with RIASEC assessments)
2. Navigate to dashboard → triggers `GET /api/v1/parents/children/`
3. Enable Django Debug Toolbar or `django.db.connection.queries`
4. Observe 22+ queries for 3 children

**Expected**

The endpoint should use ≤5 queries regardless of child count:
1. Fetch parent links with `select_related`
2. Prefetch assessments with recommendations
3. Prefetch enrolled subject counts
4. Prefetch counselor assignments

**Proposed fix**

Option A (quick fix): Cache the assessment lookup across methods using a private dict on `self`:

```python
def _latest_assessment(self, profile):
    if not hasattr(self, '_assessment_cache'):
        self._assessment_cache = {}
    key = profile.pk
    if key not in self._assessment_cache:
        self._assessment_cache[key] = (
            RIASECAssessment.objects
            .filter(student_profile=profile)
            .order_by('-submitted_at')
            .first()
        )
    return self._assessment_cache[key]
```

Option B (proper fix): Use `Prefetch` and annotations in the view queryset:

```python
links = (
    ParentStudentLink.objects
    .filter(parent=request.user)
    .select_related('student__student_profile')
    .prefetch_related(
        Prefetch('student__student_profile__riasecassessment_set',
                 queryset=RIASECAssessment.objects.order_by('-submitted_at')[:1],
                 to_attr='latest_assessment'),
    )
    .annotate(
        subject_count=Count('student__student_profile__enrolled_subjects'),
        has_counselor=Exists(CounselorAssignment.objects.filter(
            student_profile=OuterRef('student__student_profile'), is_active=True)),
    )
)
```

**Screenshot / recording:** N/A — measure with Django Debug Toolbar or `connection.queries`.

---

## Issue 3: ParentStudentLink has no role enforcement at database level

**Role:** system_admin / any user with shell access
**Page / URL:** N/A (database integrity)
**Browser:** N/A
**Mode:** both

**Type:** improvement
**Severity:** medium

**What happens**

The `ParentStudentLink` model in `backend/parents/models.py:5-25` has a `unique_together` constraint on `(parent, student)` but **no validation** that `parent.role == 'parent'` or `student.role == 'student'`. The model accepts any two `User` records regardless of their role.

```python
class ParentStudentLink(models.Model):
    parent = models.ForeignKey(settings.AUTH_USER_MODEL, ...)  # no role check
    student = models.ForeignKey(settings.AUTH_USER_MODEL, ...)  # no role check
```

**Database evidence:**
The `User` model has a `role` CharField with choices `('student', 'counselor', 'school_admin', 'parent', 'system_admin')`. Nothing at the model layer prevents:

```python
# This would succeed — two students linked as parent↔child
ParentStudentLink.objects.create(parent=student_user, student=another_student)
# This would also succeed — a counselor as "parent"
ParentStudentLink.objects.create(parent=counselor_user, student=student_user)
```

Currently the only creation path is `AcceptInviteView` which checks `role='student'` on the student FK. But any future code path — admin panel, management command (`seed_test_users.py`), Django shell, data migration — could create invalid links.

**Why this is wrong:**
Defense in depth. The model is the last line of validation before data hits the database. Relying solely on view-level checks means any code path that bypasses the view (admin, shell, management commands, future API endpoints) can create corrupted data. Django's `clean()` / `full_clean()` pattern exists exactly for this case.

**Steps to reproduce**

1. Open Django shell: `python manage.py shell`
2. Create an invalid link:
   ```python
   from parents.models import ParentStudentLink
   from django.contrib.auth import get_user_model
   User = get_user_model()
   counselor = User.objects.filter(role='counselor').first()
   student = User.objects.filter(role='student').first()
   ParentStudentLink.objects.create(parent=counselor, student=student)  # succeeds!
   ```
3. The link is created with no error

**Expected**

The model should reject links where `parent.role != 'parent'` or `student.role != 'student'`.

**Proposed fix**

Add a `clean()` method to `ParentStudentLink`:

```python
from django.core.exceptions import ValidationError

class ParentStudentLink(models.Model):
    # ... fields ...

    def clean(self):
        if self.parent_id and self.parent.role != 'parent':
            raise ValidationError({'parent': 'Parent must have the parent role.'})
        if self.student_id and self.student.role != 'student':
            raise ValidationError({'student': 'Student must have the student role.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
```

Note: calling `full_clean()` in `save()` ensures validation runs even when not going through a form/serializer.

**Screenshot / recording:** N/A — database-level integrity issue.

---

## Issue 4: Broad `except Exception: pass` silently swallows all errors in RIASEC notification

**Role:** student (authenticated, completing RIASEC assessment)
**Page / URL:** `POST /api/v1/riasec/submit/`
**Browser:** any (API-level)
**Mode:** both

**Type:** bug
**Severity:** medium

**What happens**

In `backend/riasec/views.py:83-93`, the parent notification code uses a bare `except Exception: pass`:

```python
try:
    parent_links = ParentStudentLink.objects.filter(student=request.user)
    student_name = f'{request.user.first_name} {request.user.last_name}'.strip()
    for link in parent_links:
        create_notification(
            user=link.parent,
            type_code='child_assessment_complete',
            message=f'{student_name} has completed their career personality assessment.',
        )
except Exception:
    pass  # silently swallows EVERYTHING
```

This catches not just `DatabaseError` (the intended failure mode) but also:
- `TypeError` (if `create_notification` signature changes)
- `AttributeError` (if `link.parent` is unexpectedly None)
- `ImportError` (if a module fails to load)
- `KeyboardInterrupt` (if someone Ctrl+C's the server — actually `BaseException`, but still)

**Why this is wrong:**
Bare `except Exception: pass` is an anti-pattern because it makes bugs **invisible**. If `create_notification` is refactored and its signature changes, the notification silently stops working. Nobody gets an error in logs, nobody gets a Sentry alert, and the parent never receives the notification. The bug could persist for weeks before anyone notices parents aren't getting notified.

The intent was correct — don't crash the student's assessment submission because of a notification failure. But the implementation hides all errors instead of just database errors.

**Steps to reproduce**

1. Intentionally break `create_notification` (e.g., add a required parameter)
2. Submit a RIASEC assessment as a student with a linked parent
3. Assessment saves successfully (200 response)
4. Parent receives **no notification**
5. **No error appears in logs** — the bug is invisible

**Expected**

Notification failures should be logged so developers can detect and fix them. Only expected failure modes (e.g., database errors) should be caught.

**Proposed fix**

```python
import logging

logger = logging.getLogger(__name__)

# After the transaction.atomic() block:
try:
    parent_links = ParentStudentLink.objects.filter(student=request.user)
    student_name = f'{request.user.first_name} {request.user.last_name}'.strip()
    for link in parent_links:
        create_notification(
            user=link.parent,
            type_code='child_assessment_complete',
            message=f'{student_name} has completed their career personality assessment.',
        )
except Exception:
    logger.exception('Failed to notify parents for student %s', request.user.id)
```

This still prevents the student's assessment from failing, but makes the error **visible** in production logs.

**Screenshot / recording:** N/A — logging/debugging concern.

---

## Issue 5: Silent link failure in AcceptInviteView — parent gets 201 with no child linked

**Role:** parent (accepting invite)
**Page / URL:** `POST /api/v1/auth/accept-invite/`
**Browser:** any (API-level)
**Mode:** both

**Type:** bug · broken/empty state
**Severity:** medium

**What happens**

In `backend/accounts/views.py:311-316`, when a parent accepts an invite, the link creation silently fails if the student no longer exists or has changed roles:

```python
if student_id is not None:
    try:
        student = User.objects.get(pk=student_id, role='student')
        ParentStudentLink.objects.create(parent=user, student=student)
    except User.DoesNotExist:
        pass  # parent created, but NOT linked — no indication to user
```

The parent receives a `201 Account created successfully.` response and lands on a dashboard showing **"No child linked to your account yet. Contact your school to link your child's account."** They have no idea why the link failed — the invite email specifically said they'd be linked to their child.

**Database evidence:**
This can happen when:
1. Student's account is deleted between invite send and acceptance (stale `student_id` in token)
2. Student's role is changed (e.g., admin accidentally reassigns role)
3. Token contains a corrupted `student_id` (edge case)

The invite token (`make_parent_invite_token`) embeds `student_id` at creation time. If the student is deleted 48 hours later (within the token validity window), the parent creates an account but `User.objects.get(pk=student_id, role='student')` raises `DoesNotExist`, the except swallows it, and the parent sees an empty dashboard.

**Steps to reproduce**

1. Student A invites parent via `POST /api/v1/auth/invite-parent/` → token created with `student_id=A.id`
2. Student A's account is deleted (or role changed to something other than `student`)
3. Parent clicks the invite link within 48 hours
4. Parent fills in the form and submits → `POST /api/v1/auth/accept-invite/`
5. Response: `201 Account created successfully.`
6. Parent dashboard shows: "No child linked to your account yet."
7. Parent is confused — the invite said they'd see their child's data

**Expected**

The response should indicate whether the link was created. If it failed, the parent should see a message like "Account created, but we couldn't link your child. Please contact your school."

**Proposed fix**

Option A: Include link status in the response:
```python
link_created = False
if student_id is not None:
    try:
        student = User.objects.get(pk=student_id, role='student')
        ParentStudentLink.objects.create(parent=user, student=student)
        link_created = True
    except User.DoesNotExist:
        pass

message = 'Account created successfully.'
if student_id and not link_created:
    message = 'Account created, but the student could not be found. Contact your school to link your child.'
```

Option B: At minimum, log a warning:
```python
except User.DoesNotExist:
    logger.warning('Parent invite accepted but student_id=%s not found or wrong role', student_id)
```

**Screenshot / recording:** N/A — API response + empty state on parent dashboard.

---

## Issue 6: CounselorNoteCreateSerializer missing visible_to_parent field

**Role:** counselor (authenticated)
**Page / URL:** `POST /api/v1/counselors/notes/`
**Browser:** any
**Mode:** both

**Type:** improvement
**Severity:** low

**What happens**

The `CounselorNoteCreateSerializer` in `backend/counselors/serializers.py:17-19` only accepts `student_id` and `body`:

```python
class CounselorNoteCreateSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    body = serializers.CharField(max_length=2000)
```

A counselor **cannot set `visible_to_parent` at creation time**. They must:
1. Create the note (POST)
2. Copy the note ID from the response
3. Send a separate PATCH request to toggle `visible_to_parent`

This is unnecessary friction. If a counselor writes a note specifically for the parent to see, they have to make two API calls and two UI interactions instead of one.

**Why this matters:**
The `visible_to_parent` field was added in Sprint 8 (commit `8529e99`) and the PATCH endpoint was updated to accept it. But the creation serializer was not updated. This is a missed integration — the feature works end-to-end via PATCH but not via the simpler create flow.

**Steps to reproduce**

1. Log in as a counselor
2. Navigate to student detail → write a note
3. Want to share this note with the parent immediately
4. Must: create note → then separately PATCH to toggle visibility
5. No way to set visibility during creation

**Expected**

The counselor should be able to set `visible_to_parent` when creating a note. Default remains `False` (private by default).

**Proposed fix**

Add optional field to `CounselorNoteCreateSerializer`:
```python
class CounselorNoteCreateSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    body = serializers.CharField(max_length=2000)
    visible_to_parent = serializers.BooleanField(default=False, required=False)
```

And update `CounselorNotesView.post` to pass it through:
```python
note = CounselorNote.objects.create(
    counselor=request.user,
    student_id=serializer.validated_data['student_id'],
    body=serializer.validated_data['body'],
    visible_to_parent=serializer.validated_data.get('visible_to_parent', False),
)
```

**Screenshot / recording:** N/A.

---

## Issue 7: Hardcoded `#fff` and `rgba()` in parent.css violates CSS variable rule

**Role:** any parent user
**Page / URL:** `/parent/child/:id`
**Browser:** any
**Mode:** both (but especially relevant for future dark mode)

**Type:** ds drift
**Severity:** low

**What happens**

`frontend/src/styles/parent.css` contains hardcoded color values:

- **Line 30:** `color: #fff;` on `.child-detail__header`
- **Line 37:** `background: rgba(255, 255, 255, 0.2);` on `.child-detail__avatar`

The project constraint in `CLAUDE.md` states: "Do not hardcode hex colors — use CSS variables."

**Why this matters:**
If/when a dark mode is implemented, these hardcoded whites won't adapt. The gradient header (`--color-primary` → `--color-primary-hover`) might be fine in dark mode, but the hardcoded white text and avatar overlay would need manual updating. CSS variables like `var(--color-text-on-primary)` and `var(--color-overlay-light)` would adapt automatically.

Lines 58-59 use the correct pattern with fallbacks: `var(--color-surface, #fff)` and `var(--color-border, #e5e7eb)` — these are fine because the variable takes precedence.

**Steps to reproduce**

1. Open `frontend/src/styles/parent.css`
2. Search for `#fff` — found on line 30 (hardcoded, no variable)
3. Search for `rgba` — found on line 37 (hardcoded, no variable)

**Expected**

All color values should use CSS variables from the design system in `frontend/src/styles/theme.css`.

**Proposed fix**

Add two new CSS variables to `theme.css`:
```css
--color-text-on-primary: #fff;
--color-overlay-light: rgba(255, 255, 255, 0.2);
```

Then update `parent.css`:
```css
.child-detail__header {
    color: var(--color-text-on-primary);
}
.child-detail__avatar {
    background: var(--color-overlay-light);
}
```

**Screenshot / recording:** N/A — CSS convention issue.

---

## Issue 8: ChildDetailPage shows infinite loading skeletons for invalid child ID

**Role:** parent (authenticated)
**Page / URL:** `/parent/child/abc` or `/parent/child/NaN`
**Browser:** Chrome / Safari / mobile
**Mode:** both

**Type:** broken/empty state
**Severity:** low

**What happens**

If a parent navigates to `/parent/child/abc` (non-numeric ID), the `ChildDetailPage` component in `frontend/src/pages/parent/ChildDetailPage.tsx:18-26` disables the query but shows loading skeletons forever:

```typescript
const studentId = Number(id)  // NaN for "abc"

const detailQ = useQuery({
    queryKey: ['parent-child-detail', studentId],
    queryFn: () => parentApi.getChildDetail(studentId).then((r) => r.data.data),
    enabled: !Number.isNaN(studentId),  // false → query never fires
})

if (detailQ.isLoading) {  // isLoading is true when query is disabled
    return <skeletons />  // ← user sees this forever
}
```

When `enabled: false`, React Query sets `isLoading: true` and `data: undefined`. The component's first conditional check is `isLoading`, so it renders skeletons indefinitely. The error state check never triggers because no query was made.

**Steps to reproduce**

1. Log in as a parent
2. Manually navigate to `/parent/child/abc` in the URL bar
3. Page shows loading skeletons forever
4. No error message, no back button visible, no way to recover without using browser back

**Expected**

The page should show an error state with a "Back to dashboard" link when the child ID is not a valid number.

**Proposed fix**

Add an early return before the query hook:
```typescript
const studentId = Number(id)

if (Number.isNaN(studentId)) {
    return (
        <div className="child-detail">
            <Link to="/" className="child-detail__back">← Back to dashboard</Link>
            <div className="child-detail__section" style={{ textAlign: 'center' }}>
                <p>Invalid child ID. Please go back to your dashboard.</p>
            </div>
        </div>
    )
}
```

**Screenshot / recording:** N/A — navigate to `/parent/child/abc` to reproduce.
