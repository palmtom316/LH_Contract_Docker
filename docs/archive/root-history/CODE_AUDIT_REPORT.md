# System Code Audit Report & Optimization Plan

**Date:** 2025-12-21
**Project:** Lanhai Contract Management System v2 (Beta)

## 1. Overview
This report provides a comprehensive audit of the current codebase, including Backend (FastAPI), Frontend (Vue 3), and Database (PostgreSQL). The system has reached a stable beta functional state, with core contract management, finance tracking, and system administration features implemented.

## 2. Codebase Analysis

### 2.1 Backend (FastAPI + SQLAlchemy Async)
*   **Structure:** Well-organized following modern FastAPI patterns (`routers`, `models`, `schemas`, `services`).
*   **Database Access:** Uses `SQLAlchemy` with `AsyncSession` and `AsyncAdaptedQueuePool` for connection pooling. This is performant for I/O bound operations.
*   **Validation:** Uses `Pydantic` schemas for rigorous request/response validation.
*   **Authentication:** JWT-based authentication with `OAuth2PasswordBearer` and `passlib` for hashing. Role-based access control (`is_superuser`, `is_active`) is present.
*   **File Handling:** Standard static file mounting and local storage. Basic but effective for this scale.
*   **Reset Logic:** Recently optimized to use `TRUNCATE CASCADE` and explicit table checks, resolving previous transaction stability issues.

### 2.2 Frontend (Vue 3 + Vite + Element Plus)
*   **Component Architecture:** Uses explicit Views (`Upstream`, `Downstream`, `Management`) with shared custom components (`FormulaInput`, `SmartDateInput`, `DictSelect`).
*   **State Management:** Uses `Pinia` stores (`user`, `system`) for global state, which is the current best practice for Vue 3.
*   **Routing:** Standard `vue-router` with navigation guards for authentication titles.
*   **API Interaction:** Centralized `axios` instance with interceptors for token injection and standardized error handling.
*   **Responsiveness:** Contains logic (`checkIsMobile`) for adapting layouts, though some complex tables fallback to card views on mobile.

### 2.3 Database
*   **Schema:** Normalized relational design.
    *   Core Tables: `contracts_upstream`, `contracts_downstream`, `contracts_management`.
    *   Finance Tables: Separated tables for `receivables`, `payables`, `invoices`, `settlements` linked via Foreign Keys.
    *   System Tables: `users`, `sys_dictionary`, `sys_config`, `sys_audit_log`.
*   **Indexing:** Key columns (`contract_code`, `status`, `party_b_name`) are indexed (`index=True` in models), ensuring good query performance.
*   **Constraints:** Foreign keys with `CASCADE` (mostly) ensure data integrity upon deletion.

## 3. Findings & Recommendations

### 3.1 Backend Optimizations
*   **Recommendation 1: Dynamic Router Loading**
    *   *Current:* `main.py` manually imports and includes every router.
    *   *Improvement:* Can automate router discovery to avoid manual edits when adding modules.
*   **Recommendation 2: Standardized Logging**
    *   *Current:* Basic `print` or `logging` mixed.
    *   *Improvement:* Implement a unified structured logger (JSON format) for easier debugging and integration with monitoring tools (like ELK/Prometheus).
*   **Recommendation 3: Transaction Management Wrapper**
    *   *Current:* Manual try/except/rollback in some complex logic.
    *   *Improvement:* Create a generic decorator or context manager for atomic transactions to reduce boilerplate code and risk of unhandled rollbacks.

### 3.2 Frontend Optimizations
*   **Recommendation 1: Code Reusability - [x] **Refactor Contract Lists**: Extract shared logic (search, pagination, deletion) from `UpstreamList.vue`, `DownstreamList.vue`, and `ManagementList.vue` into a Composable (e.g., `useContractList`).
*   **Recommendation 2: Typescript Integration**
    *   *Observation:* Project set up for JS but has `checkJs` or VSCode warnings about Types.
    *   *Improvement:* Gradually migrate key utilities and complex components to TypeScript for better type safety and developer experience.
*   **Recommendation 3: Lazy Loading Components**
    *   *Improvement:* Ensure heavy components (like rich text editors or complex charts) are async lazy loaded to improve initial page load speed.

### 3.3 Database & Operations
*   **Recommendation 1: Data Archiving Strategy**
    *   *Observation:* `sys_audit_log` and finance tables will grow indefinitely.
    *   *Improvement:* Implement a scheduled job (e.g., using `APScheduler` in backend) to auto-archive or prune old audit logs (which is currently manual).
*   **Recommendation 2: Backup Reliability**
    *   *Observation:* Backup relies on `pg_dump` presence.
    *   *Improvement:* Containerize the database backup process or ensure `pg_dump` version matches the DB container to avoid version mismatch warnings.

## 4. Operation Plan (Next Steps)

1.  **Phase 1: Stabilization (Immediate)**
    *   Verify the system reset stability (Completed).
    *   [x] Fix any lingering lint warnings in Vue files (Global types error).
    *   [x] Conduct a full end-to-end test of the "Management Contract" flow (Finance addition -> Calculation -> Settlement).
        - Note: Flow is functional, but amount display issue observed (needs investigation in Phase 3).

2.  **Phase 2: Refactoring (This Week)**
    *   [x] **Refactor Frontend List Views:** Create `useContractList` composable.
    *   **Normalize Backend Error Handling:** Ensure all endpoints use the standardized `AppException`.
        - Note: Error handling framework exists (`errors.py`), but many routes still use raw `HTTPException`. Migration recommended.

3.  **Phase 3: Performance & Security (Next Week)**
    *   [x] Audit all API endpoints for permission scopes (ensure `user` role cannot access `admin` endpoints, beyond just UI hiding).
    *   Add comprehensive unit tests for the Calculation Logic (`FormulaInput` backend validation if needed).

4.  **Phase 4: Documentation**
    *   [x] Update `README.md` with new setup instructions (System Reset usage).
    *   [x] Generate API documentation (Export OpenAPI JSON and host it).

