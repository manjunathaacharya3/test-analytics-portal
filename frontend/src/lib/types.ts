/**
 * Common type definitions for the application
 */

// ============================================================================
// API Error Types
// ============================================================================

export interface APIError {
  detail: string;
  status?: number;
  errors?: Record<string, string[]>;
}

// ============================================================================
// Project Types
// ============================================================================

export interface ProjectOverview {
  id: string;
  name: string;
  description: string | null;
  repository_url: string | null;
  owner: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_run: string | null;
  total_tests: number;
  pass_rate: number | null;
  last_status: string | null;
}

export interface ProjectFilters {
  page?: number;
  size?: number;
  is_active?: boolean;
  owner?: string;
  search?: string;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  repository_url?: string;
  owner: string;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  repository_url?: string;
  owner?: string;
  is_active?: boolean;
}

export interface Module {
  id: string;
  name: string;
  description: string | null;
  project_id: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// Execution Types
// ============================================================================

export interface Execution {
  id: string;
  project_id: string;
  module_id: string;
  file_name: string;
  file_size: number;
  total_scenarios: number;
  passed_scenarios: number;
  failed_scenarios: number;
  skipped_scenarios: number;
  duration: number | null;
  uploaded_by: string;
  created_at: string;
  pass_rate: number;
  status: "passed" | "failed" | "mixed";
  module_name?: string; // Optional, may be joined from module table
}

export interface ExecutionFilters {
  page?: number;
  size?: number;
  status?: string;
  module_id?: string;
  date_from?: string;
  date_to?: string;
}

export interface ExecutionListResponse {
  executions: Execution[];
  total: number;
  page: number;
  size: number;
  total_pages: number;
}

// ============================================================================
// Scenario Types
// ============================================================================

export interface Scenario {
  id: string;
  report_id: string;
  name: string;
  status: "passed" | "failed" | "skipped";
  duration: number | null;
  error_message: string | null;
  stack_trace: string | null;
  tags: string | null;
  feature: string | null;
  created_at: string;
}

export interface ScenarioListResponse {
  scenarios: Scenario[];
  total: number;
  page: number;
  size: number;
  total_pages: number;
}

// ============================================================================
// Export Types
// ============================================================================

export interface ExportOptions {
  format: "csv" | "json" | "excel";
  filename?: string;
  columns?: string[];
}
