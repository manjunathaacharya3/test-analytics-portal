# TAPS Migration Plan: POC → Production

## Test Analytics & Predictive System — Comprehensive Migration Blueprint

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Analysis (POC)](#2-current-state-analysis-poc)
3. [Tech Stack Recommendation](#3-tech-stack-recommendation)
4. [Architecture Design](#4-architecture-design)
5. [Component Mapping (POC → Production)](#5-component-mapping-poc--production)
6. [Database Migration Strategy](#6-database-migration-strategy)
7. [Migration Phases](#7-migration-phases)
8. [Performance Optimizations](#8-performance-optimizations)
9. [Deployment Strategy](#9-deployment-strategy)
10. [Risk Assessment & Mitigation](#10-risk-assessment--mitigation)
11. [Testing Strategy](#11-testing-strategy)
12. [Appendix](#12-appendix)

---

## 1. Executive Summary

### 1.1 Purpose

This document outlines a comprehensive plan to migrate the **Test Analytics Portal (TAPS)** from its current Proof-of-Concept (POC) implementation to a **production-grade, high-performance application**. The migration prioritizes **performance**, **user experience**, **readability**, and **long-term maintainability**.

### 1.2 Current State (POC)

| Aspect | POC Implementation |
|--------|--------------------|
| **Backend** | Python FastAPI + SQLAlchemy (async) |
| **Frontend** | Python Dash + Plotly + Bootstrap (server-rendered) |
| **Database** | SQLite (fallback) / PostgreSQL |
| **Caching** | Custom `timed_cache` decorator (in-memory, per-process) |
| **Authentication** | None (CORS `allow_origins=["*"]`) |
| **Deployment** | Docker Compose (2 containers) |
| **Testing** | None |
| **Monitoring** | Basic `print()` statements |
| **State Management** | Dash `dcc.Store` (client-side) |
| **Data Fetching** | Synchronous `requests`/`httpx` from frontend to backend |

### 1.3 Target State (Production)

| Aspect | Production Implementation |
|--------|---------------------------|
| **Backend** | Python FastAPI (retained & hardened) + async SQLAlchemy |
| **Frontend** | React 18 + TypeScript + Next.js (App Router) |
| **Database** | PostgreSQL 16 (primary) + Redis 7 (cache/sessions) |
| **Caching** | Redis with multi-layer strategy (API, query, page) |
| **Authentication** | JWT + OAuth 2.0 with RBAC |
| **Deployment** | Kubernetes (Helm charts) + CI/CD |
| **Testing** | Jest + React Testing Library + Pytest + Playwright |
| **Monitoring** | OpenTelemetry + Prometheus + Grafana + Structured Logging |
| **State Management** | TanStack Query (server state) + Zustand (client state) |
| **Data Fetching** | REST API with SWR/React Query + WebSocket for real-time |

### 1.4 Why Migrate?

| POC Limitation | Production Impact |
|----------------|-------------------|
| Dash server-renders all UI (Python → HTML) | Every interaction round-trips to server; poor UX at scale |
| `timed_cache` is per-process, no invalidation | Stale data, memory leaks, no cache sharing across workers |
| No authentication or authorization | Security vulnerability; not deployable |
| Synchronous HTTP calls from Dash to FastAPI | Frontend blocks on every API call; poor perceived performance |
| No test coverage | Regressions undetectable; unsafe to refactor |
| Mock data for Defect Management | Feature incomplete; not functional |
| Single Dockerfile for both services | No independent scaling |
| No structured logging or monitoring | Blind to production issues |

---

## 2. Current State Analysis (POC)

### 2.1 Project Structure

```
test-analytics-portal/
├── database/
│   ├── base.py                    # SQLAlchemy declarative base
│   ├── database.py                # Engine init, session factory, fallback logic
│   └── tables/
│       ├── project.py             # Project model (id, name, description, owner, etc.)
│       ├── module.py              # Module model (belongs to Project)
│       ├── execution.py           # Execution model (belongs to Module)
│       └── scenario.py            # Scenario model (belongs to Execution)
├── service/
│   ├── main.py                    # FastAPI app, CORS, router registration
│   ├── cucumber_parser.py         # Cucumber JSON → structured data parser
│   ├── apis/
│   │   ├── projects.py            # CRUD for projects, module listing
│   │   ├── report.py              # Cucumber report upload & metric computation
│   │   └── execution.py           # Execution queries (by project, module, scenarios)
│   └── schema/
│       ├── project.py             # Pydantic: ProjectCreate, ProjectResponse
│       ├── report.py              # Pydantic: ReportResponse
│       ├── execution.py           # Pydantic: ExecutionResponse
│       └── ProjectOverviewResponse.py  # Enriched project overview schema
├── ui/
│   ├── dashboard.py               # Dash app init, sidebar, layout
│   ├── assets/                    # CSS files (sidebar, projects, execution, etc.)
│   └── pages/
│       ├── projects.py            # Projects dashboard page
│       ├── execution_summary.py   # Execution summary with filters & table
│       ├── trends.py              # Pass rate & duration trend charts
│       ├── module_details.py      # Module-level execution details & scenarios
│       ├── defect_management.py   # Defect tracking (MOCK DATA)
│       ├── ai_failure_analysis.py # AI-powered failure analysis (960 lines)
│       └── settings.py            # Project creation/edit form
├── docker-compose.yml             # 2-service compose (backend + dashboard)
├── Dockerfile                     # Single Python 3.11 image
├── requirements.txt               # 18 Python dependencies
└── test_portal.db                 # SQLite database file
```

### 2.2 API Endpoints Inventory

| Method | Endpoint | Source File | Description |
|--------|----------|-------------|-------------|
| `GET` | `/health` | `service/main.py` | Health check |
| `POST` | `/projects/create_project` | `service/apis/projects.py` | Create new project |
| `GET` | `/projects/all_projects` | `service/apis/projects.py` | List all projects with enriched metrics |
| `GET` | `/projects/{project_id}/modules` | `service/apis/projects.py` | List modules for a project |
| `POST` | `/api/reports/upload` | `service/apis/report.py` | Upload Cucumber JSON report |
| `GET` | `/api/executions/{project_id}/executions` | `service/apis/execution.py` | Get executions for a project |
| `GET` | `/api/executions/project/{project_id}` | `service/apis/execution.py` | Get all executions by project |
| `GET` | `/api/executions/module/{module_id}` | `service/apis/execution.py` | Get executions for a module |
| `GET` | `/api/executions/{execution_id}/scenarios` | `service/apis/execution.py` | Get scenarios for an execution |

### 2.3 Database Schema (4 Tables)

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  projects   │────▶│   modules   │────▶│  executions  │────▶│  scenarios  │
├─────────────┤     ├─────────────┤     ├──────────────┤     ├─────────────┤
│ id (PK)     │     │ id (PK)     │     │ id (PK)      │     │ id (PK)     │
│ name        │     │ name        │     │ module_id(FK)│     │ exec_id(FK) │
│ description │     │ description │     │ passed       │     │ scenario    │
│ repo_url    │     │ project_id  │     │ failed       │     │ status      │
│ owner       │     │   (FK)      │     │ total        │     │ tags (JSON) │
│ is_active   │     │ is_active   │     │ duration     │     │ duration    │
│ created_at  │     │ created_at  │     │ status       │     │ failed_step │
│ updated_at  │     │ updated_at  │     │ created_at   │     │ error       │
└─────────────┘     └─────────────┘     │ updated_at   │     │ attachments │
                                        └──────────────┘     │   (JSON)    │
                                                             │ created_at  │
                                                             │ updated_at  │
                                                             └─────────────┘
```

### 2.4 Frontend Pages Inventory

| Page | Route | Source File | Lines | Key Features |
|------|-------|-------------|-------|--------------|
| Projects Dashboard | `/projects` | `ui/pages/projects.py` | ~200 | Project cards, KPIs, status indicators |
| Execution Summary | `/execution-summary` | `ui/pages/execution_summary.py` | 422 | Filters, DataTable, summary cards |
| Trends | `/trends` | `ui/pages/trends.py` | 295 | Plotly line charts, project/module toggle |
| Module Details | `/module-details` | `ui/pages/module_details.py` | 530 | Execution runs, scenario drill-down, defect linking |
| Defect Management | `/defect-management` | `ui/pages/defect_management.py` | 303 | **Mock data only**, CRUD UI |
| AI Failure Analysis | `/ai-failure-analysis` | `ui/pages/ai_failure_analysis.py` | 960 | AI insights modal, failure patterns, generate fix |
| Settings | `/settings` | `ui/pages/settings.py` | 165 | Project create/edit form |

### 2.5 Key POC Issues Identified

1. **Performance Bottleneck**: Dash re-renders entire page server-side on every callback; each user interaction triggers a full round-trip
2. **Caching Anti-pattern**: `timed_cache` is a simple in-memory dict per process — no TTL eviction, no cross-worker sharing, no invalidation
3. **N+1 Query Problem**: `list_projects()` in `service/apis/projects.py` runs 3 separate queries per project in a loop
4. **Mixed HTTP Clients**: Frontend uses both `requests` (sync) and `httpx` (sync) — blocking the Dash event loop
5. **No Error Boundaries**: Frontend crashes propagate to entire page
6. **Hardcoded Mock Data**: Defect Management uses hardcoded dictionaries, not connected to database
7. **No Input Validation**: Settings page has minimal client-side validation
8. **Security**: CORS allows all origins, no auth, no rate limiting
9. **Monolithic CSS**: 7 separate CSS files with potential style conflicts
10. **No TypeScript/Type Safety**: Frontend has no type checking

---

## 3. Tech Stack Recommendation

### 3.1 Recommended Production Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRODUCTION STACK                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    FRONTEND LAYER                        │   │
│  │  Next.js 14 (App Router) + React 18 + TypeScript 5       │   │
│  │  TailwindCSS 3 + shadcn/ui + Recharts                    │   │
│  │  TanStack Query v5 + Zustand                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                         REST + WebSocket                        │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    BACKEND LAYER                         │   │
│  │  FastAPI 0.110+ (Python 3.12) — RETAINED & HARDENED      │   │
│  │  SQLAlchemy 2.0 (async) + Alembic                        │   │
│  │  Pydantic v2 + python-jose (JWT)                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     DATA LAYER                           │   │
│  │  PostgreSQL 16 (primary) + Redis 7 (cache/sessions)      │   │
│  │  Alembic (migrations) + pgBouncer (connection pooling)   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   INFRASTRUCTURE                         │   │
│  │  Docker + Kubernetes + Helm                               │   │
│  │  GitHub Actions CI/CD                                     │   │
│  │  OpenTelemetry + Prometheus + Grafana                     │   │
│  │  Nginx (reverse proxy + static assets)                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Technology Justification

#### Frontend: Next.js 14 + React 18 + TypeScript

| Criteria | Why Next.js + React |
|----------|--------------------|
| **Performance** | Client-side rendering eliminates server round-trips for UI updates. React's virtual DOM diffing is orders of magnitude faster than Dash's full-page re-render. Next.js adds SSR/SSG for initial load performance, automatic code splitting, and image optimization. |
| **User Experience** | Instant UI feedback, optimistic updates, smooth transitions, offline capability with service workers. |
| **Maintainability** | TypeScript provides compile-time type safety. Component-based architecture with clear separation. Massive ecosystem of battle-tested libraries. |
| **Readability** | JSX is more intuitive than Dash's `html.Div([html.H3(...)])` pattern. TypeScript interfaces document data shapes. |
| **Ecosystem** | 200K+ npm packages, shadcn/ui for accessible components, Recharts for charts (replacing Plotly). |

**Why NOT keep Dash?**
- Dash is designed for data science dashboards, not production web apps
- Every user interaction triggers a Python callback (server round-trip)
- No code splitting, no lazy loading, no SSR optimization
- Limited component ecosystem compared to React
- No TypeScript support
- Difficult to implement complex UX patterns (modals, drag-drop, real-time)

#### Backend: FastAPI (Retained & Hardened)

| Criteria | Why Keep FastAPI |
|----------|------------------|
| **Performance** | Already async-native; one of the fastest Python frameworks. Minimal migration effort. |
| **Existing Logic** | Cucumber parser, metric computation, and report upload logic are well-structured and can be retained. |
| **Type Safety** | Pydantic v2 provides runtime validation + OpenAPI schema generation. |
| **Ecosystem** | Excellent middleware support, dependency injection, background tasks. |

**Hardening Required:**
- Upgrade to Pydantic v2 model syntax
- Add proper authentication (JWT + OAuth 2.0)
- Implement RBAC (Role-Based Access Control)
- Add rate limiting and request validation
- Structured logging with correlation IDs
- API versioning (`/api/v1/...`)

#### UI Component Library: shadcn/ui + TailwindCSS

| Criteria | Why shadcn/ui |
|----------|---------------|
| **Performance** | Copy-paste components (no runtime library overhead). Tree-shakeable. |
| **Accessibility** | Built on Radix UI primitives — WCAG 2.1 AA compliant out of the box. |
| **Customization** | Full source code ownership; style with TailwindCSS utility classes. |
| **Maintainability** | No vendor lock-in; components live in your codebase. |

#### Charts: Recharts (replacing Plotly)

| Criteria | Why Recharts |
|----------|-------------|
| **Bundle Size** | ~45KB gzipped vs Plotly.js ~1MB+ gzipped |
| **React Integration** | Native React components with declarative API |
| **Performance** | SVG-based, lightweight, responsive by default |
| **Customization** | Composable components, easy theming |

#### State Management: TanStack Query + Zustand

| Concern | Solution |
|---------|----------|
| **Server State** (API data) | TanStack Query v5 — automatic caching, background refetching, stale-while-revalidate, pagination, infinite scroll |
| **Client State** (UI state) | Zustand — minimal boilerplate, TypeScript-first, no providers needed |

#### Caching: Redis 7

| POC Pattern | Production Pattern |
|-------------|--------------------|
| `timed_cache` decorator (in-memory dict) | Redis with TTL, cache invalidation, pub/sub for real-time |
| Per-process, no sharing | Shared across all backend workers |
| No eviction policy | LRU eviction with configurable max memory |
| No invalidation | Event-driven invalidation on data mutation |

---

## 4. Architecture Design

### 4.1 High-Level Architecture

```
                    ┌─────────────────────────┐
                    │      CDN / Nginx        │
                    │   (Static Assets +      │
                    │    Reverse Proxy)        │
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
              ┌─────▼─────┐           ┌───────▼───────┐
              │  Next.js   │           │   FastAPI     │
              │  Frontend  │◄─────────▶│   Backend     │
              │  (SSR/CSR) │  REST +   │   (API v1)    │
              │            │  WebSocket│               │
              └─────┬──────┘           └───────┬───────┘
                    │                          │
                    │                  ┌───────┴───────┐
                    │                  │               │
                    │           ┌──────▼──────┐ ┌──────▼──────┐
                    │           │ PostgreSQL  │ │   Redis     │
                    │           │   16        │ │   7         │
                    │           │ (Primary DB)│ │ (Cache +    │
                    │           │             │ │  Sessions)  │
                    │           └─────────────┘ └─────────────┘
                    │
              ┌─────▼──────────────────────────┐
              │       Monitoring Stack          │
              │  OpenTelemetry → Prometheus     │
              │  → Grafana + Loki (Logs)        │
              └────────────────────────────────┘
```

### 4.2 Backend Architecture (Modular Monolith)

**Decision: Modular Monolith** (not microservices)

**Rationale:** TAPS is a focused application with a single bounded context (test analytics). Microservices would add unnecessary operational complexity. A modular monolith provides clean separation while keeping deployment simple.

```
backend/
├── app/
│   ├── main.py                    # FastAPI app factory
│   ├── config.py                  # Settings via pydantic-settings
│   ├── dependencies.py            # Shared DI (db session, current_user, etc.)
│   │
│   ├── auth/                      # Authentication & Authorization module
│   │   ├── router.py              # Login, register, refresh token
│   │   ├── service.py             # JWT creation, verification
│   │   ├── models.py              # User, Role models
│   │   ├── schemas.py             # Auth request/response schemas
│   │   └── middleware.py          # Auth middleware
│   │
│   ├── projects/                  # Projects module
│   │   ├── router.py              # Project CRUD endpoints
│   │   ├── service.py             # Business logic
│   │   ├── models.py              # Project SQLAlchemy model
│   │   ├── schemas.py             # Pydantic schemas
│   │   └── repository.py          # Data access layer
│   │
│   ├── executions/                # Executions module
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── models.py              # Execution, Scenario models
│   │   ├── schemas.py
│   │   └── repository.py
│   │
│   ├── reports/                   # Report ingestion module
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── parsers/
│   │   │   ├── base.py            # Abstract parser interface
│   │   │   ├── cucumber.py        # Cucumber JSON parser (from POC)
│   │   │   └── junit.py           # Future: JUnit XML parser
│   │   └── schemas.py
│   │
│   ├── defects/                   # Defect Management module (NEW - replaces mock)
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── models.py              # Defect model (NEW table)
│   │   ├── schemas.py
│   │   └── repository.py
│   │
│   ├── analytics/                 # Analytics & AI module
│   │   ├── router.py
│   │   ├── service.py             # Trend computation, failure analysis
│   │   ├── ai_service.py          # AI/ML integration
│   │   └── schemas.py
│   │
│   ├── core/                      # Shared infrastructure
│   │   ├── database.py            # Engine, session, connection pooling
│   │   ├── cache.py               # Redis cache wrapper
│   │   ├── logging.py             # Structured logging setup
│   │   ├── middleware.py          # CORS, rate limiting, request ID
│   │   ├── exceptions.py          # Custom exception handlers
│   │   └── events.py              # Startup/shutdown events
│   │
│   └── migrations/                # Alembic migrations
│       ├── alembic.ini
│       ├── env.py
│       └── versions/
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── pyproject.toml                 # Poetry/pip dependencies
├── Dockerfile
└── docker-compose.yml
```

### 4.3 Frontend Architecture (Next.js App Router)

```
frontend/
├── src/
│   ├── app/                       # Next.js App Router
│   │   ├── layout.tsx             # Root layout (sidebar, providers)
│   │   ├── page.tsx               # Home → redirect to /projects
│   │   ├── projects/
│   │   │   ├── page.tsx           # Projects dashboard
│   │   │   └── [id]/
│   │   │       ├── page.tsx       # Project detail
│   │   │       ├── executions/
│   │   │       │   └── page.tsx   # Execution summary
│   │   │       ├── trends/
│   │   │       │   └── page.tsx   # Trends analysis
│   │   │       └── modules/
│   │   │           └── [moduleId]/
│   │   │               └── page.tsx  # Module details
│   │   ├── defects/
│   │   │   └── page.tsx           # Defect management
│   │   ├── ai-analysis/
│   │   │   └── page.tsx           # AI failure analysis
│   │   └── settings/
│   │       └── page.tsx           # Settings/project management
│   │
│   ├── components/                # Atomic Design structure
│   │   ├── atoms/                 # Basic elements
│   │   │   ├── Badge.tsx
│   │   │   ├── Button.tsx
│   │   │   ├── StatusIcon.tsx
│   │   │   └── KPICard.tsx
│   │   ├── molecules/             # Composed components
│   │   │   ├── FilterBar.tsx
│   │   │   ├── DataTable.tsx
│   │   │   ├── SummaryCards.tsx
│   │   │   └── ProjectCard.tsx
│   │   ├── organisms/             # Complex sections
│   │   │   ├── Sidebar.tsx
│   │   │   ├── ExecutionTable.tsx
│   │   │   ├── TrendCharts.tsx
│   │   │   ├── ScenarioList.tsx
│   │   │   └── AIInsightModal.tsx
│   │   └── templates/             # Page layouts
│   │       ├── DashboardLayout.tsx
│   │       └── DetailLayout.tsx
│   │
│   ├── hooks/                     # Custom React hooks
│   │   ├── useProjects.ts         # TanStack Query: projects
│   │   ├── useExecutions.ts       # TanStack Query: executions
│   │   ├── useModules.ts          # TanStack Query: modules
│   │   ├── useTrends.ts           # TanStack Query: trend data
│   │   └── useDebounce.ts         # Utility hook
│   │
│   ├── lib/                       # Utilities
│   │   ├── api.ts                 # Axios/fetch wrapper with interceptors
│   │   ├── constants.ts           # App constants
│   │   ├── utils.ts               # Helper functions
│   │   └── types.ts               # Shared TypeScript types
│   │
│   ├── store/                     # Zustand stores
│   │   ├── useFilterStore.ts      # Filter state (project, module, date)
│   │   └── useUIStore.ts          # UI state (sidebar, modals)
│   │
│   └── styles/                    # Global styles
│       └── globals.css            # TailwindCSS + custom tokens
│
├── public/                        # Static assets
│   └── logo.svg
│
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
├── package.json
├── Dockerfile
└── .env.local
```

### 4.4 API Design (RESTful v1)

All endpoints move under `/api/v1/` with consistent naming:

| POC Endpoint | Production Endpoint | Changes |
|-------------|---------------------|----------|
| `GET /health` | `GET /api/v1/health` | Add detailed health (DB, Redis, uptime) |
| `POST /projects/create_project` | `POST /api/v1/projects` | RESTful naming |
| `GET /projects/all_projects` | `GET /api/v1/projects` | Add pagination, sorting, filtering |
| `GET /projects/{id}/modules` | `GET /api/v1/projects/{id}/modules` | Add pagination |
| `POST /api/reports/upload` | `POST /api/v1/reports` | Add async processing, progress tracking |
| `GET /api/executions/{pid}/executions` | `GET /api/v1/projects/{id}/executions` | Nested resource pattern |
| `GET /api/executions/project/{pid}` | `GET /api/v1/projects/{id}/executions` | Consolidated |
| `GET /api/executions/module/{mid}` | `GET /api/v1/modules/{id}/executions` | Consistent nesting |
| `GET /api/executions/{eid}/scenarios` | `GET /api/v1/executions/{id}/scenarios` | Consistent nesting |
| *(none)* | `POST /api/v1/auth/login` | **NEW**: JWT authentication |
| *(none)* | `POST /api/v1/auth/register` | **NEW**: User registration |
| *(none)* | `GET /api/v1/defects` | **NEW**: Real defect CRUD |
| *(none)* | `POST /api/v1/analytics/ai-analysis` | **NEW**: AI analysis endpoint |
| *(none)* | `WS /api/v1/ws/executions` | **NEW**: WebSocket for real-time |

---

## 5. Component Mapping (POC → Production)

### 5.1 Frontend Page Migration Map

| POC Page | POC File | Production Component | Key Changes |
|----------|----------|---------------------|-------------|
| **Projects Dashboard** | `ui/pages/projects.py` (Dash) | `app/projects/page.tsx` (React) | Server component for initial load; client-side filtering; `useProjects()` hook with TanStack Query; shadcn/ui Card components; skeleton loading states |
| **Execution Summary** | `ui/pages/execution_summary.py` (422 lines) | `app/projects/[id]/executions/page.tsx` | TanStack Table with virtual scrolling; URL-based filter state; server-side pagination; `useExecutions()` hook |
| **Trends** | `ui/pages/trends.py` (295 lines) | `app/projects/[id]/trends/page.tsx` | Recharts `<LineChart>` replacing Plotly; date range picker; responsive charts; memoized computations |
| **Module Details** | `ui/pages/module_details.py` (530 lines) | `app/projects/[id]/modules/[moduleId]/page.tsx` | Collapsible scenario accordion; inline defect linking; `useModuleExecutions()` hook |
| **Defect Management** | `ui/pages/defect_management.py` (303 lines, MOCK) | `app/defects/page.tsx` | **Full rewrite**: Real CRUD backed by new Defect table; filterable DataTable; status workflow |
| **AI Failure Analysis** | `ui/pages/ai_failure_analysis.py` (960 lines) | `app/ai-analysis/page.tsx` | Streaming AI responses; React Suspense for loading; modal with tabs; WebSocket for real-time |
| **Settings** | `ui/pages/settings.py` (165 lines) | `app/settings/page.tsx` | React Hook Form with Zod validation; toast notifications; optimistic updates |
| **Sidebar** | `ui/dashboard.py` (sidebar section) | `components/organisms/Sidebar.tsx` | Collapsible sidebar; active route highlighting; responsive mobile drawer |

### 5.2 Backend Service Migration Map

| POC Component | POC File | Production Component | Key Changes |
|--------------|----------|---------------------|-------------|
| **App Init** | `service/main.py` | `app/main.py` | App factory pattern; lifespan events; middleware stack |
| **Projects API** | `service/apis/projects.py` | `app/projects/router.py` + `service.py` + `repository.py` | Repository pattern; N+1 query fix; pagination |
| **Report Upload** | `service/apis/report.py` | `app/reports/router.py` + `service.py` | Background task processing; progress tracking |
| **Execution API** | `service/apis/execution.py` | `app/executions/router.py` + `service.py` | Consolidated endpoints; caching with Redis |
| **Cucumber Parser** | `service/cucumber_parser.py` | `app/reports/parsers/cucumber.py` | Abstract parser interface; extensible for JUnit/TestNG |
| **DB Engine** | `database/database.py` | `app/core/database.py` | Remove SQLite fallback; pgBouncer pooling; health checks |
| **Schemas** | `service/schema/*.py` | `app/{module}/schemas.py` | Pydantic v2 syntax; shared base schemas |

### 5.3 Database Model Migration Map

| POC Model | POC File | Production Model | Changes |
|-----------|----------|-------------------|----------|
| `Project` | `database/tables/project.py` | `app/projects/models.py` | Add indexes on `name`, `owner`; UUID type column |
| `Module` | `database/tables/module.py` | `app/projects/models.py` | Add composite index on `(project_id, name)` |
| `Execution` | `database/tables/execution.py` | `app/executions/models.py` | Add indexes on `module_id`, `created_at`; add `start_time`, `end_time` |
| `Scenario` | `database/tables/scenario.py` | `app/executions/models.py` | Add index on `execution_id`; full-text search on `error` |
| *(none)* | *(none)* | `app/defects/models.py` | **NEW**: Defect table (id, title, severity, priority, status, assigned_to, module_id, scenario_id, etc.) |
| *(none)* | *(none)* | `app/auth/models.py` | **NEW**: User table (id, email, hashed_password, role, etc.) |

### 5.4 Utility & Pattern Migration Map

| POC Pattern | POC Location | Production Pattern | Implementation |
|-------------|-------------|-------------------|----------------|
| `timed_cache()` decorator | All `ui/pages/*.py` | Redis cache with `@cache()` decorator | `app/core/cache.py` with Redis backend, TTL, invalidation |
| `requests.get()` (sync HTTP) | `ui/pages/execution_summary.py` | TanStack Query `useQuery()` | Client-side data fetching with caching |
| `httpx.get()` (sync HTTP) | `ui/pages/trends.py`, `module_details.py` | TanStack Query `useQuery()` | Automatic refetching, stale-while-revalidate |
| `dcc.Store` (client state) | All Dash pages | Zustand store + URL state | Persistent, shareable state |
| `dash.callback` | All Dash pages | React `useEffect` + event handlers | No server round-trip for UI updates |
| `dash_table.DataTable` | Execution summary, module details | TanStack Table + shadcn/ui | Virtual scrolling, column resizing, export |
| `plotly.express` charts | `ui/pages/trends.py` | Recharts `<LineChart>`, `<BarChart>` | 20x smaller bundle, native React |
| `dbc.Modal` | AI analysis, module details | shadcn/ui `<Dialog>` | Accessible, animated, composable |
| `dbc.Card` | All pages | shadcn/ui `<Card>` | Consistent design tokens |
| CSS files (7 separate) | `ui/assets/*.css` | TailwindCSS utility classes | No CSS conflicts, design system tokens |

---

## 6. Database Migration Strategy

### 6.1 Migration Approach

```
Phase 1: Schema Migration (Alembic)
├── Generate initial migration from existing models
├── Add new tables (User, Defect)
├── Add indexes and constraints
├── Add UUID primary key type (PostgreSQL native)
└── Add full-text search indexes

Phase 2: Data Migration
├── Export SQLite data → CSV/JSON
├── Transform data (UUID format, timestamps)
├── Import into PostgreSQL
├── Validate data integrity
└── Run consistency checks

Phase 3: Connection Optimization
├── Configure pgBouncer connection pooling
├── Set up read replicas (if needed)
├── Configure async connection pool size
└── Add connection health checks
```

### 6.2 Schema Evolution

```sql
-- New indexes for performance
CREATE INDEX idx_projects_name ON projects(name);
CREATE INDEX idx_projects_owner ON projects(owner);
CREATE INDEX idx_modules_project_id ON modules(project_id);
CREATE UNIQUE INDEX idx_modules_project_name ON modules(project_id, name);
CREATE INDEX idx_executions_module_id ON executions(module_id);
CREATE INDEX idx_executions_created_at ON executions(created_at DESC);
CREATE INDEX idx_executions_module_created ON executions(module_id, created_at DESC);
CREATE INDEX idx_scenarios_execution_id ON scenarios(execution_id);
CREATE INDEX idx_scenarios_status ON scenarios(status);

-- New Defect table
CREATE TABLE defects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    severity VARCHAR(20) NOT NULL,        -- Critical, High, Medium, Low
    priority VARCHAR(10) NOT NULL,         -- P0, P1, P2, P3
    status VARCHAR(30) NOT NULL DEFAULT 'Open',  -- Open, In Progress, Fixed, Closed, Won't Fix
    assigned_to VARCHAR(255),
    reported_by VARCHAR(255) NOT NULL,
    project_id UUID REFERENCES projects(id),
    module_id UUID REFERENCES modules(id),
    scenario_id UUID REFERENCES scenarios(id),
    resolution TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ
);

CREATE INDEX idx_defects_project ON defects(project_id);
CREATE INDEX idx_defects_status ON defects(status);
CREATE INDEX idx_defects_severity ON defects(severity);

-- New User table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',  -- admin, manager, viewer
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);
```

### 6.3 Query Optimization — Fixing N+1 Problem

**POC Problem** (`service/apis/projects.py` → `list_projects()`):
```python
# POC: 3 queries PER project (N+1 anti-pattern)
for project in projects:  # N iterations
    result = await db.execute(select(func.count(Module.id))...)  # Query 1
    result = await db.execute(select(func.sum(...))...)           # Query 2
    result = await db.execute(select(Execution.status)...)        # Query 3
```

**Production Fix** (single optimized query):
```python
# Production: 1 query with JOINs and subqueries
stmt = (
    select(
        Project,
        func.count(distinct(Module.id)).label("modules_count"),
        func.sum(Execution.total).label("total_tests"),
        func.sum(Execution.passed).label("passed_tests"),
        func.max(Execution.created_at).label("last_run"),
    )
    .outerjoin(Module, Module.project_id == Project.id)
    .outerjoin(Execution, Execution.module_id == Module.id)
    .group_by(Project.id)
    .options(selectinload(Project.modules))
)
```

---

## 7. Migration Phases

### Phase 1: Foundation (Weeks 1-2)

**Objective:** Set up production project structure, CI/CD, and database.

| Task | Details | Deliverable |
|------|---------|-------------|
| 1.1 | Initialize Next.js 14 project with TypeScript, TailwindCSS, shadcn/ui | `frontend/` directory |
| 1.2 | Restructure FastAPI backend into modular monolith | `backend/app/` directory |
| 1.3 | Set up PostgreSQL 16 + Redis 7 via Docker Compose | `docker-compose.yml` |
| 1.4 | Configure Alembic migrations from existing models | Initial migration files |
| 1.5 | Set up GitHub Actions CI/CD pipeline | `.github/workflows/` |
| 1.6 | Configure ESLint, Prettier, Ruff (Python linter) | Config files |
| 1.7 | Set up environment management (.env files) | `.env.example` |
| 1.8 | Migrate SQLite data to PostgreSQL | Data migration script |

### Phase 2: Backend API Migration (Weeks 3-4)

**Objective:** Harden and optimize all backend APIs.

| Task | Details | Deliverable |
|------|---------|-------------|
| 2.1 | Implement JWT authentication + user management | `app/auth/` module |
| 2.2 | Migrate Projects API with repository pattern | `app/projects/` module |
| 2.3 | Migrate Report Upload with background processing | `app/reports/` module |
| 2.4 | Migrate Execution API with Redis caching | `app/executions/` module |
| 2.5 | Implement Defect Management API (replace mock data) | `app/defects/` module |
| 2.6 | Add API versioning (`/api/v1/`) | Router prefixes |
| 2.7 | Implement rate limiting and request validation | Middleware |
| 2.8 | Set up structured logging with correlation IDs | `app/core/logging.py` |
| 2.9 | Fix N+1 queries in projects listing | Optimized queries |
| 2.10 | Write Pytest unit + integration tests | `tests/` directory |

### Phase 3: Frontend Migration (Weeks 5-8)

**Objective:** Build React frontend replacing all Dash pages.

| Task | Details | Deliverable |
|------|---------|-------------|
| 3.1 | Build shared layout (Sidebar, Header, Providers) | `components/organisms/Sidebar.tsx` |
| 3.2 | Build atom components (Badge, Button, KPICard, StatusIcon) | `components/atoms/` |
| 3.3 | Build molecule components (FilterBar, DataTable, SummaryCards) | `components/molecules/` |
| 3.4 | Migrate Projects Dashboard page | `app/projects/page.tsx` |
| 3.5 | Migrate Execution Summary page | `app/projects/[id]/executions/page.tsx` |
| 3.6 | Migrate Trends page with Recharts | `app/projects/[id]/trends/page.tsx` |
| 3.7 | Migrate Module Details page | `app/projects/[id]/modules/[mid]/page.tsx` |
| 3.8 | Build Defect Management page (full CRUD) | `app/defects/page.tsx` |
| 3.9 | Build Settings page with form validation | `app/settings/page.tsx` |
| 3.10 | Implement TanStack Query hooks for all API calls | `hooks/` directory |
| 3.11 | Implement Zustand stores for UI state | `store/` directory |
| 3.12 | Add loading skeletons and error boundaries | Across all pages |

### Phase 4: Advanced Features (Weeks 9-10)

**Objective:** Implement AI analysis, real-time updates, and advanced UX.

| Task | Details | Deliverable |
|------|---------|-------------|
| 4.1 | Migrate AI Failure Analysis with streaming responses | `app/ai-analysis/page.tsx` |
| 4.2 | Implement WebSocket for real-time execution updates | `WS /api/v1/ws/executions` |
| 4.3 | Add export functionality (CSV, PDF reports) | Export components |
| 4.4 | Implement dark mode toggle | Theme provider |
| 4.5 | Add keyboard shortcuts and accessibility audit | WCAG 2.1 AA compliance |
| 4.6 | Implement notification system (toast + in-app) | Notification components |

### Phase 5: Performance Optimization & Hardening (Weeks 11-12)

**Objective:** Optimize for production-grade performance.

| Task | Details | Deliverable |
|------|---------|-------------|
| 5.1 | Implement Redis caching strategy (see Section 8) | Cache layer |
| 5.2 | Add database connection pooling (pgBouncer) | Connection pool config |
| 5.3 | Optimize Next.js bundle (code splitting, tree shaking) | Bundle analysis report |
| 5.4 | Implement virtual scrolling for large datasets | TanStack Virtual |
| 5.5 | Add API response compression (gzip/brotli) | Middleware |
| 5.6 | Configure CDN for static assets | Nginx/CDN config |
| 5.7 | Performance profiling and bottleneck resolution | Lighthouse report |
| 5.8 | Security hardening (CSP, HSTS, input sanitization) | Security headers |

### Phase 6: Testing, QA & Deployment (Weeks 13-14)

**Objective:** Comprehensive testing and production deployment.

| Task | Details | Deliverable |
|------|---------|-------------|
| 6.1 | Write Jest + RTL unit tests for React components | Frontend tests |
| 6.2 | Write Playwright E2E tests for critical flows | E2E test suite |
| 6.3 | Write Pytest integration tests for all API endpoints | Backend tests |
| 6.4 | Load testing with k6 or Locust | Performance benchmarks |
| 6.5 | Set up Kubernetes Helm charts | `k8s/` directory |
| 6.6 | Configure monitoring (Prometheus + Grafana) | Dashboards |
| 6.7 | Set up structured logging (Loki/ELK) | Log aggregation |
| 6.8 | Production deployment and smoke testing | Live deployment |
| 6.9 | Documentation (API docs, runbooks, architecture) | `docs/` directory |

---

## 8. Performance Optimizations

### 8.1 Caching Strategy (Multi-Layer)

```
┌─────────────────────────────────────────────────────────────┐
│                    CACHING LAYERS                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: Browser Cache (HTTP Cache Headers)                │
│  ├── Static assets: Cache-Control: max-age=31536000        │
│  ├── API responses: ETag + If-None-Match                   │
│  └── Next.js ISR: revalidate pages on interval             │
│                                                             │
│  Layer 2: TanStack Query (Client-Side)                     │
│  ├── staleTime: 5 minutes (projects list)                  │
│  ├── staleTime: 1 minute (execution data)                  │
│  ├── gcTime: 30 minutes                                    │
│  └── Background refetch on window focus                    │
│                                                             │
│  Layer 3: Redis (Server-Side)                              │
│  ├── Project overview: TTL 5 min, invalidate on mutation   │
│  ├── Execution data: TTL 2 min, invalidate on upload       │
│  ├── Module list: TTL 10 min, invalidate on project change │
│  ├── Trend data: TTL 5 min, invalidate on new execution    │
│  └── Session data: TTL 24 hours                            │
│                                                             │
│  Layer 4: Database Query Cache (PostgreSQL)                │
│  ├── Prepared statements                                   │
│  ├── Connection pooling (pgBouncer)                        │
│  └── Materialized views for aggregations                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Redis Cache Implementation

```python
# Production: app/core/cache.py
import redis.asyncio as redis
from functools import wraps
import json
import hashlib

class CacheService:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)
    
    async def get(self, key: str):
        data = await self.redis.get(key)
        return json.loads(data) if data else None
    
    async def set(self, key: str, value: any, ttl: int = 300):
        await self.redis.setex(key, ttl, json.dumps(value, default=str))
    
    async def invalidate_pattern(self, pattern: str):
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await self.redis.delete(*keys)

def cached(ttl: int = 300, prefix: str = ""):
    """Decorator replacing POC's timed_cache with Redis-backed cache"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{prefix}:{func.__name__}:{hashlib.md5(str(args).encode()).hexdigest()}"
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            result = await func(*args, **kwargs)
            await cache_service.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
```

### 8.3 Frontend Performance Optimizations

| Optimization | Implementation | Impact |
|-------------|----------------|--------|
| **Code Splitting** | Next.js automatic route-based splitting | Reduce initial bundle by ~60% |
| **Lazy Loading** | `React.lazy()` for heavy components (charts, modals) | Faster first paint |
| **Virtual Scrolling** | TanStack Virtual for tables with 1000+ rows | Constant memory usage |
| **Image Optimization** | Next.js `<Image>` with WebP/AVIF | 50-80% smaller images |
| **Memoization** | `React.memo()`, `useMemo()`, `useCallback()` | Prevent unnecessary re-renders |
| **Debounced Search** | `useDebounce()` hook for filter inputs | Reduce API calls |
| **Optimistic Updates** | TanStack Query mutations with optimistic UI | Instant perceived performance |
| **Prefetching** | `<Link prefetch>` for likely navigation targets | Zero-latency page transitions |
| **Bundle Analysis** | `@next/bundle-analyzer` | Identify and eliminate bloat |

### 8.4 Backend Performance Optimizations

| Optimization | Implementation | Impact |
|-------------|----------------|--------|
| **N+1 Query Fix** | Single JOIN query for project listing | 3N → 1 queries |
| **Connection Pooling** | pgBouncer with 20 connections | Prevent connection exhaustion |
| **Async I/O** | All DB operations async (already in POC) | Non-blocking request handling |
| **Response Compression** | GzipMiddleware in FastAPI | 60-80% smaller responses |
| **Pagination** | Cursor-based pagination for large datasets | Constant query time |
| **Background Tasks** | FastAPI BackgroundTasks for report processing | Non-blocking uploads |
| **Database Indexes** | Strategic indexes on query patterns | 10-100x faster queries |
| **Prepared Statements** | SQLAlchemy compiled cache | Reduced query parsing |

### 8.5 Performance Benchmarks (Target)

| Metric | POC (Estimated) | Production Target |
|--------|-----------------|-------------------|
| **First Contentful Paint** | ~3-5s (server render) | < 1.0s |
| **Time to Interactive** | ~5-8s | < 2.0s |
| **API Response (p95)** | ~500ms | < 100ms |
| **Projects List Load** | ~2-3s (N+1 queries) | < 200ms (cached) |
| **Execution Table Render** | ~1-2s (full re-render) | < 50ms (virtual scroll) |
| **Chart Render** | ~1s (Plotly load) | < 200ms (Recharts) |
| **Bundle Size (JS)** | ~1.5MB (Plotly alone) | < 200KB (initial) |
| **Lighthouse Score** | ~40-50 | > 90 |
| **Concurrent Users** | ~10-20 | 500+ |

---

## 9. Deployment Strategy

### 9.1 Container Architecture

```yaml
# Production docker-compose.yml (development)
services:
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000/api/v1
    depends_on:
      backend:
        condition: service_healthy

  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/taps
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 10s
      retries: 5

  postgres:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=taps
      - POSTGRES_USER=taps_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U taps_user -d taps"]
      interval: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru

  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
  redis_data:
```

### 9.2 Kubernetes Deployment (Production)

```
k8s/
├── helm/
│   └── taps/
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── values-staging.yaml
│       ├── values-production.yaml
│       └── templates/
│           ├── frontend-deployment.yaml
│           ├── backend-deployment.yaml
│           ├── postgres-statefulset.yaml
│           ├── redis-deployment.yaml
│           ├── ingress.yaml
│           ├── hpa.yaml              # Horizontal Pod Autoscaler
│           ├── configmap.yaml
│           └── secrets.yaml
```

### 9.3 CI/CD Pipeline (GitHub Actions)

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Commit  │───▶│  Lint +  │───▶│  Test    │───▶│  Build   │───▶│  Deploy  │
│  Push    │    │  Format  │    │  Suite   │    │  Images  │    │  (Env)   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                │ ESLint        │ Jest (FE)     │ Docker        │ Staging
                │ Prettier      │ Pytest (BE)   │ Multi-stage   │ Production
                │ Ruff          │ Playwright    │ Push to       │ Helm upgrade
                │ TypeScript    │ (E2E)         │ Registry      │ Smoke tests
                │ check         │               │               │
```

### 9.4 Environment Management

| Environment | Purpose | Database | Deployment |
|-------------|---------|----------|------------|
| **Development** | Local development | PostgreSQL (Docker) | `docker-compose up` |
| **Staging** | Pre-production testing | PostgreSQL (managed) | Kubernetes (auto-deploy on `main`) |
| **Production** | Live users | PostgreSQL (managed, HA) | Kubernetes (manual approval) |

### 9.5 Monitoring & Observability

```
┌─────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY STACK                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Metrics:    OpenTelemetry → Prometheus → Grafana           │
│  ├── API latency (p50, p95, p99)                           │
│  ├── Request rate and error rate                           │
│  ├── Database query duration                               │
│  ├── Redis hit/miss ratio                                  │
│  └── Frontend Core Web Vitals                              │
│                                                             │
│  Logging:    Structured JSON → Loki → Grafana              │
│  ├── Request/response logging with correlation IDs         │
│  ├── Error logging with stack traces                       │
│  └── Audit logging for auth events                         │
│                                                             │
│  Tracing:    OpenTelemetry → Jaeger/Tempo                  │
│  ├── Distributed request tracing                           │
│  ├── Database query tracing                                │
│  └── External API call tracing                             │
│                                                             │
│  Alerting:   Grafana Alerting → Slack/PagerDuty            │
│  ├── Error rate > 1% for 5 minutes                         │
│  ├── API p95 latency > 500ms                               │
│  ├── Database connection pool exhaustion                   │
│  └── Redis memory > 80%                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 10. Risk Assessment & Mitigation

| # | Risk | Probability | Impact | Mitigation |
|---|------|-------------|--------|------------|
| 1 | **Data loss during SQLite → PostgreSQL migration** | Medium | Critical | Backup SQLite before migration; validate row counts; run checksums; keep SQLite as fallback for 2 weeks |
| 2 | **Frontend migration takes longer than estimated** | High | High | Migrate pages incrementally; keep Dash running in parallel during transition; feature flag new pages |
| 3 | **API contract changes break existing integrations** | Medium | High | Version APIs (`/api/v1/`); maintain backward compatibility; deprecation notices; integration tests |
| 4 | **Performance regression in production** | Low | High | Load test before deployment; canary releases; feature flags; rollback plan; performance budgets |
| 5 | **Team learning curve (React/TypeScript)** | High | Medium | Pair programming; code reviews; start with simple pages; provide TypeScript training |
| 6 | **Redis cache inconsistency** | Medium | Medium | Cache invalidation on mutations; short TTLs; fallback to DB on cache miss; monitoring |
| 7 | **Authentication implementation complexity** | Medium | Medium | Use battle-tested libraries (python-jose, passlib); follow OWASP guidelines; security review |
| 8 | **Docker/K8s operational complexity** | Medium | Medium | Start with Docker Compose; graduate to K8s when needed; use managed K8s (EKS/GKE/AKS) |
| 9 | **Scope creep during migration** | High | Medium | Strict phase gates; MVP per phase; defer nice-to-haves; weekly progress reviews |
| 10 | **AI/ML integration instability** | Medium | Low | Abstract AI service behind interface; graceful degradation; timeout handling; mock fallback |

---

## 11. Testing Strategy

### 11.1 Testing Pyramid

```
                    ┌───────────┐
                    │   E2E     │  ~20 tests
                    │ Playwright│  Critical user flows
                   ┌┴───────────┴┐
                   │ Integration  │  ~50 tests
                   │ API + DB     │  All endpoints
                  ┌┴──────────────┴┐
                  │   Unit Tests    │  ~200+ tests
                  │ Components +   │  All components,
                  │ Services       │  services, utils
                  └────────────────┘
```

### 11.2 Frontend Testing

| Layer | Tool | Coverage Target | What to Test |
|-------|------|-----------------|---------------|
| **Unit** | Jest + React Testing Library | 80%+ | Component rendering, user interactions, hooks, utilities |
| **Integration** | Jest + MSW (Mock Service Worker) | Key flows | API integration, state management, data flow |
| **E2E** | Playwright | Critical paths | Login → Projects → Execution → Trends → AI Analysis |
| **Visual** | Chromatic (optional) | UI components | Visual regression detection |
| **Accessibility** | jest-axe + Lighthouse CI | All pages | WCAG 2.1 AA compliance |

### 11.3 Backend Testing

| Layer | Tool | Coverage Target | What to Test |
|-------|------|-----------------|---------------|
| **Unit** | Pytest + pytest-asyncio | 85%+ | Services, parsers, utilities, validators |
| **Integration** | Pytest + httpx.AsyncClient | All endpoints | API endpoints with test database |
| **Load** | k6 or Locust | Performance targets | Concurrent users, response times, throughput |
| **Security** | Bandit + Safety | All code | Vulnerability scanning, dependency audit |

### 11.4 Critical E2E Test Scenarios

1. **Project Lifecycle**: Create project → Upload report → View execution summary → View trends
2. **Drill-Down Flow**: Projects → Select project → Execution summary → Module details → Scenario details
3. **Defect Workflow**: View failed scenario → Link defect → View in defect management → Update status
4. **AI Analysis Flow**: Select project → View failures → Generate AI insight → View recommendation
5. **Settings Flow**: Create project → Edit project → Verify in projects list
6. **Filter & Search**: Apply date filter → Module filter → Status filter → Verify results

---

## 12. Appendix

### 12.1 Dependency Comparison

#### Backend Dependencies (POC → Production)

| POC Dependency | Production Equivalent | Reason |
|---------------|----------------------|--------|
| `fastapi` | `fastapi>=0.110.0` | Upgrade to latest |
| `uvicorn[standard]` | `uvicorn[standard]` | Retained |
| `sqlalchemy` | `sqlalchemy>=2.0` | Upgrade to 2.0 syntax |
| `python-multipart` | `python-multipart` | Retained (file uploads) |
| `dash` | **REMOVED** | Replaced by Next.js frontend |
| `dash-bootstrap-components` | **REMOVED** | Replaced by shadcn/ui |
| `pandas` | **REMOVED from backend** | Move data processing to SQL |
| `plotly` | **REMOVED** | Replaced by Recharts (frontend) |
| `asyncpg` | `asyncpg>=0.29.0` | Retained |
| `psycopg2-binary` | `psycopg2-binary` | Retained (sync operations) |
| `httpx` | `httpx` | Retained (external API calls) |
| `alembic` | `alembic>=1.13.0` | Upgrade |
| `elasticsearch` | `elasticsearch` | Retained (if used) |
| `python-jose` | `python-jose[cryptography]` | Retained + enhanced |
| `passlib` | `passlib[bcrypt]` | Retained + enhanced |
| `python-dotenv` | `pydantic-settings` | Better config management |
| `aiosqlite` | **REMOVED** | No SQLite in production |
| `aiohttp` | **REMOVED** | Use httpx instead |
| *(none)* | `redis[hiredis]` | **NEW**: Redis caching |
| *(none)* | `opentelemetry-*` | **NEW**: Observability |
| *(none)* | `structlog` | **NEW**: Structured logging |
| *(none)* | `gunicorn` | **NEW**: Production ASGI server |

#### Frontend Dependencies (NEW)

```json
{
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "typescript": "^5.4.0",
    "@tanstack/react-query": "^5.0.0",
    "@tanstack/react-table": "^8.0.0",
    "@tanstack/react-virtual": "^3.0.0",
    "zustand": "^4.5.0",
    "recharts": "^2.12.0",
    "tailwindcss": "^3.4.0",
    "axios": "^1.7.0",
    "zod": "^3.23.0",
    "react-hook-form": "^7.51.0",
    "@hookform/resolvers": "^3.3.0",
    "date-fns": "^3.6.0",
    "lucide-react": "^0.370.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.3.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/node": "^20.0.0",
    "eslint": "^8.57.0",
    "eslint-config-next": "^14.2.0",
    "prettier": "^3.2.0",
    "jest": "^29.7.0",
    "@testing-library/react": "^15.0.0",
    "@testing-library/jest-dom": "^6.4.0",
    "@playwright/test": "^1.43.0",
    "@next/bundle-analyzer": "^14.2.0"
  }
}
```

### 12.2 Migration Checklist

- [ ] **Phase 1**: Project structure initialized
- [ ] **Phase 1**: PostgreSQL + Redis running
- [ ] **Phase 1**: Alembic migrations created
- [ ] **Phase 1**: CI/CD pipeline operational
- [ ] **Phase 1**: Data migrated from SQLite
- [ ] **Phase 2**: Authentication implemented
- [ ] **Phase 2**: All API endpoints migrated
- [ ] **Phase 2**: N+1 queries fixed
- [ ] **Phase 2**: Redis caching operational
- [ ] **Phase 2**: Backend tests passing
- [ ] **Phase 3**: Sidebar and layout built
- [ ] **Phase 3**: All 7 pages migrated to React
- [ ] **Phase 3**: TanStack Query hooks implemented
- [ ] **Phase 3**: Loading states and error boundaries
- [ ] **Phase 4**: AI analysis with streaming
- [ ] **Phase 4**: WebSocket real-time updates
- [ ] **Phase 4**: Export functionality
- [ ] **Phase 5**: Redis caching strategy implemented
- [ ] **Phase 5**: Performance benchmarks met
- [ ] **Phase 5**: Lighthouse score > 90
- [ ] **Phase 6**: Unit test coverage > 80%
- [ ] **Phase 6**: E2E tests for critical flows
- [ ] **Phase 6**: Load testing completed
- [ ] **Phase 6**: Monitoring dashboards configured
- [ ] **Phase 6**: Production deployment successful

### 12.3 Estimated Timeline

| Phase | Duration | Team Size | Key Milestone |
|-------|----------|-----------|---------------|
| Phase 1: Foundation | 2 weeks | 2 engineers | Infrastructure ready |
| Phase 2: Backend | 2 weeks | 2 engineers | APIs hardened + tested |
| Phase 3: Frontend | 4 weeks | 2-3 engineers | All pages migrated |
| Phase 4: Advanced | 2 weeks | 2 engineers | AI + real-time features |
| Phase 5: Performance | 2 weeks | 1-2 engineers | Performance targets met |
| Phase 6: Testing/Deploy | 2 weeks | 2 engineers | Production live |
| **Total** | **~14 weeks** | **2-3 engineers** | **Production-ready TAPS** |

---

*Document Version: 1.0*  
*Created: Based on POC analysis of test-analytics-portal*  
*Status: Migration Plan — Ready for Review*