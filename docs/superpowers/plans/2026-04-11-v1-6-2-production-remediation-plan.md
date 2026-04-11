# v1.6.2 Production Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the current production release blockers in local `1.6.2` so the branch can be promoted with controlled auth boundaries, authorized file access, verified webhooks, aligned deployment docs, and repeatable release validation.

**Architecture:** This remediation keeps the current FastAPI + Vue + Docker Compose architecture, but tightens trust boundaries at the request edge and moves release safety from implicit startup behavior to explicit release workflow. The implementation order is intentionally sequential: fix auth and file exposure first, then permission parity and webhook trust, then release contract and frontend session hardening, then finish with verification and documentation alignment.

**Tech Stack:** FastAPI, SQLAlchemy async, PyJWT, pytest/httpx, Vue 3, Vite, Nginx, Docker Compose, Alembic, shell release scripts.

---

## Planned File Changes

- Modify: `backend/app/services/auth.py`
  - Enforce `access` token type at all request-auth entry points.
  - Keep refresh-token verification limited to refresh-specific flows.
- Modify: `backend/app/routers/auth.py`
  - Revoke all active refresh tokens after successful password change.
- Modify: `backend/tests/test_auth.py`
  - Add request-level regression test proving refresh tokens cannot call protected endpoints.
- Modify: `backend/tests/test_auth_hardening.py`
  - Add password-change token revocation regression test.
- Modify: `backend/app/routers/common.py`
  - Add object-level authorization checks before serving MinIO/local files.
- Add: `backend/app/services/file_authorization.py`
  - Centralize allowlisted file-key ownership resolution and permission checks for business files.
- Modify: `backend/tests/test_file_compatibility.py`
  - Keep path-transport tests and add authorization-failure coverage.
- Add: `backend/tests/test_file_authorization.py`
  - Focused tests for allowed vs denied access to file-backed business objects.
- Modify: `nginx/nginx.conf`
  - Remove direct public `/uploads/` exposure.
  - Restrict production docs endpoints.
- Modify: `docker-compose.production.yml`
  - Stop mounting `uploads_data` into frontend static root.
- Modify: `backend/app/routers/feishu.py`
  - Verify every callback, not only `url_verification`.
- Add: `backend/tests/test_feishu_webhook_security.py`
  - Cover unsigned/forged callback rejection and valid callback acceptance.
- Modify: `backend/app/routers/contracts_upstream.py`
  - Align import permission with create permission.
- Modify: `backend/app/routers/dashboard.py`
  - Require `VIEW_DASHBOARD` for trend endpoint.
- Add: `backend/tests/test_permission_hardening.py`
  - Cover import and dashboard permission parity.
- Modify: `backend/app/main.py`
  - Remove implicit schema mutation from normal app startup.
  - Mount health router if detailed checks are meant to be part of release validation.
- Modify: `backend/app/database.py`
  - Stop calling `Base.metadata.create_all()` during normal production boot if explicit migrations are the contract.
- Modify: `backend/app/core/db_check.py`
  - Retain schema inspection helpers for diagnostics, but remove automatic DDL execution from normal startup.
- Add: `backend/tests/test_release_contract.py`
  - Lock in mounted health routes and startup behavior.
- Modify: `frontend/src/utils/authSession.js`
  - Remove long-lived refresh token persistence from `localStorage`.
- Modify: `frontend/src/stores/user.js`
  - Align in-memory/session behavior with the new token contract.
- Modify: `frontend/src/utils/request.js`
- Modify: `frontend/src/utils/request_optimized.js`
  - Ensure refresh flow and logout behavior match the new storage contract.
- Modify: `frontend/public/diagnose.html`
  - Remove or production-gate the diagnostic page.
- Add: `frontend/src/utils/__tests__/authSession.spec.js`
  - Lock token persistence behavior.
- Modify: `docs/release/deployment-checklist-hardening.md`
  - Fix invalid service names and make smoke checks match real mounted routes.
- Modify: `docs/release/upgrade-runbook-v1.6-hardening.md`
  - Make release steps explicit about backup, migration, and verification gates.

