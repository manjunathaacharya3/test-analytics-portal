/**
 * API Service Layer for TAPS Frontend
 * 
 * This service handles all HTTP requests to the backend API.
 * It provides type-safe methods for all API endpoints.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_VERSION = '/api/v1';

// Types matching backend ProjectOverviewResponse
export interface Project {
  id: string; // UUID from backend
  name: string;
  description?: string;
  repository_url?: string;
  owner: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  // Aggregated metrics from ProjectOverviewResponse
  modules: number;
  total_tests: number;
  pass_rate: number;
  last_status?: string;
  last_run?: string;
}

export interface Execution {
  id: number;
  project_id: number;
  module_name?: string;
  start_time: string;
  end_time?: string;
  duration_seconds?: number;
  total_scenarios: number;
  passed: number;
  failed: number;
  skipped: number;
  status: 'running' | 'passed' | 'failed' | 'skipped';
}

export interface Scenario {
  id: number;
  execution_id: number;
  name: string;
  status: 'passed' | 'failed' | 'skipped';
  duration_seconds?: number;
  error_message?: string;
  steps?: any[];
}

export interface Defect {
  id: number;
  project_id: number;
  scenario_id?: number;
  title: string;
  description?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'open' | 'in_progress' | 'fixed' | 'closed';
  assignee?: string;
  created_at: string;
  updated_at?: string;
}

export interface Module {
  id: string;
  project_id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface TrendData {
  date: string;
  pass_rate?: number;
  total_tests?: number;
  duration?: number;
}

// Real failed scenario data (no AI-generated fields - there is no AI/ML
// backend producing confidence scores, root cause, similar failures, etc.)
export interface FailedScenario {
  id: string;
  name: string;
  status: string;
  duration?: number;
  error_message?: string;
  stack_trace?: string;
  tags: string[];
  feature?: string;
  created_at: string;
  project_id: string;
  project_name: string;
  module_id: string;
  module_name: string;
}

export interface FailedScenarioListResponse {
  scenarios: FailedScenario[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface AnalyticsSummary {
  total_projects: number;
  total_executions: number;
  total_scenarios: number;
  overall_pass_rate: number;
  active_defects: number;
}

// Note: ApiResponse interface removed - direct API responses used

/**
 * API Error
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public details?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Generic fetch wrapper with error handling
 */
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${API_VERSION}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers:
{
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        response.status,
        errorData.message || `HTTP ${response.status}: ${response.statusText}`,
        errorData
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    
    // Network error or other fetch errors
    throw new ApiError(
      0,
      error instanceof Error ? error.message : 'Network error',
      error
    );
  }
}

/**
 * API Service Object
 */
