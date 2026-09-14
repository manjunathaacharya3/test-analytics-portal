"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { projectsAPI, executionsAPI } from "@/lib/api";
import type {
  ProjectOverview,
  Module,
  Execution,
  Scenario,
  APIError,
} from "@/lib/types";

type ExecutionStatus = "passed" | "failed" | "mixed";
type ScenarioStatus = "passed" | "failed" | "skipped";

interface DefectModalState {
  isOpen: boolean;
  scenarioId: string | null;
  scenarioName: string;
}

/**
 * Module Details Page
 * 
 * Displays detailed execution data for a specific module with:
 * - Cascading dropdowns for Project and Module selection
 * - Summary cards (Total Executions, Pass Rate, Avg Duration)
 * - Execution date filter
 * - Execution runs table with row selection
 * - Scenarios section (appears on row selection)
 * - Link Defect modal for failed scenarios
 */
export default function ModuleDetailsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const projectIdParam = searchParams.get("project") || "";
  const moduleIdParam = searchParams.get("module") || "";
  
  // State for filters - pre-select from URL if available
  const [selectedProject, setSelectedProject] = React.useState<string>(projectIdParam);
  const [selectedModule, setSelectedModule] = React.useState<string>(moduleIdParam);
  const [selectedDate, setSelectedDate] = React.useState<string>("all");
  
  // State for table selection
  const [selectedExecutionId, setSelectedExecutionId] = React.useState<string | null>(null);
  
  // State for defect modal
  const [defectModal, setDefectModal] = React.useState<DefectModalState>({
    isOpen: false,
    scenarioId: null,
    scenarioName: "",
  });
  const [defectId, setDefectId] = React.useState<string>("");
  const [defectError, setDefectError] = React.useState<string>("");
  
  // API Data States
  const [projects, setProjects] = React.useState<ProjectOverview[]>([]);
  const [modules, setModules] = React.useState<Module[]>([]);
  const [executions, setExecutions] = React.useState<Execution[]>([]);
  const [scenarios, setScenarios] = React.useState<Scenario[]>([]);
  
  // Loading States
  const [loadingProjects, setLoadingProjects] = React.useState<boolean>(false);
  const [loadingModules, setLoadingModules] = React.useState<boolean>(false);
  const [loadingExecutions, setLoadingExecutions] = React.useState<boolean>(false);
  const [loadingScenarios, setLoadingScenarios] = React.useState<boolean>(false);
  
  // Error States
  const [projectsError, setProjectsError] = React.useState<string>("");
  const [modulesError, setModulesError] = React.useState<string>("");
  const [executionsError, setExecutionsError] = React.useState<string>("");
  const [scenariosError, setScenariosError] = React.useState<string>("");
  
  // Fetch projects on mount
  React.useEffect(() => {
    const fetchProjects = async () => {
      console.log("[ModuleDetails] Fetching projects...");
      setLoadingProjects(true);
      setProjectsError("");
      try {
        const data = await projectsAPI.getProjects();
        console.log("[ModuleDetails] Projects fetched:", data);
        setProjects(data);
      } catch (error) {
        const errorMsg = (error as APIError).detail || "Failed to load projects";
        console.error("[ModuleDetails] Error fetching projects:", errorMsg);
        setProjectsError(errorMsg);
      } finally {
        setLoadingProjects(false);
      }
    };
    fetchProjects();
  }, []);
  
  // Fetch modules when project is selected
  React.useEffect(() => {
    if (!selectedProject) {
      setModules([]);
      setModulesError("");
      return;
    }
    
    const fetchModules = async () => {
      console.log(`[ModuleDetails] Fetching modules for project: ${selectedProject}`);
      setLoadingModules(true);
      setModulesError("");
      try {
        const data = await projectsAPI.getProjectModules(selectedProject);
        console.log("[ModuleDetails] Modules fetched:", data);
        setModules(data);
      } catch (error) {
        const errorMsg = (error as APIError).detail || "Failed to load modules";
        console.error("[ModuleDetails] Error fetching modules:", errorMsg);
        setModulesError(errorMsg);
      } finally {
        setLoadingModules(false);
      }
    };
    fetchModules();
  }, [selectedProject]);
  
  // Fetch executions when module is selected
  React.useEffect(() => {
    if (!selectedModule) {
      setExecutions([]);
      setExecutionsError("");
      return;
    }
    
    const fetchExecutions = async () => {
      console.log(`[ModuleDetails] Fetching executions for module: ${selectedModule}`);
      setLoadingExecutions(true);
      setExecutionsError("");
      try {
        const response = await executionsAPI.getModuleExecutions(selectedModule);
        console.log("[ModuleDetails] Executions fetched:", response);
        setExecutions(response.executions || []);
      } catch (error) {
        const errorMsg = (error as APIError).detail || "Failed to load executions";
        console.error("[ModuleDetails] Error fetching executions:", errorMsg);
        setExecutionsError(errorMsg);
      } finally {
        setLoadingExecutions(false);
      }
    };
    fetchExecutions();
  }, [selectedModule]);
  
  // Fetch scenarios when execution is selected
  React.useEffect(() => {
    if (!selectedExecutionId) {
      setScenarios([]);
      setScenariosError("");
      return;
    }
    
    const fetchScenarios = async () => {
      console.log(`[ModuleDetails] Fetching scenarios for execution: ${selectedExecutionId}`);
      setLoadingScenarios(true);
      setScenariosError("");
      try {
        const response = await executionsAPI.getExecutionScenarios(selectedExecutionId);
        console.log("[ModuleDetails] Scenarios fetched:", response);
        setScenarios(response.scenarios || []);
      } catch (error) {
        const errorMsg = (error as APIError).detail || "Failed to load scenarios";
        console.error("[ModuleDetails] Error fetching scenarios:", errorMsg);
        setScenariosError(errorMsg);
      } finally {
        setLoadingScenarios(false);
      }
    };
    fetchScenarios();
  }, [selectedExecutionId]);
  
  // Get unique execution dates
  const executionDates = React.useMemo(() => {
    const dates = executions.map(exec => exec.created_at.split('T')[0]);
    return ['all', ...Array.from(new Set(dates))];
  }, [executions]);
  
  // Filter execution runs by date
  const filteredExecutionRuns = React.useMemo(() => {
    if (selectedDate === 'all') return executions;
    return executions.filter(exec => 
      exec.created_at.startsWith(selectedDate)
    );
  }, [selectedDate, executions]);
  
  // Calculate summary metrics
  const summaryMetrics = React.useMemo(() => {
    const totalExecutions = filteredExecutionRuns.length;
    const totalPassed = filteredExecutionRuns.reduce((sum, exec) => sum + exec.passed_scenarios, 0);
    const totalTests = filteredExecutionRuns.reduce((sum, exec) => sum + exec.total_scenarios, 0);
    const passRate = totalTests > 0 ? (totalPassed / totalTests) * 100 : 0;
    
    // Calculate average duration (in seconds from backend)
    const totalSeconds = filteredExecutionRuns.reduce((sum, exec) => {
      return sum + (exec.duration || 0);
    }, 0);
    const avgSeconds = totalExecutions > 0 ? totalSeconds / totalExecutions : 0;
    const avgDuration = `${Math.floor(avgSeconds / 60)}m ${Math.floor(avgSeconds % 60)}s`;
    
    return {
      totalExecutions,
      passRate: passRate.toFixed(1),
      avgDuration,
    };
  }, [filteredExecutionRuns]);
  
  // Handle project selection change
  const handleProjectChange = (projectId: string) => {
    console.log(`[ModuleDetails] Project selected: ${projectId}`);
    setSelectedProject(projectId);
    setSelectedModule(""); // Reset module selection
    setSelectedExecutionId(null); // Reset selected execution
    setSelectedDate("all"); // Reset date filter
    // Update URL
    if (projectId) {
      router.push(`/module-details?project=${projectId}`);
    }
  };

  // Handle module selection change
  const handleModuleChange = (moduleId: string) => {
    console.log(`[ModuleDetails] Module selected: ${moduleId}`);
    setSelectedModule(moduleId);
    setSelectedExecutionId(null); // Reset selected execution
    setSelectedDate("all"); // Reset date filter
    // Update URL
    if (selectedProject && moduleId) {
      router.push(`/module-details?project=${selectedProject}&module=${moduleId}`);
    }
  };
  
  // Handle defect modal open
  const handleLinkDefect = (scenarioId: string, scenarioName: string) => {
    setDefectModal({
      isOpen: true,
      scenarioId,
      scenarioName,
    });
    setDefectId("");
    setDefectError("");
  };
  
  // Handle defect submission
  const handleDefectSubmit = () => {
    if (!defectId.trim()) {
      setDefectError("Defect ID is required");
      return;
    }
    
    console.log(`[ModuleDetails] Linking defect ${defectId} to scenario ${defectModal.scenarioId}`);
    // TODO: Implement API call to link defect to scenario
    
    // Close modal on success
    setDefectModal({ isOpen: false, scenarioId: null, scenarioName: "" });
    setDefectId("");
    setDefectError("");
  };
  
  // Format duration from seconds to "Xm Ys" format
  const formatDuration = (seconds: number | null): string => {
    if (!seconds) return "0s";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    if (mins > 0) {
      return `${mins}m ${secs}s`;
    }
    return `${secs}s`;
  };
  
  // Format datetime to display format
  const formatDateTime = (isoString: string): string => {
    return isoString.replace('T', ' ').split('.')[0];
  };
  
  // Note: getStatusColor removed as it was unused
  
  const getStatusBgColor = (status: ExecutionStatus | ScenarioStatus) => {
    switch (status) {
      case "passed":
        return "bg-green-50";
      case "failed":
        return "bg-red-50";
      default:
        return "bg-gray-50";
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Module Details
          </h1>
          <button
            onClick={() => router.push('/projects')}
            style={{
              background: "#374151",
              borderRadius: "6px",
              padding: "5px 10px",
              fontSize: "12px",
              fontWeight: 500,
              color: "white",
              border: "none",
              cursor: "pointer",
              transition: "background 0.2s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "#111827";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "#374151";
            }}
          >
            ← Back to Projects
          </button>
        </div>

        {/* Cascading Dropdowns */}
        <div className="mb-6">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-12">
            {/* Project Dropdown - 6 cols */}
            <div className="md:col-span-6">
              <label className="mb-2 block text-sm font-medium text-foreground">
                Project
              </label>
              <select
                value={selectedProject}
                onChange={(e) => handleProjectChange(e.target.value)}
                disabled={loadingProjects}
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              >
                <option value="">
                  {loadingProjects ? "Loading projects..." : "Select Project..."}
                </option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
              {projectsError && (
                <p className="mt-2 text-sm text-red-600">{projectsError}</p>
              )}
              {!loadingProjects && projects.length === 0 && !projectsError && (
                <p className="mt-2 text-sm text-muted-foreground">No projects available</p>
              )}
            </div>

            {/* Module Dropdown - 6 cols (disabled until project selected) */}
            <div className="md:col-span-6">
              <label className="mb-2 block text-sm font-medium text-foreground">
                Module
              </label>
              <select
                value={selectedModule}
                onChange={(e) => handleModuleChange(e.target.value)}
                disabled={!selectedProject || loadingModules}
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              >
                <option value="">
                  {!selectedProject 
                    ? "Select a project first..." 
                    : loadingModules 
                    ? "Loading modules..." 
                    : "Select Module..."}
                </option>
                {modules.map((module) => (
                  <option key={module.id} value={module.id}>
                    {module.name}
                  </option>
                ))}
              </select>
              {modulesError && (
                <p className="mt-2 text-sm text-red-600">{modulesError}</p>
              )}
              {!loadingModules && selectedProject && modules.length === 0 && !modulesError && (
                <p className="mt-2 text-sm text-muted-foreground">No modules found for this project</p>
              )}
            </div>
          </div>
        </div>

        {/* Summary Cards - 3 cards */}
        {selectedModule && !loadingExecutions && (
          <div className="mb-6">
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              {/* Total Executions Card */}
              <div className="rounded-lg border border-border bg-card p-3 shadow-sm transition-all hover:shadow-md">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100">
                    <i className="fas fa-play-circle" style={{ color: '#6f42c1', fontSize: '16px' }} />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs font-medium text-muted-foreground">Total Executions</p>
                    <p className="text-lg font-bold text-foreground">{summaryMetrics.totalExecutions}</p>
                  </div>
                </div>
              </div>

              {/* Pass Rate Card */}
              <div className="rounded-lg border border-border bg-card p-3 shadow-sm transition-all hover:shadow-md">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100">
                    <i className="fas fa-chart-pie" style={{ color: '#28a745', fontSize: '16px' }} />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs font-medium text-muted-foreground">Pass Rate</p>
                    <p className="text-lg font-bold text-foreground">{summaryMetrics.passRate}%</p>
                  </div>
                </div>
              </div>

              {/* Avg Duration Card */}
              <div className="rounded-lg border border-border bg-card p-3 shadow-sm transition-all hover:shadow-md">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-orange-100">
                    <i className="fas fa-stopwatch" style={{ color: '#fd7e14', fontSize: '16px' }} />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs font-medium text-muted-foreground">Avg Duration</p>
                    <p className="text-lg font-bold text-foreground">{summaryMetrics.avgDuration}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Loading state for executions */}
        {selectedModule && loadingExecutions && (
          <div className="mb-6 text-center">
            <p className="text-muted-foreground">Loading executions...</p>
          </div>
        )}

        {/* Execution Date Filter */}
        {selectedModule && !loadingExecutions && executions.length > 0 && (
          <div className="mb-6">
            <div className="w-full md:w-64">
              <label className="mb-2 block text-sm font-medium text-foreground">
                Execution Date
              </label>
              <select
                value={selectedDate}
                onChange={(e) => {
                  setSelectedDate(e.target.value);
                  setSelectedExecutionId(null);
                }}
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="all">All Dates</option>
                {executionDates.slice(1).map((date) => (
                  <option key={date} value={date}>
                    {date}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}

        {/* Error state for executions */}
        {selectedModule && executionsError && (
          <div className="mb-6">
            <div className="rounded-lg border border-red-200 bg-red-50 p-4">
              <p className="text-sm text-red-600">{executionsError}</p>
            </div>
          </div>
        )}

        {/* Empty state for executions */}
        {selectedModule && !loadingExecutions && executions.length === 0 && !executionsError && (
          <div className="mb-6">
            <div className="rounded-lg border border-border bg-card p-8 text-center">
              <p className="text-muted-foreground">No executions found for this module</p>
            </div>
          </div>
        )}

        {/* Execution Runs Table */}
        {selectedModule && !loadingExecutions && filteredExecutionRuns.length > 0 && (
          <div className="mb-6">
            <div className="rounded-lg border border-border bg-card shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr style={{ backgroundColor: '#1e293b' }}>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-white">
                        Execution Date
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-white">
                        Passed
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-white">
                        Failed
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-white">
                        Total
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-white">
                        Duration
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-white">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredExecutionRuns.map((exec) => (
                      <tr
                        key={exec.id}
                        onClick={() => {
                          console.log(`[ModuleDetails] Execution selected: ${exec.id}`);
                          setSelectedExecutionId(exec.id);
                        }}
                        className={cn(
                          "cursor-pointer border-b border-border transition-colors",
                          getStatusBgColor(exec.status),
                          selectedExecutionId === exec.id && "ring-2 ring-primary"
                        )}
                      >
                        <td className="px-3 py-2 text-xs text-foreground">
                          {formatDateTime(exec.created_at)}
                        </td>
                        <td className="px-3 py-2 text-xs font-medium text-green-600">
                          {exec.passed_scenarios}
                        </td>
                        <td className="px-3 py-2 text-xs font-medium text-red-600">
                          {exec.failed_scenarios}
                        </td>
                        <td className="px-3 py-2 text-xs text-foreground">
                          {exec.total_scenarios}
                        </td>
                        <td className="px-3 py-2 text-xs text-foreground">
                          {formatDuration(exec.duration)}
                        </td>
                        <td className="px-3 py-2 text-xs">
                          <Badge variant={exec.status === "passed" ? "success" : exec.status === "failed" ? "error" : "default"}>
                            {exec.status.toUpperCase()}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Loading state for scenarios */}
        {selectedExecutionId && loadingScenarios && (
          <div className="mb-6">
            <h2 className="mb-4 text-xl font-semibold text-foreground">
              Scenarios
            </h2>
            <div className="text-center">
              <p className="text-muted-foreground">Loading scenarios...</p>
            </div>
          </div>
        )}

        {/* Error state for scenarios */}
        {selectedExecutionId && scenariosError && (
          <div className="mb-6">
            <h2 className="mb-4 text-xl font-semibold text-foreground">
              Scenarios
            </h2>
            <div className="rounded-lg border border-red-200 bg-red-50 p-4">
              <p className="text-sm text-red-600">{scenariosError}</p>
            </div>
          </div>
        )}

        {/* Empty state for scenarios */}
        {selectedExecutionId && !loadingScenarios && scenarios.length === 0 && !scenariosError && (
          <div className="mb-6">
            <h2 className="mb-4 text-xl font-semibold text-foreground">
              Scenarios
            </h2>
            <div className="rounded-lg border border-border bg-card p-8 text-center">
              <p className="text-muted-foreground">No scenarios found for this execution</p>
            </div>
          </div>
        )}

        {/* Scenarios Section (appears on row selection) */}
        {selectedExecutionId && !loadingScenarios && scenarios.length > 0 && (
          <div className="mb-6">
            <h2 className="mb-4 text-lg font-semibold text-foreground">
              Scenarios
            </h2>
            <div className="rounded-lg border border-border bg-card shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr style={{ backgroundColor: '#1e293b' }}>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-white">
                        Scenario
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-white">
                        Tags
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-white">
                        Duration
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-white">
                        Status
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-white">
                        Feature
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-white">
                        Error
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-white">
                        Stack Trace
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-white">
                        Defect
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {scenarios.map((scenario) => (
                      <tr
                        key={scenario.id}
                        className="border-b border-border transition-colors hover:bg-muted/50"
                      >
                        <td className="px-3 py-2 text-xs text-foreground">
                          {scenario.name}
                        </td>
                        <td className="px-3 py-2 text-xs text-muted-foreground">
                          {scenario.tags || "-"}
                        </td>
                        <td className="px-3 py-2 text-xs text-foreground">
                          {formatDuration(scenario.duration)}
                        </td>
                        <td className="px-3 py-2 text-xs">
                          <Badge variant={
                            scenario.status === "passed" ? "success" : 
                            scenario.status === "failed" ? "error" : 
                            "default"
                          }
                          style={{ fontSize: '10px', padding: '2px 6px' }}>
                            {scenario.status.toUpperCase()}
                          </Badge>
                        </td>
                        <td className="px-3 py-2 text-xs text-muted-foreground">
                          {scenario.feature || "-"}
                        </td>
                        <td className="px-3 py-2 text-xs text-red-600">
                          {scenario.error_message || "-"}
                        </td>
                        <td className="px-3 py-2 text-xs text-muted-foreground">
                          {scenario.stack_trace ? (
                            <div className="max-w-xs truncate" title={scenario.stack_trace}>
                              {scenario.stack_trace}
                            </div>
                          ) : (
                            "-"
                          )}
                        </td>
                        <td className="px-3 py-2 text-xs">
                          {scenario.status === "failed" ? (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleLinkDefect(scenario.id, scenario.name)}
                              style={{ fontSize: '11px', padding: '4px 8px' }}
                            >
                              Link Defect
                            </Button>
                          ) : (
                            <span className="text-muted-foreground">-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Defect Modal */}
        {defectModal.isOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="w-full max-w-md rounded-lg bg-card p-6 shadow-xl">
              <h3 className="mb-4 text-lg font-semibold text-foreground">
                Link Defect
              </h3>
              <p className="mb-4 text-sm text-muted-foreground">
                Scenario: {defectModal.scenarioName}
              </p>
              <div className="mb-4">
                <label className="mb-2 block text-sm font-medium text-foreground">
                  Defect ID
                </label>
                <input
                  type="text"
                  value={defectId}
                  onChange={(e) => {
                    setDefectId(e.target.value);
                    setDefectError("");
                  }}
                  placeholder="Enter Defect ID..."
                  className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
                {defectError && (
                  <p className="mt-2 text-sm text-red-600">
                    {defectError}
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="default"
                  onClick={handleDefectSubmit}
                  className="flex-1"
                >
                  OK
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setDefectModal({ isOpen: false, scenarioId: null, scenarioName: "" });
                    setDefectId("");
                    setDefectError("");
                  }}
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