## Delivery Notes

- This plan intentionally groups multiple subsystems because they are all tied to one release gate: whether `1.6.2` is safe to promote to production.
- Implementation should not start until this document is approved.
- Tasks 1 through 4 are release blockers and must land before any production promotion.
- Do not parallelize startup-behavior changes with database migration execution changes unless a reviewer confirms the final release contract.

### Task 1: Lock Request Auth to Access Tokens and Revoke Sessions on Password Change

**Files:**
- Modify: `backend/app/services/auth.py`
- Modify: `backend/app/routers/auth.py`
- Modify: `backend/tests/test_auth.py`
- Modify: `backend/tests/test_auth_hardening.py`
- Test: `backend/tests/test_refresh_token.py`

- [ ] **Step 1: Add a failing request-auth regression test for refresh-token misuse**

```python
@pytest.mark.asyncio
async def test_refresh_token_cannot_call_me_endpoint(client: AsyncClient, test_user: User):
    login_response = await client.post(
        "/api/v1/auth/login/json",
        json={"username": "testuser", "password": "testpass123"},
    )
    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )

    assert response.status_code == 401
```

- [ ] **Step 2: Add a failing regression test for password change session revocation**

```python
@pytest.mark.asyncio
async def test_change_password_revokes_existing_refresh_tokens(
    client: AsyncClient,
    test_db: AsyncSession,
    test_user: User,
):
    login_response = await client.post(
        "/api/v1/auth/login/json",
        json={"username": "testuser", "password": "testpass123"},
    )
    assert login_response.status_code == 200
    payload = login_response.json()

    change_response = await client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {payload['access_token']}"},
        json={"old_password": "testpass123", "new_password": "ValidPass456"},
    )
    assert change_response.status_code == 200

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": payload["refresh_token"]},
    )
    assert refresh_response.status_code == 401
```

- [ ] **Step 3: Run the focused tests to verify they fail**

Run:

```bash
pytest backend/tests/test_auth.py -k refresh_token_cannot_call_me_endpoint -q
pytest backend/tests/test_auth_hardening.py -k change_password_revokes_existing_refresh_tokens -q
```

Expected: at least one test fails because request auth currently accepts refresh tokens and password change does not revoke all outstanding refresh tokens.

- [ ] **Step 4: Implement the minimal auth boundary changes**

```python
# backend/app/services/auth.py
def _require_access_token_type(payload: dict, credentials_exception: HTTPException) -> None:
    if payload.get("type") != "access":
        raise credentials_exception

# insert these two lines immediately after each jwt.decode call in both request-auth helpers
payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
_require_access_token_type(payload, credentials_exception)
```

```python
# backend/app/routers/auth.py
current_user.hashed_password = get_password_hash(password_data.new_password)
await revoke_all_user_tokens(current_user.id, db)
await create_audit_log(
    db=db,
    user=current_user,
    action=AuditAction.CHANGE_PASSWORD,
    resource_type=ResourceType.USER,
    description=f"用户 {current_user.username} 修改密码",
    ip_address=get_client_ip(request),
    user_agent=get_user_agent(request),
)
await db.commit()
return {"message": "密码修改成功"}
```

- [ ] **Step 5: Extend refresh-token tests to prove the contract**

```python
# backend/tests/test_refresh_token.py
@pytest.mark.asyncio
async def test_refresh_token_cannot_authenticate_business_routes(client: AsyncClient, test_user: User):
    login_response = await client.post(
        "/api/v1/auth/login/json",
        json={"username": "testuser", "password": "testpass123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )

    assert response.status_code == 401
```

- [ ] **Step 6: Run the auth test slice and verify it passes**

Run:

```bash
pytest backend/tests/test_auth.py backend/tests/test_auth_hardening.py backend/tests/test_refresh_token.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/auth.py backend/app/routers/auth.py backend/tests/test_auth.py backend/tests/test_auth_hardening.py backend/tests/test_refresh_token.py
git commit -m "fix: enforce access token boundaries"
```

