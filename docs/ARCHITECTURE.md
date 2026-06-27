# TwisterLab Architecture Documentation
**Source:** Codebase Analysis (Verified against live code)
**Location:** `C:\Users\Administrator\Documents\twisterlab/docs/ARCHITECTURE.md`

---

## 🏗️ I. Core Architectural Pillars

The system's design is rigidly modular, structured around three core layers: **API Exposure**, **Service Abstraction**, and **State Persistence**. No component operates in isolation; communication must pass through the defined service contracts.

### A. API Layer (Public Contract)
*   **Mechanism:** All external access points are exposed via FastAPI routers (`src/twisterlab/api/routes/*`). The routing enforces authentication, role-based authorization, and request validation using Pydantic schemas.
*   **Observed Endpoints:**
    *   `/domain/sync` ($\text{POST}$) : Triggers agent workflows (e.g., `sync_agent.execute(...)`). (**Source:** `src/twisterlab/api/routes/system.py:13-30`)
    *   `/tools/{tool_name}` ($\text{POST}$): The core executor for all MCP tools, requiring both a tool name and arguments payload. (**Source:** `src/twisterlab/api/routes/tools.py:264-363`).
    *   `/mcp/execute` ($\text{POST}$): Handles the general JSON-RPC message execution (`{"method": "tools/call", ...}`). (**Source:** `src/twisterlab/api/routes/mcp.py:32-105`).

### B. Service Layer (Business Logic Abstraction)
*   **Role:** This layer mediates calls between the API and the actual execution engines. It enforces *how* the calling module interacts with resources.
*   **Core Contracts:** Defined by Abstract Base Classes (`ABC`) in `src/twisterlab/services/base.py`. These force implementations for:
    *   `LLMClient`: Mandatory abstract methods for `generate()`, `chat()`, and `stream()`. (**Source:** `src/twisterlab/services/base.py:106-131`).
    *   `CacheClient`: Abstract interface defining fundamental operations (`get`, `set`, `delete`). (**Source:** `redis_client.py`).

### C. State Persistence
**Observed Mechanisms:**
1.  **Redis Cache:** The service layer utilizes a dedicated, highly asynchronous client implementation (`src/twisterlab/services/redis_client.py`) for fast caching and transient messaging (PubSub). This confirms the system relies on Redis as its primary high-speed state store.
2.  **Database:** Persistence is managed by **Alembic**. The entire `alembic/` folder structure mandates that schema changes must follow explicit, versioned migration scripts (`0001_create_agents.py`).

## 🔄 Communication and Workflow Pattern (Proven)

The communication model is strictly layered:
$$\text{API Router} \xrightarrow{\text{Delegates}} \text{Service Layer Client} \xrightarrow{\text{Reads/Writes State Via}} \text{Redis/DB}$$

*   **Agent Communication:** Agents do not communicate peer-to-peer. The **`AgentRegistry`** pattern is mandatory: an agent instance must be requested from the central registry (`registry.get_agent("sync")`) before use. (**Source:** `src/twisterlab/api/routes/system.py`).
*   **Realtime Streaming (SSE):** For interactive features like browser control, a specific mechanism is used: A dedicated endpoint streams events using **Server-Sent Events (SSE)** (`src/twisterlab/api/routes/mcp_sse.py`), broadcasting results via Redis PubSub to keep multiple connected clients synchronized.

## 🛠️ Key Technical Dependencies & Protocols

| Dependency | Purpose | Module Evidence | Version Check |
| :--- | :--- | :--- | :--- |
| **FastAPI** | Defines API endpoints and request/response schemas. | `src/twisterlab/api/routes/*` | Structural (Framework). |
| **Redis (aioredis)** | Handles high-speed, non-persistent state. | `redis_client.py`, `mcp_sse.py`. | Confirmed async usage of Redis. |
| **SQLAlchemy / Alembic** | Ensures database schema integrity via migrations. | `alembic/` directory structure. | Process (Migration). |
| **Async/Await** | Mandated everywhere: API Routes, Service Clients, and State Access. | All files read contain multiple instances of `async`/`await`. | Convention enforced by language usage. |

## 🧱 ASCII Diagram of Proven Flow

```mermaid
graph TD
    A[External Client / HTTP Request] -->|API Call (POST/GET)| B(FastAPI Router);
    B --1. Check Auth & Rate Limit--> C{Auth/RBAC Layer};
    C --> D[Service Layer: Middleware];
    D --2. Access State/Data--> E[Redis Client <==> Redis Store];
    D --3. Read Config--> F[File System / Env Vars];
    D --> G(Agent Registry);
    G --4. Dispatch Task to--> H{Specialized Agent Instance};
    H -->|I/O Operations| I[External Tools: HTTPX, Browser Agent];

    subgraph "State Flow"
        E & F
    end
```

**Note:** This diagram is purely illustrative and mapped directly from the component interactions observed across the API routes and service client reads.

---
***End of Audited Architecture Document***