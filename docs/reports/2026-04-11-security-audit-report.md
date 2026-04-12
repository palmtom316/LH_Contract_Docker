# 2026-04-11 Security Audit Status

Status: remediation implemented in worktree `v1-6-2-remediation`, verification complete for automated checks, manual production smoke checks still pending.

## Fixed Items

- Refresh token could authenticate protected request flows.
  Status: fixed
  Evidence: `backend/tests/test_auth.py`, `backend/tests/test_refresh_token.py`

- Password change did not revoke active refresh tokens.
  Status: fixed
  Evidence: `backend/tests/test_auth_hardening.py`

- Authenticated users could fetch business files without object-level authorization, and production config exposed `/uploads/`.
  Status: fixed
  Evidence: `backend/tests/test_file_compatibility.py`, `backend/tests/test_file_authorization.py`

- Feishu event callbacks were accepted without full verification.
  Status: fixed
  Evidence: `backend/tests/test_feishu_webhook_security.py`

- Upstream Excel import and dashboard period trend had weaker permission gates than sibling routes.
  Status: fixed
  Evidence: `backend/tests/test_permission_hardening.py`

- Normal app startup still implied schema mutation and release docs referenced a nonexistent compose service.
  Status: fixed
  Evidence: `backend/tests/test_release_contract.py`

- Frontend persisted refresh tokens in `localStorage` and diagnostic page exposed local auth material.
  Status: fixed
  Evidence: `frontend/src/utils/__tests__/authSession.spec.js`, `npm --prefix frontend run build`

## Automated Verification Summary

- Backend verification matrix: `50 passed`
- Frontend `authSession` tests: `2 passed`
- Frontend production build: passed
- `python3 scripts/verify_migration.py --safety-only`: passed
- `docker compose -f docker-compose.production.yml config --services`: `db`, `redis`, `backend`, `frontend`

## Remaining Release Gates

- Manual smoke checks against a live deployment are still required before production promotion.
- No remediation commit hash is recorded yet because these changes have not been committed in this session.
