"use client";

import { useQuery } from "@tanstack/react-query";
import { executionsAPI } from "@/lib/api";
import type {
  Execution,
  ExecutionFilters,
  ExecutionListResponse,
  ScenarioListResponse,
  APIError,
} from "@/lib/types";

/**
 * Query key factory for executions
 */
export const executionsKeys = {
  all: ["executions"] as const,
  lists: () => [...executionsKeys.all, "list"] as const,
  list: (projectId: string, filters?: ExecutionFilters) =>
    [...executionsKeys.lists(), projectId, filters] as const,
  details: () => [...executionsKeys.all, "detail"] as const,
  detail: (id: string) => [...executionsKeys.details(), id] as const,
  scenarios: (id: string, page?: number, size?: number, status?: string) =>
    [...executionsKeys.detail(id), "scenarios", { page, size, status }] as const,
  moduleExecutions: (moduleId: string, filters?: ExecutionFilters) =>
    [...executionsKeys.all, "module", moduleId, filters] as const,
};

/**
 * Hook to fetch executions for a project with optional filters
 * 
 * @param projectId - Project ID
 * @param filters - Optional filters for executions (page, size, status, module_id, date_from, date_to)
 * @returns Query result with executions data, loading state, and error
 * 
 * @example
 * ```tsx
 * const { data, isLoading, error } = useProjectExecutions("project-123", { status: "failed" });
 * ```
 */
export function useProjectExecutions(
  projectId: string,
  filters?: ExecutionFilters
) {
  return useQuery<ExecutionListResponse, APIError>({
    queryKey: executionsKeys.list(projectId, filters),
    queryFn: () => executionsAPI.getProjectExecutions(projectId, filters),
    enabled: !!projectId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    retry: 3,
    refetchOnWindowFocus: true,
  });
}

/**
 * Hook to fetch executions for a module with optional filters
 * 
 * @param moduleId - Module ID
 * @param filters - Optional filters for executions
 * @param enabled - Whether to enable the query (default: true)
 * @returns Query result with executions data
 * 
 * @example
 * ```tsx
 * const { data } = useModuleExecutions("module-123");
 * ```
 */
export function useModuleExecutions(
  moduleId: string,
  filters?: ExecutionFilters,
  enabled: boolean = true
) {
  return useQuery<ExecutionListResponse, APIError>({
    queryKey: executionsKeys.moduleExecutions(moduleId, filters),
    queryFn: () => executionsAPI.getModuleExecutions(moduleId, filters),
    enabled: enabled && !!moduleId,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    retry: 3,
  });
}

/**
 * Hook to fetch a single execution by ID
 * 
 * @param executionId - Execution ID
 * @param enabled - Whether to enable the query (default: true)
 * @returns Query result with execution data
 * 
 * @example
 * ```tsx
 * const { data: execution, isLoading } = useExecution("execution-123");
 * ```
 */
export function useExecution(executionId: string, enabled: boolean = true) {
  return useQuery<Execution, APIError>({
    queryKey: executionsKeys.detail(executionId),
    queryFn: () => executionsAPI.getExecution(executionId),
    enabled: enabled && !!executionId,
    staleTime: 5 * 60 * 1000,
    retry: 3,
  });
}

/**
 * Hook to fetch scenarios for an execution
 * 
 * @param executionId - Execution ID
 * @param page - Page number (default: 1)
 * @param size - Page size (default: 50)
 * @param status - Optional status filter
 * @param enabled - Whether to enable the query (default: true)
 * @returns Query result with scenarios data
 * 
 * @example
 * ```tsx
 * const { data: scenarios } = useExecutionScenarios("execution-123", 1, 50, "failed");
 * ```
 */
export function useExecutionScenarios(
  executionId: string,
  page: number = 1,
  size: number = 50,
  status?: string,
  enabled: boolean = true
) {
  return useQuery<ScenarioListResponse, APIError>({
    queryKey: executionsKeys.scenarios(executionId, page, size, status),
    queryFn: () =>
      executionsAPI.getExecutionScenarios(executionId, page, size, status),
    enabled: enabled && !!executionId,
    staleTime: 5 * 60 * 1000,
    retry: 3,
  });
}
