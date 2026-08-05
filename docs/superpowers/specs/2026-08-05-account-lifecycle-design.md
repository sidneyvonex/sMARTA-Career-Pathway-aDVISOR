# Account Lifecycle: Provisioning, Self-Service, Admin Reset, Ownership Transfer

Date: 2026-08-05
Status: Approved for planning

## Problem

Several account-lifecycle gaps exist:

1. Creating a school (`SchoolListView.post`) only creates the `School` row — no login account is provisioned for the school, so a system admin has to separately invite a school admin via a different flow (`InviteStaffView`), and there is no direct link between "the school's registered email" and an actual account.
2. No user of any role can change their own name or password while logged in — `MeView` is GET-only.
3. No admin (system or school) can force-reset another user's password. The only reset mechanism is the self-service "forgot password" link flow (`PasswordResetView` / `PasswordResetConfirmView`), which requires the user to still have access to their own inbox and initiate it themselves.
4. There is no way to hand off the `school_admin` role for a school from one person to another (staff turnover). Today the only way to change a `User.school` / `User.role` is direct DB/Django-admin access.
5. (Verified, not a gap) No endpoint anywhere lets a user edit their own `email` — `StudentProfileSerializer.email` is `read_only`, `SchoolProfileView`'s editable fields are on the `School` model (contact email) not `User.email`, and no other role has a profile-edit endpoint that touches `User.email`. This spec adds an explicit guard on the new self-service endpoint (below) so this stays true as new code is added, and adds a regression test.

## Existing patterns being reused

- **Temp password generation**: `_temporary_password()` in `backend/school_admin/views.py` (used today for bulk student import — 12 chars, guarantees upper/lower/digit). Move to `backend/accounts/utils.py` so both `school_admin` and `system_admin` views can use it without a cross-app import into `school_admin`.
- **Async email**: `@shared_task` functions in `backend/accounts/emails.py`, dispatched with `.delay(...)`. New tasks follow the exact same shape (subject/message/from_email/recipient_list, plain `send_mail`).
- **Audit logging**: `log_action(actor, action, target_type, target_id, details, request)` from `system_admin/utils.py`, called after every mutating admin action today. New actions follow the same call shape.
- **Admin list/detail UI**: `ManagementTable` + `getSecondaryActions` + `ConfirmDialog` pattern already used on `SystemAdminSchoolsPage` and `SystemAdminUsersPage` for Activate/Deactivate/Edit. New "Reset password" and "Transfer admin" actions slot into the same pattern.

## A. School creation auto-provisions a school-admin account

`SchoolListView.post` (`backend/system_admin/views.py`):