### Task 2: Remove Public Upload Exposure and Enforce File Object Authorization

**Files:**
- Modify: `backend/app/routers/common.py`
- Add: `backend/app/services/file_authorization.py`
- Modify: `nginx/nginx.conf`
- Modify: `docker-compose.production.yml`
- Modify: `backend/tests/test_file_compatibility.py`
- Add: `backend/tests/test_file_authorization.py`

- [ ] **Step 1: Add a failing file authorization regression test**

```python
@pytest.mark.asyncio
async def test_file_endpoint_rejects_authenticated_user_without_resource_access(
    monkeypatch,
):
    async def fake_get_user_from_token(token, db):
        return SimpleNamespace(id=2002, username="outsider", is_active=True)

    async def fake_resolve_file_access(path, db, current_user):
        return False

    monkeypatch.setattr(common, "get_user_from_token", fake_get_user_from_token)
    monkeypatch.setattr(common, "user_can_access_file_path", fake_resolve_file_access)

    with pytest.raises(common.HTTPException) as exc:
        await common.get_file(
            path="contracts/2026/04/demo.pdf",
            request=_build_request({"authorization": "Bearer header-token"}),
            db=object(),
        )

    assert exc.value.status_code == 403
```

- [ ] **Step 2: Add a failing release-configuration test for public uploads**

```python
def test_production_compose_does_not_mount_uploads_into_frontend_static_root():
    content = Path("docker-compose.production.yml").read_text(encoding="utf-8")
    assert "/usr/share/nginx/html/uploads" not in content


def test_nginx_config_does_not_expose_public_uploads_alias():
    content = Path("nginx/nginx.conf").read_text(encoding="utf-8")
    assert "location /uploads/" not in content
```

- [ ] **Step 3: Run the focused tests to verify failure**

Run:

```bash
pytest backend/tests/test_file_compatibility.py -k "public_uploads or file_endpoint_rejects_authenticated_user_without_resource_access" -q
```

Expected: FAIL because public uploads are still mounted and the file endpoint still allows any authenticated user with a path.

- [ ] **Step 4: Implement minimal server-side authorization**

```python
# backend/app/services/file_authorization.py
FILE_RULES = (
    (ContractUpstream, "contract_file_key", Permission.VIEW_UPSTREAM_BASIC_INFO),
    (ContractUpstream, "approval_pdf_key", Permission.VIEW_UPSTREAM_BASIC_INFO),
    (ContractDownstream, "contract_file_key", Permission.VIEW_DOWNSTREAM_BASIC_INFO),
    (ContractDownstream, "approval_pdf_key", Permission.VIEW_DOWNSTREAM_BASIC_INFO),
    (ContractManagement, "contract_file_key", Permission.VIEW_MANAGEMENT_BASIC_INFO),
    (ContractManagement, "approval_pdf_key", Permission.VIEW_MANAGEMENT_BASIC_INFO),
    (ExpenseNonContract, "file_key", Permission.VIEW_EXPENSES),
    (ExpenseNonContract, "approval_pdf_key", Permission.VIEW_EXPENSES),
    (ZeroHourLabor, "dispatch_file_key", Permission.VIEW_EXPENSES),
    (ZeroHourLabor, "approval_pdf_key", Permission.VIEW_EXPENSES),
)


async def user_can_access_file_path(path: str, db: AsyncSession, current_user: User) -> bool:
    if current_user.is_superuser:
        return True

    for model, field_name, permission in FILE_RULES:
        stmt = select(model).where(getattr(model, field_name) == path)
        row = (await db.execute(stmt)).scalar_one_or_none()
        if row is None:
            continue
        if not has_permission(current_user, permission):
            return False
        owner_id = getattr(row, "created_by", None)
        return owner_id in (None, current_user.id)

    return False
```

```python
# backend/app/routers/common.py
from app.services.file_authorization import user_can_access_file_path

if not await user_can_access_file_path(safe_path, db, current_user):
    raise HTTPException(status_code=403, detail="无权访问该文件")
```

