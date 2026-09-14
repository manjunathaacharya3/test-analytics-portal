/**
 * API client for Test Analytics Portal
 * 
 * Provides type-safe API calls to the backend with error handling,
 * authentication, and request/response transformation.
 */

import type {
  ProjectOverview,
  ProjectFilters,
  ProjectCreate,
  ProjectUpdate,
  Module,
  Execution,
  ExecutionFilters,
  ExecutionListResponse,
  ScenarioListResponse,
  APIError,
} from "./types";

// ============================================================================
// Configuration
// ============================================================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_VERSION = "v1";
const API_PREFIX = `/api/${API_VERSION}`;

// ============================================================================
// HTTP Client
// ============================================================================

class APIClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    // Get auth token from localStorage (if available)
    const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
    
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    // Add authorization header if token exists
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Handle non-OK responses
      if (!response.ok) {
        let errorDetail = "An error occurred";
        try {
          const errorData = await response.json();
          errorDetail = errorData.detail || errorData.message || errorDetail;
        } catch {
          errorDetail = response.statusText || errorDetail;
        }

        const error: APIError = {
          detail: errorDetail,
          status: response.status,
        };
        throw error;
      }

      // Handle 204 No Content
      if (response.status === 204) {
        return {} as T;
      }

      return await response.json();
    } catch (error) {
      // Re-throw APIError as-is
      if ((error as APIError).detail) {
        throw error;
      }

      // Wrap other errors
      const apiError: APIError = {
        detail: error instanceof Error ? error.message : "Network error occurred",
        status: 0,
      };
      throw apiError;
    }
  }

  async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const queryString = params
      ? "?" +
        Object.entries(params)
          .filter(([_, value]) => value !== undefined && value !== null)
          .map(
            ([key, value]) =>
              `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`
          )
          .join("&")
      : "";

    return this.request<T>(`${endpoint}${queryString}`, {
      method: "GET",
    });
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async patch<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PATCH",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: "DELETE",
    });
  }
}

const client = new APIClient(API_BASE_URL);

// ============================================================================
// Projects API
// ============================================================================

export const projectsAPI = {
  /**
   * Get all projects with optional filters
   */
  async getProjects(filters?: ProjectFilters): Promise<ProjectOverview[]> {
    return client.get<ProjectOverview[]>(`${API_PREFIX}/projects`, filters);
  },

  /**
   * Get a single project by ID
   */
  async getProject(projectId: string): Promise<ProjectOverview> {
    return client.get<ProjectOverview>(`${API_PREFIX}/projects/${projectId}`);
  },

  /**
   * Get modules for a project
   */
  async getProjectModules(projectId: string): Promise<Module[]> {
    return client.get<Module[]>(`${API_PREFIX}/projects/${projectId}/modules`);
  },

  /**
   * Create a new project
   */
  async createProject(data: ProjectCreate): Promise<ProjectOverview> {
    return client.post<ProjectOverview>(`${API_PREFIX}/projects`, data);
  },

  /**
   * Update an existing project
   */
  async updateProject(
    projectId: string,
    data: ProjectUpdate
  ): Promise<ProjectOverview> {
    return client.patch<ProjectOverview>(
      `${API_PREFIX}/projects/${projectId}`,
      data
    );
  },

  /**
   * Delete a project (soft delete)
   */
  async deleteProject(projectId: string): Promise<void> {
    return client.delete<void>(`${API_PREFIX}/projects/${projectId}`);
  },
};

// ============================================================================
// Executions API
// ============================================================================

export const executionsAPI = {
  /**
   * Get executions for a project
   */
  async getProjectExecutions(
    projectId: string,
    filters?: ExecutionFilters
  ): Promise<ExecutionListResponse> {
    return client.get<ExecutionListResponse>(
      `${API_PREFIX}/projects/${projectId}/executions`,
      filters
    );
  },

  /**
   * Get executions for a module
   */
  async getModuleExecutions(
    moduleId: string,
    filters?: ExecutionFilters
  ): Promise<ExecutionListResponse> {
    return client.get<ExecutionListResponse>(
      `${API_PREFIX}/modules/${moduleId}/executions`,
      filters
    );
  },

  /**
   * Get a single execution by ID
   */
  async getExecution(executionId: string): Promise<Execution> {
    return client.get<Execution>(`${API_PREFIX}/executions/${executionId}`);
  },

  /**
   * Get scenarios for an execution
   */
  async getExecutionScenarios(
    executionId: string,
    page: number = 1,
    size: number = 50,
    status?: string
  ): Promise<ScenarioListResponse> {
    return client.get<ScenarioListResponse>(
      `${API_PREFIX}/executions/${executionId}/scenarios`,
      { page, size, status }
    );
  },
};

// ============================================================================
// Export for convenience
// ============================================================================

export default client;