- `email` becomes **required** (currently optional). Validate non-empty and not already used by an existing `User` — return `_error('An account with this email already exists.')` if so (matches `InviteStaffView`'s existing check).
- After `school.save()`, create the admin account inside the same flow (not a separate transaction — if user creation fails, the school creation should roll back too, so wrap both in `transaction.atomic()`):
  - `User.objects.create_user(email=school.email, password=<temp password>, first_name=school.name, last_name='Administrator', role='school_admin', school=school, county=school.county, is_email_verified=True)`
- Dispatch `send_school_admin_welcome_email.delay(user_id, email, first_name, temp_password, school_name)`.
- `log_action(action='school_admin_provisioned', target_type='user', target_id=<new user id>, details={'school_id': school.id, 'email': email})` in addition to the existing `school_created` log entry.
- Response payload unchanged in shape (still returns the school), no password ever appears in the HTTP response — it only ever leaves the system via the email task.

**Frontend** (`SystemAdminSchoolsPage.tsx`): no new fields needed — `email` was already optional in the create form (`createData.email`) and is now required. Change the input to `required` and update the helper text ("Used to create the school's login account"). Success toast becomes `'{name} created. Login details sent to {email}.'`.

## B. Self-service account settings

`backend/accounts/views.py`:

- `MeView` gains a `patch(self, request)`: accepts `first_name`, `last_name` from `request.data`. Any other key (including `email`) is ignored — only these two fields are ever read off `request.data`, so there's no path for a client to smuggle an email change through this endpoint. Runs basic non-empty validation, saves, returns `_success(data={'user': UserSerializer(request.user).data}, message='Profile updated.')`.
- New `ChangePasswordView(APIView)`, `POST /api/v1/auth/me/password/`, `permission_classes = [IsAuthenticated]`:
  - Body: `current_password`, `new_password`.
  - `if not request.user.check_password(current_password): return _error('Current password is incorrect.')`
  - Run `validate_password(new_password, user=request.user)` (Django's built-in validator, already used elsewhere per `DjangoValidationError` import in this file) — return its messages via `_error` on failure.
  - `request.user.set_password(new_password); request.user.save(update_fields=['password'])`.
  - `log_action(action='password_changed_self', target_type='user', target_id=request.user.id, request=request)`.
  - No email sent (self-initiated action the user is already aware of).

**Frontend**: new `AccountSettingsPage.tsx` at `frontend/src/pages/AccountSettingsPage.tsx`, routed for every authenticated role, linked from wherever the per-role top nav currently exposes a profile/account link. Two `form-field` groups following existing auth-page CSS classes: "Your name" (first/last name, `Save changes` button) and "Change password" (current/new/confirm, client-side confirm-match check, `Update password` button). Both use `react-hot-toast` per `CLAUDE.md` (`Profile updated.` / a new catalogue entry `Password updated. Please log in.`... actually since this doesn't force logout, the message is `'Password updated.'`). New API functions in `frontend/src/api/accounts.ts` (or wherever `MeView`'s GET is currently called from — reuse that file).

## C. Admin-initiated password reset

Three new endpoints, one shared email task:

- `backend/system_admin/views.py`: `UserPasswordResetView`, `POST /api/v1/system-admin/users/<id>/reset-password/`, `permission_classes = SYSTEM_ADMIN_PERMS`. Any user, any role.
- `backend/school_admin/views.py`: `CounselorPasswordResetView` and `StudentPasswordResetView` (or one view branching on a `role` path segment — implementer's call in the plan), scoped with `permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]` and a `.filter(school=request.user.school)` guard so a school admin cannot reset a user outside their own school (return 404, not 403, to avoid leaking existence of accounts in other schools — matches how other school-admin endpoints already scope by school).

All three share the same body:
- Generate temp password via the shared `_temporary_password()`.
- `user.set_password(temp_password); user.save(update_fields=['password'])`.
- Dispatch `send_password_reset_temp_email.delay(user_id, email, first_name, temp_password)`.
- `log_action(action='password_reset_by_admin', target_type='user', target_id=user.id, details={'reset_by': request.user.id}, request=request)`.
- `_success(message=f'Password reset. New credentials sent to {user.email}.')` — password itself never in the response.

**Frontend**: "Reset password" secondary action (with `ConfirmDialog`, mirroring the existing Activate/Deactivate confirm pattern) on:
- `SystemAdminUsersPage.tsx` — every user row.
- The school admin's counselor list (`CounselorManagementPage.tsx`) and student list (`SchoolStudentsPage.tsx`) — rows for that school only (already scoped since these pages only list the caller's own school).

## D. School-admin ownership transfer

`backend/system_admin/views.py`: `SchoolAdminTransferView`, `POST /api/v1/system-admin/schools/<id>/transfer-admin/`, `permission_classes = SYSTEM_ADMIN_PERMS`.

Body: `{ "new_admin_user_id": <int> }`.

- Look up the school (404 if missing).
- Look up `new_admin_user_id` — must exist (`_error` if not).
- Inside `transaction.atomic()`:
  - Find current school admin(s): `User.objects.filter(school=school, role='school_admin')`. For each: `user.school = None; user.save(update_fields=['school'])` — role stays `school_admin` (per design decision: "unlink from school", not demoted), so a system admin can reassign them to a different school later without a role change.
  - New admin: `new_admin.school = school; new_admin.role = 'school_admin'; new_admin.save(update_fields=['school', 'role'])` (promotes if they weren't already `school_admin`).
- Dispatch two email tasks: `send_school_admin_transfer_email.delay(user_id=new_admin.id, email=new_admin.email, first_name=new_admin.first_name, school_name=school.name, is_incoming=True)` and the same for each outgoing admin with `is_incoming=False` (one task function, a boolean flag picks the subject/body — avoids duplicating the Celery task).
- `log_action(action='school_admin_transferred', target_type='school', target_id=school.id, details={'old_admin_ids': [...], 'new_admin_id': new_admin.id}, request=request)`.
- `_success(message=f'{school.name} admin transferred to {new_admin.email}.')`.

**Frontend**: `SystemAdminSchoolsPage.tsx` detail drawer gains a "Transfer admin" button opening a small inline form — a text input for the new admin's email (looked up via a new lightweight `GET /api/v1/system-admin/users/lookup/?email=` or reuse the existing `getUsers` search — implementer's call in the plan) plus a confirm step, since this is a consequential action (existing `ConfirmDialog` pattern).

## Error handling

All four new/changed endpoints follow existing conventions: `_error(message)` for validation failures (400 implied by the helper's default), `_success(data=..., message=...)` on success, no bare `Response(...)`. Permission failures fall through to DRF's standard 403 via the `permission_classes` already established per role (`IsSystemAdmin`, `IsSchoolAdmin`).

## Testing

New `pytest-django` tests in `backend/tests/`:
- `test_school_admin_provisioning.py` (or added to `test_system_admin_views.py`): school creation without email fails; with a duplicate email fails; success creates both `School` and `User` (role, school FK, temp password login all verified via `factory_boy`); asserts the welcome email task was dispatched (mock `.delay` or use Celery eager mode per existing test settings — check `CELERY_TASK_ALWAYS_EAGER` in `config.settings.test`).
- `test_accounts_self_service.py`: `MeView.patch` updates name; **explicitly asserts posting `email` in the body does not change `request.user.email`** (the regression test for item 5 above); `ChangePasswordView` — wrong current password rejected, weak new password rejected (via `validate_password`), correct flow changes password and old password no longer works.
- `test_password_reset_by_admin.py`: system admin can reset any user; school admin can reset own-school counselor/student; school admin gets 404 resetting a user in a different school; email task dispatched; password actually changes (`user.check_password(temp_password)` after refetch).
- `test_school_admin_transfer.py`: transfer moves `school` FK correctly for both old and new admin; old admin's `role` stays `school_admin` with `school=None`; new admin promoted from another role if needed; both email tasks dispatched; nonexistent target user errors cleanly.

Frontend: Vitest + MSW handlers added to `frontend/src/test/msw/handlers.ts` for all new endpoints; a test file per new page/behavior (`AccountSettingsPage.test.tsx` at minimum) following the existing `frontend/src/test/*.test.tsx` structure.

## Out of scope

- Forcing a password change on first login after a temp password is used (no "must change password" flag exists on `User` today — could be a follow-up).
- Multi-admin-per-school support beyond what naturally falls out of "unlink, don't delete" (a school could end up with zero admins between transfer steps if the implementer chooses to run them sequentially instead of atomically — the atomic transaction above prevents this in the single-transfer-call case, but bulk/multi-step reassignment flows are not designed here).
- Rate limiting on the new admin-triggered endpoints (existing pattern only rate-limits public/unauthenticated endpoints like `PasswordResetView`; these are all behind `IsAuthenticated` + role checks already).