- [ ] **Step 5: Remove static upload exposure from production config**

```yaml
# docker-compose.production.yml
frontend:
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./nginx/ssl:/etc/nginx/ssl:ro
```

```nginx
# nginx/nginx.conf
# Delete the public /uploads/ alias block entirely.
```

- [ ] **Step 6: Add positive and negative authorization tests**

```python
@pytest.mark.asyncio
async def test_file_endpoint_allows_owner_access(monkeypatch):
    async def fake_get_user_from_token(token, db):
        return SimpleNamespace(id=1001, username="owner", is_active=True, is_superuser=False)

    async def fake_resolve_file_access(path, db, current_user):
        return current_user.id == 1001

    monkeypatch.setattr(common, "get_user_from_token", fake_get_user_from_token)
    monkeypatch.setattr(common, "user_can_access_file_path", fake_resolve_file_access)

    class MissingMinioClient:
        def stat_object(self, bucket, path):
            raise RuntimeError("not found")

    monkeypatch.setattr(common, "get_minio_client", lambda: MissingMinioClient())

    with pytest.raises(common.ValidationError):
        await common.get_file(
            path="contracts/2026/04/demo.pdf",
            request=_build_request({"authorization": "Bearer header-token"}),
            db=object(),
        )


@pytest.mark.asyncio
async def test_file_endpoint_rejects_non_owner_access(monkeypatch):
    async def fake_get_user_from_token(token, db):
        return SimpleNamespace(id=2002, username="outsider", is_active=True, is_superuser=False)

    async def fake_resolve_file_access(path, db, current_user):
        return False

    monkeypatch.setattr(common, "get_user_from_token", fake_get_user_from_token)
    monkeypatch.setattr(common, "user_can_access_file_path", fake_resolve_file_access)

    with pytest.raises(common.HTTPException) as exc:
        await common.get_file(
            path="contracts/2026/04/demo.pdf",
            request=_build_request({"authorization": "Bearer header-token"}),
            db=object(),
        )

    assert exc.value.status_code == 403
```

- [ ] **Step 7: Run the file-access test slice**

Run:

```bash
pytest backend/tests/test_file_compatibility.py backend/tests/test_file_authorization.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/app/routers/common.py nginx/nginx.conf docker-compose.production.yml backend/tests/test_file_compatibility.py backend/tests/test_file_authorization.py
git commit -m "fix: enforce file authorization in production"
```

### Task 3: Verify Feishu Callbacks and Align Permission Gates

**Files:**
- Modify: `backend/app/routers/feishu.py`
- Modify: `backend/app/routers/contracts_upstream.py`
- Modify: `backend/app/routers/dashboard.py`
- Add: `backend/tests/test_feishu_webhook_security.py`
- Add: `backend/tests/test_permission_hardening.py`

- [ ] **Step 1: Add a failing webhook forgery regression test**

```python
@pytest.mark.asyncio
async def test_feishu_webhook_rejects_unsigned_event_callback(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.routers.feishu.FEISHU_WEBHOOK_VERIFICATION_TOKEN", "expected-token")

    response = await client.post(
        "/api/feishu/webhook",
        json={
            "header": {"event_type": "approval.instance.status_changed"},
            "event": {"instance_code": "fake", "status": "APPROVED"},
        },
    )

    assert response.status_code == 403
```

- [ ] **Step 2: Add failing permission-parity tests**

```python
@pytest.mark.asyncio
async def test_upstream_import_requires_same_permission_as_manual_create(client: AsyncClient, user_token: str):
    response = await client.post(
        "/api/v1/contracts/upstream/import/excel",
        headers={"Authorization": f"Bearer {user_token}"},
        files={"file": ("demo.xlsx", b"fake", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_dashboard_period_trend_requires_view_dashboard(client: AsyncClient, user_token: str):
    response = await client.get(
        "/api/v1/dashboard/stats/trend/period",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 403
```

- [ ] **Step 3: Run the focused tests to verify failure**

Run:

```bash
pytest backend/tests/test_feishu_webhook_security.py backend/tests/test_permission_hardening.py -q
```

Expected: FAIL because event callbacks are currently accepted without full verification and the permission gates are weaker than their sibling routes.

- [ ] **Step 4: Implement callback verification and permission parity**

```python
# backend/app/routers/feishu.py
def _verify_feishu_event(body: dict, request: Request) -> None:
    token = body.get("token")
    if not FEISHU_WEBHOOK_VERIFICATION_TOKEN or token != FEISHU_WEBHOOK_VERIFICATION_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid webhook signature")


@router.post("/webhook")
async def feishu_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    if body.get("type") == "url_verification":
        challenge = body.get("challenge")
        if not challenge:
            raise HTTPException(status_code=400, detail="Missing challenge")
        _verify_feishu_event(body, request)
        return {"challenge": challenge}
    _verify_feishu_event(body, request)
    header = body.get("header", {})
    event_type = header.get("event_type", "")
```

```python
# backend/app/routers/contracts_upstream.py
@router.post("/import/excel")
async def import_contracts_from_excel(
    file: UploadFile,
    current_user: User = Depends(require_permission(Permission.CREATE_UPSTREAM_CONTRACTS)),
    service: ContractUpstreamService = Depends(get_contract_service),
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise ValidationError(message="文件格式错误", field_errors={"file": "只支持 Excel 文件格式 (.xlsx, .xls)"})
```

```python
# backend/app/routers/dashboard.py
@router.get("/stats/trend/period")
async def get_period_trend(
    period: str = "monthly",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VIEW_DASHBOARD)),
):
    return {"period": period}
```

- [ ] **Step 5: Run the permission and webhook slice**

Run:

```bash
pytest backend/tests/test_feishu_webhook_security.py backend/tests/test_permission_hardening.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/feishu.py backend/app/routers/contracts_upstream.py backend/app/routers/dashboard.py backend/tests/test_feishu_webhook_security.py backend/tests/test_permission_hardening.py
git commit -m "fix: harden webhook and permission gates"
```

### Task 4: Make Production Startup and Release Checks Predictable

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/database.py`
- Modify: `backend/app/core/db_check.py`
- Add: `backend/tests/test_release_contract.py`
- Modify: `docs/release/deployment-checklist-hardening.md`
- Modify: `docs/release/upgrade-runbook-v1.6-hardening.md`

- [ ] **Step 1: Add a failing release-contract regression test**

```python
def test_main_mounts_detailed_health_route():
    routes = {route.path for route in app.routes}
    assert "/health/detailed" in routes


def test_main_does_not_run_schema_mutation_as_part_of_normal_boot_contract():
    content = Path("backend/app/main.py").read_text(encoding="utf-8")
    assert "run_startup_check" not in content
```

- [ ] **Step 2: Add a failing release-doc consistency test**

```python
def test_deployment_checklist_references_existing_compose_services():
    content = Path("docs/release/deployment-checklist-hardening.md").read_text(encoding="utf-8")
    assert "frontend nginx" not in content
```

- [ ] **Step 3: Run the focused tests to verify failure**

Run:

```bash
pytest backend/tests/test_release_contract.py -q
```

Expected: FAIL because `/health/detailed` is defined but not mounted, startup still performs schema mutation, and the checklist still names a nonexistent `nginx` service.

- [ ] **Step 4: Implement the release contract**

```python
# backend/app/main.py
from app.routers import health

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"[START] Starting {settings.APP_NAME}")
    await init_db()
    await init_data()
    yield


app.include_router(health.router)
```

```python
# backend/app/database.py
async def init_db():
    # Verify connectivity only; explicit migrations own schema changes.
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
```

```python
# backend/app/core/db_check.py
async def auto_fix_schema(conn: AsyncConnection) -> dict:
    return {
        "fixed_count": 0,
        "skipped_count": 0,
        "failed_count": 0,
        "details": {"mode": "disabled_in_app_startup"},
    }
