# TwisterLab Architecture Documentation Draft (Evidence-Based)

**Project Location:** `C:\Users\Administrator\Documents\twisterlab`
**Scope of Analysis:** Limited to patterns and structures found in `src/twisterlab/*`, key API routes, the Redis service layer, and Alembic.
**Revision Status:** Preliminary Draft — **NOT** ready for final documentation.

---

## 🔍 Observed Facts (Fait Observé)

This section documents concrete structures confirmed by reading files or observing file paths.

### A. Core Components & Responsibilities

1.  **API Layer ($\mathbf{Public\;Contract}$):**
    *   The entry point for external communication is defined by FastAPI routes found in `src/twisterlab/api/routes/*`.
    *   `system.py`: Confirms high-level system operations, including `/health`, `/metrics`, and the critical `/domain/sync` endpoint which delegates to a dedicated agent call (`await sync_agent.execute(...)`).
    *   **External Integration:** The pattern for integrating external services is observed in `src/twisterlab/api/routes/system.py` (N8N example), which uses `httpx` with environment variables (`os.getenv`) to make requests to third-party URLs.

2.  **State Management Dependency ($\mathbf{Redis}$):**
    *   The dependency is concrete and highly utilized: `src/twisterlab/services/redis_client.py`. This class handles connection pooling, asynchronous operations (`aioredis`), and methods for caching/stats tracking (e.g., `get_stats()`).

3.  **Data Persistence:**
    *   The presence of the entire `alembic` directory confirms an **SQLAlchemy-backed migration system**. Schema changes *must* follow this lifecycle.

### B. Observed Communication Patterns ($\mathbf{Hypothèse\;Inférée}$)

1.  **Service Abstraction Layer:** The usage pattern seen in calling agents (`sync_agent = registry.get_agent("sync")`) strongly implies a **Service Registry Pattern**. Services do not communicate directly; they ask the central registry for an initialized, configured service object/agent instance.
2.  **Execution Flow Chain:** `API Route` $\rightarrow$ `Service Call (e.g., calling RedisClient)` $\rightarrow$ `Agent Execution`. This confirms a strict orchestration layer between API and Agents.

## 📐 Hypothetical Architecture Diagram Concept (Conceptualization)

*(Note: The actual diagram cannot be drawn, but the flow is documented here)*
`External Client/API Gateway` $\xrightarrow{\text{HTTP Request}}$ `[FastAPI Router]` $\xrightarrow{\text{Calls Service Layer}}$ `[Service Module / RedisClient]` $\rightarrow$ `[Agent Registry] \rightarrow Agent Execution`

**Dependencies:**
*   **Foundation:** FastAPI, SQLAlchemy (via Alembic).
*   **Runtime State:** Redis.
*   **External Communication:** HTTPX for external APIs; specialized SDKs for internal services.

## ✍️ Conventions Inferred from Code (`src/twisterlab/api/routes/system.py` & `redis_client.py`)

1.  **Error Handling (Convention):** All public endpoints must implement comprehensive error handling using standard HTTP status codes and `HTTPException`.
2.  **Security:** Sensitive config (API keys) must be masked when exposed, and configuration loading should reference a specific `.env` file or secure service (`src/twisterlab/api/routes/system.py:159-213`).

---
**Conclusion for Draft Review:** The code is structured around distinct, decoupled layers (API $\rightarrow$ Service $\rightarrow$ Agent). State is managed primarily through Redis and persistent data through Alembic. This draft focuses only on evidence found in the most critical file sets read.