export const apiService = {
  /**
   * Projects API
   */
  projects: {
    /**
     * Get all projects
     */
    getAll: async (): Promise<Project[]> => {
      return apiFetch<Project[]>('/projects');
    },

    /**
     * Get project by ID
     */
    getById: async (id: number): Promise<Project> => {
      return apiFetch<Project>(`/projects/${id}`);
    },

    /**
     * Create new project
     */
    create: async (data: Partial<Project>): Promise<Project> => {
      return apiFetch<Project>('/projects', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    /**
     * Update project
     */
    update: async (id: number, data: Partial<Project>): Promise<Project> => {
      return apiFetch<Project>(`/projects/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });
    },

    /**
     * Delete project
     */
    delete: async (id: number): Promise<void> => {
      return apiFetch<void>(`/projects/${id}`, {
        method: 'DELETE',
      });
    },
  },

  /**
   * Executions API
   */
  executions: {
    /**
     * Get all executions
     */
    getAll: async (params?: {
      project_id?: number;
      limit?: number;
      skip?: number;
    }): Promise<Execution[]> => {
      const query = new URLSearchParams();
      if (params?.project_id) query.append('project_id', params.project_id.toString());
      if (params?.limit) query.append('limit', params.limit.toString());
      if (params?.skip) query.append('skip', params.skip.toString());
      
      const queryString = query.toString();
      return apiFetch<Execution[]>(
        `/executions${queryString ? `?${queryString}` : ''}`
      );
    },

    /**
     * Get execution by ID
     */
    getById: async (id: number): Promise<Execution> => {
      return apiFetch<Execution>(`/executions/${id}`);
    },

    /**
     * Get executions by project
     */
    getByProject: async (projectId: number): Promise<Execution[]> => {
      return apiFetch<Execution[]>(`/projects/${projectId}/executions`);
    },
  },

  /**
   * Scenarios API
   */
  scenarios: {
    /**
     * Get scenarios by execution ID
     */
    getByExecution: async (executionId: number): Promise<Scenario[]> => {
      return apiFetch<Scenario[]>(`/executions/${executionId}/scenarios`);
    },

    /**
     * Get scenario by ID
     */
    getById: async (id: number): Promise<Scenario> => {
      return apiFetch<Scenario>(`/scenarios/${id}`);
    },

    /**
     * Get failed scenarios, enriched with project/module context.
     * Used by the AI Insights / Failure Analysis page.
     */
    getFailures: async (params?: {
      project_id?: string;
      module_id?: string;
      search?: string;
      page?: number;
      size?: number;
    }): Promise<FailedScenarioListResponse> => {
      const query = new URLSearchParams();
      if (params?.project_id) query.append('project_id', params.project_id);
      if (params?.module_id) query.append('module_id', params.module_id);
      if (params?.search) query.append('search', params.search);
      if (params?.page) query.append('page', params.page.toString());
      if (params?.size) query.append('size', params.size.toString());

      const queryString = query.toString();
      return apiFetch<FailedScenarioListResponse>(
        `/scenarios/failures${queryString ? `?${queryString}` : ''}`
      );
    },
  },

  /**
   * Modules API
   */
  modules: {
    /**
     * Get modules by project ID
     */
    getByProject: async (projectId: string): Promise<Module[]> => {
      return apiFetch<Module[]>(`/projects/${projectId}/modules`);
    },

    /**
     * Create new module
     */
    create: async (projectId: string, data: { name: string; description?: string }): Promise<Module> => {
      return apiFetch<Module>(`/projects/${projectId}/modules`, {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    /**
     * Update module
     */
    update: async (projectId: string, moduleId: string, data: { name: string; description?: string }): Promise<Module> => {
      return apiFetch<Module>(`/projects/${projectId}/modules/${moduleId}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });
    },

    /**
     * Delete module
     */
    delete: async (projectId: string, moduleId: string): Promise<void> => {
      return apiFetch<void>(`/projects/${projectId}/modules/${moduleId}`, {
        method: 'DELETE',
      });
    },
  },

  /**
   * Defects API
   */
  defects: {
    /**
     * Get all defects
     */
    getAll: async (params?: {
      project_id?: number;
      status?: string;
      severity?: string;
    }): Promise<Defect[]> => {
      const query = new URLSearchParams();
      if (params?.project_id) query.append('project_id', params.project_id.toString());
      if (params?.status) query.append('status', params.status);
      if (params?.severity) query.append('severity', params.severity);
      
      const queryString = query.toString();
      return apiFetch<Defect[]>(
        `/defects${queryString ? `?${queryString}` : ''}`
      );
    },

    /**
     * Get defect by ID
     */
    getById: async (id: number): Promise<Defect> => {
      return apiFetch<Defect>(`/defects/${id}`);
    },

    /**
     * Create defect
     */
    create: async (data: Partial<Defect>): Promise<Defect> => {
      return apiFetch<Defect>('/defects', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    /**
     * Update defect
     */
    update: async (id: number, data: Partial<Defect>): Promise<Defect> => {
      return apiFetch<Defect>(`/defects/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });
    },
  },

  /**
   * Analytics API
   */
  analytics: {
    /**
     * Get analytics summary
     */
    getSummary: async (): Promise<AnalyticsSummary> => {
      return apiFetch<AnalyticsSummary>('/analytics/summary');
    },

    /**
     * Get trend data
     *
     * NOTE: The backend /analytics/trends endpoint returns a wrapper object
     * shaped like { data_points: TrendData[], period: string }, NOT a bare
     * array. We unwrap it here so callers can keep working with a simple
     * TrendData[] as before.
     */
    getTrends: async (params: {
      project_id?: string;
      days?: number;
    }): Promise<TrendData[]> => {
      const query = new URLSearchParams();
      if (params.project_id) query.append('project_id', params.project_id);
      if (params.days) query.append('days', params.days.toString());

      const response = await apiFetch<{ data_points: TrendData[]; period: string }>(
        `/analytics/trends?${query.toString()}`
      );

      return response?.data_points ?? [];
    },
  },

  /**
   * Health Check
   */
  health: {
    check: async (): Promise<{ status: string; version: string }> => {
      const response = await fetch(`${API_BASE_URL}/health`);
      return response.json();
    },
  },
};

export default apiService;
