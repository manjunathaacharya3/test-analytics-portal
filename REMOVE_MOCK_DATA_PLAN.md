# 🗑️ Remove Mock Data from All Pages - Implementation Plan

**Goal:** Update all frontend pages to use real backend APIs instead of mock data

---

## 📊 Pages Analysis Summary

| Page | Mock Data | Backend Support | Priority | Status |
|------|-----------|----------------|----------|--------|
| 1. Projects | ✅ Yes | ✅ Full | HIGH | ✅ **DONE** |
| 2. Execution Summary | ✅ Yes | ✅ Full | HIGH | 🔄 TODO |
| 3. Module Details | ✅ Yes | ✅ Full | HIGH | 🔄 TODO |
| 4. Defect Management | ✅ Yes | ✅ Full | HIGH | 🔄 TODO |
| 5. Settings | ✅ Yes | ✅ Full | MEDIUM | 🔄 TODO |
| 6. Trends | ✅ Yes | ⚠️ Partial | MEDIUM | 🔄 TODO |
| 7. AI Failure Analysis | ✅ Yes | ❌ None | LOW | ⏸️ BLOCKED |
| 8. Home (Dashboard) | Unknown | ✅ Full | LOW | 🔄 TODO |

---

## 🎯 Implementation Strategy

### **Phase 1: Core Pages (HIGH Priority)** ✅
1. ✅ **Projects Page** - DONE
   - Removed mock data
   - Using `/api/v1/projects`
   - UUID support added

### **Phase 2: Data Pages (HIGH Priority)** 🔄
2. **Execution Summary Page**
   - Remove: `summaryData`, `executionData`
   - Add API: `/api/v1/projects/{id}/executions`
   - Add API: `/api/v1/analytics/dashboard`

3. **Module Details Page**
   - Remove: `MOCK_PROJECTS`, `MOCK_MODULES`, `MOCK_EXECUTION_RUNS`, `MOCK_SCENARIOS`
   - Add API: `/api/v1/projects/{id}/modules`
   - Add API: `/api/v1/modules/{id}/executions`
   - Add API: `/api/v1/executions/{id}/scenarios`

4. **Defect Management Page**
   - Remove: `mockDefects`, `mockProjects`
   - Add API: `/api/v1/defects`
   - Add API: `/api/v1/projects` (for filter)
   - Add CRUD operations

### **Phase 3: Settings (MEDIUM Priority)** 🔄
5. **Settings Page**
   - Remove: `mockProject`
   - Add API: `/api/v1/projects/{id}` (GET/PUT)
   - Add API: `/api/v1/projects` (POST)

### **Phase 4: Analytics (MEDIUM Priority)** 🔄
6. **Trends Page**
   - Remove: `mockPassRateData`, `mockDurationData`, `mockProjects`, `mockModules`
   - Add API: `/api/v1/analytics/trends`
   - Add API: `/api/v1/projects` (for filters)

### **Phase 5: Advanced Features (LOW Priority)** ⏸️
7. **AI Failure Analysis Page**
   - Status: **BLOCKED** - Backend not implemented
   - Keep mock data until backend APIs are created
   - Required endpoints:
     - `GET /api/v1/analytics/ai-failures`
     - `GET /api/v1/scenarios/{id}/ai-analysis`

---

## 🔧 Implementation Details

### **1. Execution Summary Page**

**Current Mock Data:**
```typescript
const summaryData = {
  passRate: 87.3,
  totalTests: 1543,
  totalDuration: 12450
};

const executionData = [
  { id: 1, moduleName: 'Login Module', passed: 45, failed: 5, total: 50, ... },
  // ... 7 more items
];
```

**API Integration:**
```typescript
// Add to apiService.ts
executions: {
  getByProject: async (projectId: string) => {
    return apiFetch<Execution[]>(`/projects/${projectId}/executions`);
  }
},
analytics: {
  getDashboard: async (projectId: string) => {
    return apiFetch<DashboardMetrics>(`/analytics/dashboard?project_id=${projectId}`);
  }
}

// Update page component
const fetchData = async () => {
  const [dashboard, executions] = await Promise.all([
    apiService.analytics.getDashboard(projectId),
    apiService.executions.getByProject(projectId)
  ]);
  setSummaryData(dashboard);
  setExecutionData(executions);
};
```

---

### **2. Module Details Page**

**Current Mock Data:**
```typescript
const MOCK_PROJECTS = [{id: 1, name: 'E-Commerce'}, ...];
const MOCK_MODULES = { '1': [{id: 1, name: 'Login'}, ...] };
const MOCK_EXECUTION_RUNS = [...];
const MOCK_SCENARIOS = [...];
```

