"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { projectsAPI } from "@/lib/api";
import type {
  ProjectOverview,
  ProjectFilters,
  ProjectCreate,
  ProjectUpdate,
  APIError,
} from "@/lib/types";

/**
 * Query key factory for projects
 */
export const projectsKeys = {
  all: ["projects"] as const,
  lists: () => [...projectsKeys.all, "list"] as const,
  list: (filters?: ProjectFilters) => [...projectsKeys.lists(), filters] as const,
  details: () => [...projectsKeys.all, "detail"] as const,
  detail: (id: string) => [...projectsKeys.details(), id] as const,
  modules: (id: string) => [...projectsKeys.detail(id), "modules"] as const,
};

/**
 * Hook to fetch all projects with optional filters
 * 
 * @param filters - Optional filters for projects (page, size, is_active, owner, search)
 * @returns Query result with projects data, loading state, and error
 * 
 * @example
 * ```tsx
 * const { data: projects, isLoading, error } = useProjects({ is_active: true });
 * ```
 */
export function useProjects(filters?: ProjectFilters) {
  return useQuery<ProjectOverview[], APIError>({
    queryKey: projectsKeys.list(filters),
    queryFn: () => projectsAPI.getProjects(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    retry: 3,
    refetchOnWindowFocus: true,
  });
}

/**
 * Hook to fetch a single project by ID
 * 
 * @param projectId - Project ID
 * @param enabled - Whether to enable the query (default: true)
 * @returns Query result with project data, loading state, and error
 * 
 * @example
 * ```tsx
 * const { data: project, isLoading } = useProject("project-123");
 * ```
 */
export function useProject(projectId: string, enabled: boolean = true) {
  return useQuery({
    queryKey: projectsKeys.detail(projectId),
    queryFn: () => projectsAPI.getProject(projectId),
    enabled: enabled && !!projectId,
    staleTime: 5 * 60 * 1000,
    retry: 3,
  });
}

/**
 * Hook to fetch modules for a project
 * 
 * @param projectId - Project ID
 * @param enabled - Whether to enable the query (default: true)
 * @returns Query result with modules data
 * 
 * @example
 * ```tsx
 * const { data: modules } = useProjectModules("project-123");
 * ```
 */
export function useProjectModules(projectId: string, enabled: boolean = true) {
  return useQuery({
    queryKey: projectsKeys.modules(projectId),
    queryFn: () => projectsAPI.getProjectModules(projectId),
    enabled: enabled && !!projectId,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook to create a new project
 * 
 * @returns Mutation object with mutate function and status
 * 
 * @example
 * ```tsx
 * const createProject = useCreateProject();
 * 
 * const handleCreate = async (data: ProjectCreate) => {
 *   await createProject.mutateAsync(data);
 * };
 * ```
 */
export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ProjectCreate) => projectsAPI.createProject(data),
    onSuccess: () => {
      // Invalidate all project lists to refetch with new data
      queryClient.invalidateQueries({ queryKey: projectsKeys.lists() });
    },
  });
}

/**
 * Hook to update an existing project
 * 
 * @returns Mutation object with mutate function and status
 * 
 * @example
 * ```tsx
 * const updateProject = useUpdateProject();
 * 
 * const handleUpdate = async (id: string, data: ProjectUpdate) => {
 *   await updateProject.mutateAsync({ projectId: id, data });
 * };
 * ```
 */
export function useUpdateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, data }: { projectId: string; data: ProjectUpdate }) =>
      projectsAPI.updateProject(projectId, data),
    onSuccess: (_, variables) => {
      // Invalidate the specific project detail
      queryClient.invalidateQueries({
        queryKey: projectsKeys.detail(variables.projectId),
      });
      // Invalidate all project lists
      queryClient.invalidateQueries({ queryKey: projectsKeys.lists() });
    },
  });
}

/**
 * Hook to delete a project (soft delete)
 * 
 * @returns Mutation object with mutate function and status
 * 
 * @example
 * ```tsx
 * const deleteProject = useDeleteProject();
 * 
 * const handleDelete = async (id: string) => {
 *   await deleteProject.mutateAsync(id);
 * };
 * ```
 */
export function useDeleteProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId: string) => projectsAPI.deleteProject(projectId),
    onSuccess: (_, projectId) => {
      // Invalidate the specific project detail
      queryClient.invalidateQueries({ queryKey: projectsKeys.detail(projectId) });
      // Invalidate all project lists
      queryClient.invalidateQueries({ queryKey: projectsKeys.lists() });
    },
  });
}