```

- [ ] **Step 5: Align the release documents with actual services and routes**

```md
# docs/release/deployment-checklist-hardening.md
- Replace `up -d frontend nginx` with `up -d frontend`
- Replace `/health` 与 `/health/detailed` 返回正常 with explicit `curl -fsS http://localhost/health` and `curl -fsS http://localhost/health/detailed`
- Make migration/backup gates mandatory before backend restart
```

```md
# docs/release/upgrade-runbook-v1.6-hardening.md
- State that schema changes are applied via explicit migration execution, not app startup
- Keep backup + verify_migration + post-upgrade checks as blocking gates
```

- [ ] **Step 6: Run the release-contract test slice**

Run:

```bash
pytest backend/tests/test_release_contract.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/main.py backend/app/database.py backend/app/core/db_check.py backend/tests/test_release_contract.py docs/release/deployment-checklist-hardening.md docs/release/upgrade-runbook-v1.6-hardening.md
git commit -m "fix: align production startup with release contract"
```

### Task 5: Remove High-Risk Frontend Session Persistence and Diagnostic Exposure

**Files:**
- Modify: `frontend/src/utils/authSession.js`
- Modify: `frontend/src/stores/user.js`
- Modify: `frontend/src/utils/request.js`
- Modify: `frontend/src/utils/request_optimized.js`
- Modify: `frontend/public/diagnose.html`
- Add: `frontend/src/utils/__tests__/authSession.spec.js`

- [ ] **Step 1: Add a failing frontend token-storage test**

```javascript
import { persistSession, clearSessionStorage } from "../authSession"

test("persistSession does not write refresh token to localStorage", () => {
  persistSession({
    accessToken: "access-token",
    refreshToken: "refresh-token",
    expiresIn: 7200,
    user: { id: 1, username: "alice", permissions: [] },
  })

  expect(localStorage.getItem("token")).toBe("access-token")
  expect(localStorage.getItem("refresh_token")).toBeNull()
})
```

- [ ] **Step 2: Add a failing regression test for diagnostic exposure**

```javascript
test("diagnose page does not read auth material from localStorage", () => {
  const html = fs.readFileSync("frontend/public/diagnose.html", "utf-8")
  expect(html.includes("localStorage.getItem('token')")).toBe(false)
  expect(html.includes("localStorage.getItem('user_info')")).toBe(false)
})
```

- [ ] **Step 3: Run the focused frontend tests to verify failure**

Run:

```bash
npm --prefix frontend test -- authSession
```

Expected: FAIL because refresh tokens are still persisted and the diagnostic page still introspects auth state from browser storage.

- [ ] **Step 4: Implement the minimal frontend storage contract**

```javascript
// frontend/src/utils/authSession.js
export function persistSession({ accessToken, expiresIn, user }) {
  localStorage.setItem("token", accessToken)
  localStorage.removeItem("refresh_token")
  if (typeof expiresIn === "number" && !Number.isNaN(expiresIn)) {
    localStorage.setItem("token_expires_at", String(Date.now() + (expiresIn * 1000)))
  } else {
    localStorage.removeItem("token_expires_at")
  }
  localStorage.setItem("user_info", JSON.stringify(user || {}))
  localStorage.setItem("user_permissions", JSON.stringify((user && user.permissions) || []))
}

export function clearSessionStorage() {
  localStorage.removeItem("token")
  localStorage.removeItem("refresh_token")
  localStorage.removeItem("token_expires_at")
  localStorage.removeItem("user_info")
  localStorage.removeItem("user_permissions")
}
```

```javascript
// frontend/src/utils/request.js
const refreshToken = localStorage.getItem("refresh_token")
if (!refreshToken) {
  localStorage.clear()
  window.location.href = "/login"
  return Promise.reject(new Error("No refresh token available"))
}
```

```html
<!-- frontend/public/diagnose.html -->
<script>
  document.getElementById("results").innerHTML =
    '<div class="info">生产环境不显示本地认证材料。</div>'