**API Integration:**
```typescript
// Add to apiService.ts
modules: {
  getByProject: async (projectId: string) => {
    return apiFetch<Module[]>(`/projects/${projectId}/modules`);
  },
  getExecutions: async (moduleId: string) => {
    return apiFetch<Execution[]>(`/modules/${moduleId}/executions`);
  }
},
scenarios: {
  getByExecution: async (executionId: string, status?: string) => {
    const query = status ? `?status=${status}` : '';
    return apiFetch<Scenario[]>(`/executions/${executionId}/scenarios${query}`);
  }
}

// Update page with cascading selects
const handleProjectChange = async (projectId: string) => {
  const modules = await apiService.modules.getByProject(projectId);
  setModules(modules);
};
```

---

### **3. Defect Management Page**

**Current Mock Data:**
```typescript
const mockDefects = [
  { id: 1, title: 'Login fails', severity: 'High', ... },
  // ... 5 more items
];
const mockProjects = ['E-commerce', 'Mobile App', ...];
```

**API Integration:**
```typescript
// Already exists in apiService.ts
defects: {
  getAll: async (filters?: DefectFilters) => {
    return apiFetch<Defect[]>('/defects', { params: filters });
  },
  create: async (defect: CreateDefect) => {
    return apiFetch<Defect>('/defects', { method: 'POST', body: defect });
  },
  update: async (id: string, defect: UpdateDefect) => {
    return apiFetch<Defect>(`/defects/${id}`, { method: 'PUT', body: defect });
  }
}

// Update page
const fetchDefects = async () => {
  const defects = await apiService.defects.getAll({
    project_id: selectedProject,
    status: selectedStatus,
    severity: selectedSeverity
  });
  setDefects(defects);
};
```

---

### **4. Settings Page**

**Current Mock Data:**
```typescript
const mockProject = {
  id: 1,
  name: 'E-Commerce Platform',
  owner: 'John Doe',
  description: '...',
  repositoryUrl: '...'
};
```

**API Integration:**
```typescript
// Already exists in apiService.ts
projects: {
  getById: async (id: string) => {
    return apiFetch<Project>(`/projects/${id}`);
  },
  create: async (project: CreateProject) => {
    return apiFetch<Project>('/projects', { method: 'POST', body: project });
  },
  update: async (id: string, project: UpdateProject) => {
    return apiFetch<Project>(`/projects/${id}`, { method: 'PUT', body: project });
  }
}

// Update page
const handleSave = async () => {
  if (isEditMode) {
    await apiService.projects.update(projectId, formData);
  } else {
    await apiService.projects.create(formData);
  }
  router.push('/projects');
};
```

---

### **5. Trends Page**

**Current Mock Data:**
```typescript
const mockPassRateData = [
  { date: '2024-01-01', passRate: 85 },
  // ... 13 more items
];
const mockDurationData = [...];
const mockProjects = ['Project 1', ...];
const mockModules = ['Module 1', ...];
```

**API Integration:**
```typescript
// Add to apiService.ts
analytics: {
  getTrends: async (projectId?: string, days: number = 14) => {
    const params = new URLSearchParams();
    if (projectId) params.append('project_id', projectId);
    params.append('days', days.toString());
    return apiFetch<TrendData[]>(`/analytics/trends?${params}`);
  }
}

// Update page
const fetchTrends = async () => {
  const data = await apiService.analytics.getTrends(selectedProject, 14);
  // Map to chart format
  const passRateData = data.map(d => ({
    date: d.date,
    passRate: d.pass_rate || 0
  }));
  setPassRateData(passRateData);
};
```

---

## ✅ Success Criteria

### **Per Page:**
- [ ] All mock data constants removed
- [ ] API service methods added/updated
- [ ] Loading states implemented
- [ ] Error handling implemented
- [ ] Empty states implemented
- [ ] Console logs for debugging
- [ ] TypeScript types aligned with backend

### **Overall:**
- [ ] No TypeScript errors
- [ ] Production build passes
- [ ] All pages display real data
- [ ] Graceful handling when no data exists
- [ ] Clear error messages when API fails

---

## 🚀 Execution Order

**Day 1:**
1. ✅ Projects Page (DONE)
2. 🔄 Defect Management (most independent)
3. 🔄 Settings Page (simple CRUD)

**Day 2:**
4. 🔄 Module Details (complex, many dropdowns)
5. 🔄 Execution Summary (depends on executions)

**Day 3:**
6. 🔄 Trends Page (analytics)
7. ⏸️ AI Failure Analysis (keep mock until backend ready)

---

## 📖 Related Documentation

- [FRONTEND_BACKEND_INTEGRATION_COMPLETE.md](FRONTEND_BACKEND_INTEGRATION_COMPLETE.md)
- [AUTHENTICATION_FIX_GUIDE.md](AUTHENTICATION_FIX_GUIDE.md)
- [BUILD_AND_TEST.md](BUILD_AND_TEST.md)

---

**Status:** Ready to implement Phase 2-4  
**Last Updated:** 2026-08-15