</script>
```

- [ ] **Step 5: Run the frontend verification slice**

Run:

```bash
npm --prefix frontend test -- authSession
npm --prefix frontend run build
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/utils/authSession.js frontend/src/stores/user.js frontend/src/utils/request.js frontend/src/utils/request_optimized.js frontend/public/diagnose.html frontend/src/utils/__tests__/authSession.spec.js
git commit -m "fix: reduce frontend session exposure"
```

### Task 6: Final Verification and Release Readiness Evidence

**Files:**
- Modify: `docs/reports/2026-04-11-security-audit-report.md`
- Add: `docs/reports/2026-04-11-v1-6-2-remediation-verification.md`

- [ ] **Step 1: Record the exact verification matrix before rerunning tests**

```md
# docs/reports/2026-04-11-v1-6-2-remediation-verification.md
- Auth boundary tests
- File authorization tests
- Webhook and permission tests
- Release-contract tests
- Frontend build and authSession tests
- Manual smoke checks for /health, /health/detailed, /api/v1/auth/me, protected file download
```

- [ ] **Step 2: Run the backend verification suite**

Run:

```bash
pytest backend/tests/test_auth.py \
  backend/tests/test_auth_hardening.py \
  backend/tests/test_refresh_token.py \
  backend/tests/test_file_compatibility.py \
  backend/tests/test_file_authorization.py \
  backend/tests/test_feishu_webhook_security.py \
  backend/tests/test_permission_hardening.py \
  backend/tests/test_release_contract.py -q
```

Expected: PASS.

- [ ] **Step 3: Run frontend verification**

Run:

```bash
npm --prefix frontend test -- authSession
npm --prefix frontend run build
```

Expected: PASS.

- [ ] **Step 4: Run release workflow checks**

Run:

```bash
python3 scripts/verify_migration.py --safety-only
docker compose -f docker-compose.production.yml config --services
```

Expected:
- `verify_migration.py --safety-only` exits `0`
- compose services list contains only real services used by docs

- [ ] **Step 5: Update the security audit status**

```md
# docs/reports/2026-04-11-security-audit-report.md
- Mark each fixed item with remediation commit hash and verification evidence
- Leave any deferred item explicitly marked as not production-ready
```

- [ ] **Step 6: Commit**

```bash
git add docs/reports/2026-04-11-security-audit-report.md docs/reports/2026-04-11-v1-6-2-remediation-verification.md
git commit -m "docs: record v1.6.2 remediation verification"
```

## Self-Review

### Spec Coverage

- Refresh token misuse: covered by Task 1.
- Password-change token revocation gap: covered by Task 1.
- File object authorization and public upload exposure: covered by Task 2.
- Feishu webhook verification gap: covered by Task 3.
- Upstream import permission bypass: covered by Task 3.
- Dashboard trend permission bypass: covered by Task 3.
- Startup schema mutation and release unpredictability: covered by Task 4.
- Broken release docs and nonexistent compose service references: covered by Task 4.
- Frontend `localStorage` session exposure and diagnostic page: covered by Task 5.
- Final evidence and release sign-off: covered by Task 6.

### Placeholder Scan

- No `TODO`, `TBD`, or “similar to previous task” placeholders remain.
- Each task lists exact files, at least one concrete code/test snippet, and concrete verification commands.
- File ownership resolution is constrained to the exact allowlist helper in `backend/app/services/file_authorization.py`.

### Type and Contract Consistency

- Request-auth contract is consistent across `get_current_user()` and `get_user_from_token()`.
- Release contract assumes `/health` and `/health/detailed` are both real mounted routes after Task 4.
- Frontend contract assumes refresh tokens are no longer persisted in `localStorage`; request helpers and user store must be updated in the same task to stay consistent.

Plan complete and saved to `docs/superpowers/plans/2026-04-11-v1-6-2-production-remediation-plan.md`.

Two execution options after approval:

**1. Subagent-Driven (recommended)** - dispatch a fresh worker per task, review between tasks, faster isolation of security changes

**2. Inline Execution** - execute tasks in this session in order, with checkpoints after each release-blocking task
