"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { executionsAPI, projectsAPI } from "@/lib/api";
import type { Execution } from "@/lib/types";

/**
 * Execution Summary Page
 * 
 * Displays execution summary for a specific project with:
 * - Back button to navigate to projects
 * - Page title with project name
 * - 3 summary cards (Pass Rate, Total Test Cases, Total Duration)
 * - Filter row with Date, Module, and Status dropdowns
 * - Execution table with module-wise test results
 * - Footer with last updated timestamp
 */

// Interface for transformed execution data for UI
interface ExecutionRowData {
  id: string;
  moduleName: string;
  passed: number;
  failed: number;
  total: number;
  duration: string;
  status: "pass" | "fail" | "warning";
}

export default function ExecutionSummaryPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const projectIdParam = searchParams.get("project") || "";
  const projectNameParam = searchParams.get("projectName") || "";

  // State for API data
  const [projects, setProjects] = React.useState<any[]>([]);
  const [executions, setExecutions] = React.useState<Execution[]>([]);
  const [projectId, setProjectId] = React.useState<string>(projectIdParam);
  const [projectName, setProjectName] = React.useState<string>(projectNameParam || "Project");
  const [loading, setLoading] = React.useState(true);
  const [loadingProjects, setLoadingProjects] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // State for filters
  const [dateFilter, setDateFilter] = React.useState<string>(""); // Date in YYYY-MM-DD format
  const [statusFilter, setStatusFilter] = React.useState("");

  // Fetch all projects on mount
  React.useEffect(() => {
    const fetchProjects = async () => {
      setLoadingProjects(true);
      try {
        console.log("Fetching all projects...");
        const projectsList = await projectsAPI.getProjects();
        console.log("Projects fetched:", projectsList);
        setProjects(projectsList);
        
        // If no project in URL, don't auto-select
        // User must choose from dropdown
      } catch (err: any) {
        console.error("Error fetching projects:", err);
      } finally {
        setLoadingProjects(false);
      }
    };

    fetchProjects();
  }, []);

  // Fetch project details if project ID is in URL params
  React.useEffect(() => {
    const fetchProjectDetails = async () => {
      if (!projectIdParam) {
        return; // No project in URL, wait for user selection
      }

      try {
        console.log("Fetching project details for ID:", projectIdParam);
        const project = await projectsAPI.getProject(projectIdParam);
        console.log("Project details fetched:", project);
        setProjectName(project.name);
        setProjectId(projectIdParam);
      } catch (err: any) {
        console.error("Error fetching project details:", err);
        setProjectName("Project");
      }
    };

    fetchProjectDetails();
  }, [projectIdParam]);

  // Fetch executions from backend when project is selected
  React.useEffect(() => {
    const fetchExecutions = async () => {
      if (!projectId) {
        console.log("No project selected yet");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        console.log("Fetching executions for project:", projectId);
        
        const response = await executionsAPI.getProjectExecutions(projectId, {
          page: 1,
          size: 100,
        });
        
        console.log("Executions API response:", response);
        setExecutions(response.executions || []);
      } catch (err: any) {
        console.error("Error fetching executions:", err);
        setError(err.detail || "Failed to load execution data");
      } finally {
        setLoading(false);
      }
    };

    fetchExecutions();
  }, [projectId]);

  // Handle project selection from dropdown
  const handleProjectChange = (selectedProjectId: string) => {
    setProjectId(selectedProjectId);
    const selectedProject = projects.find(p => p.id === selectedProjectId);
    if (selectedProject) {
      setProjectName(selectedProject.name);
      // Update URL with selected project
      router.push(`/execution-summary?project=${selectedProjectId}&projectName=${encodeURIComponent(selectedProject.name)}`);
    }
  };

  // Format duration from seconds to readable format
  const formatDuration = (seconds: number | null): string => {
    if (!seconds) return "0s";
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    }
    return `${secs}s`;
  };

  // Calculate summary data from executions
  const summaryData = React.useMemo(() => {
    if (executions.length === 0) {
      return {
        passRate: "0%",
        totalTests: "0",
        totalDuration: "0s",
      };
    }

    const totalTests = executions.reduce((sum, exec) => sum + exec.total_scenarios, 0);
    const totalPassed = executions.reduce((sum, exec) => sum + exec.passed_scenarios, 0);
    const totalDuration = executions.reduce((sum, exec) => sum + (exec.duration || 0), 0);
    const passRate = totalTests > 0 ? ((totalPassed / totalTests) * 100).toFixed(1) : "0";

    console.log("Summary calculations:", { totalTests, totalPassed, totalDuration, passRate });

    return {
      passRate: `${passRate}%`,
      totalTests: totalTests.toLocaleString(),
      totalDuration: formatDuration(totalDuration),
    };
  }, [executions]);

  // Get latest execution date for preselection
  const latestExecutionDate = React.useMemo(() => {
    if (executions.length === 0) return "";
    
    const sortedExecutions = [...executions].sort((a, b) => 
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
    
    const latestDate = new Date(sortedExecutions[0].created_at);
    return latestDate.toISOString().split('T')[0]; // Format as YYYY-MM-DD
  }, [executions]);

  // Auto-select latest execution date when executions load
  React.useEffect(() => {
    if (latestExecutionDate && !dateFilter) {
      setDateFilter(latestExecutionDate);
    }
  }, [latestExecutionDate]);

  // Transform executions to row data format
  const executionData: ExecutionRowData[] = React.useMemo(() => {
    return executions.map((exec) => {
      const total = exec.total_scenarios;
      const passed = exec.passed_scenarios;
      const failed = exec.failed_scenarios;
      
      // Determine status based on pass rate
      let status: "pass" | "fail" | "warning";
      if (failed === 0) {
        status = "pass";
      } else if (failed > passed) {
        status = "fail";
      } else {
        status = "warning";
      }

      return {
        id: exec.id,
        moduleName: exec.module_name || "Unknown Module",
        passed,
        failed,
        total,
        duration: formatDuration(exec.duration),
        status,
      };
    });
  }, [executions]);

  console.log("Transformed execution data:", executionData);

  // Apply filters to execution data
  const filteredExecutionData = React.useMemo(() => {
    return executionData.filter((row) => {
      // Status filter
      if (statusFilter && row.status !== statusFilter) {
        return false;
      }
      
      // Date filter - filter by execution created_at date
      if (dateFilter) {
        const execution = executions.find(e => e.id === row.id);
        if (execution) {
          const executionDate = new Date(execution.created_at).toISOString().split('T')[0];
          if (executionDate !== dateFilter) {
            return false;
          }
        }
      }
      
      return true;
    });
  }, [executionData, executions, dateFilter, statusFilter]);

  // Get current timestamp
  const lastUpdated = new Date().toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  // Handle back button click
  const handleBackClick = () => {
    router.push("/projects");
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "pass":
        return "✅";
      case "fail":
        return "❌";
      case "warning":
        return "⚠️";
      default:
        return "⬜";
    }
  };

  // Get row background color based on status
  const getRowColor = (status: string) => {
    switch (status) {
      case "pass":
        return "#e6f7ec";
      case "fail":
        return "#fdecea";
      case "warning":
        return "#fffbea";
      default:
        return "#ffffff";
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="flex h-full flex-col">
        {/* Header with Title and Back Button */}
        <div className="mb-6 flex items-center justify-between">
          <h1
            style={{
              color: "#1b4332",
              fontWeight: "bold",
              fontSize: "24px",
              margin: 0,
            }}
          >
            Execution Summary{projectName !== "Project" ? `: ${projectName}` : ""}
          </h1>
          <button
            onClick={handleBackClick}
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

        {/* Project Dropdown - Always visible */}
        <div className="mb-6">
          <label
            style={{
              display: "block",
              marginBottom: "6px",
              fontSize: "12px",
              fontWeight: 500,
              color: "#374151",
            }}
          >
            Select Project
          </label>
          <select
            value={projectId}
            onChange={(e) => handleProjectChange(e.target.value)}
            disabled={loadingProjects}
            style={{
              width: "100%",
              maxWidth: "400px",
              padding: "8px 12px",
              borderRadius: "6px",
              border: "1px solid #d1d5db",
              background: loadingProjects ? "#f1f5f9" : "white",
              fontSize: "14px",
              cursor: loadingProjects ? "not-allowed" : "pointer",
              color: loadingProjects ? "#94a3b8" : "#1f2937",
            }}
          >
            <option value="">
              {loadingProjects ? "Loading projects..." : "Select a project..."}
            </option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </div>

        {/* Summary Cards */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: "15px",
            marginBottom: "20px",
          }}
        >
          {/* Card 1: Overall Pass Rate */}
          <div
            style={{
              background: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
              padding: "12px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div>
              <div
                style={{
                  fontSize: "22px",
                  fontWeight: "bold",
                  color: "#1b4332",
                  marginBottom: "4px",
                }}
              >
                {summaryData.passRate}
              </div>
              <div style={{ fontSize: "12px", color: "#6c757d" }}>
                Overall Pass Rate
              </div>
            </div>
            <i
              className="fas fa-chart-line"
              style={{ fontSize: "18px", color: "#28a745" }}
            ></i>
          </div>

          {/* Card 2: Total Test Cases */}
          <div
            style={{
              background: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
              padding: "12px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div>
              <div
                style={{
                  fontSize: "22px",
                  fontWeight: "bold",
                  color: "#0d6efd",
                  marginBottom: "4px",
                }}
              >
                {summaryData.totalTests}
              </div>
              <div style={{ fontSize: "12px", color: "#6c757d" }}>
                Total Test Cases
              </div>
            </div>
            <i
              className="fas fa-flask"
              style={{ fontSize: "18px", color: "#17a2b8" }}
            ></i>
          </div>

          {/* Card 3: Total Duration */}
          <div
            style={{
              background: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
              padding: "12px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div>
              <div
                style={{
                  fontSize: "22px",
                  fontWeight: "bold",
                  color: "#10b981",
                  marginBottom: "4px",
                }}
              >
                {summaryData.totalDuration}
              </div>
              <div style={{ fontSize: "12px", color: "#6c757d" }}>
                Total Duration
              </div>
            </div>
            <i
              className="fas fa-clock"
              style={{ fontSize: "18px", color: "#6f42c1" }}
            ></i>
          </div>
        </div>

        {/* Filter Row */}
        <div
          style={{
            background: "#f1f5f9",
            padding: "12px",
            borderRadius: "8px",
            marginBottom: "18px",
            display: "grid",
            gridTemplateColumns: "repeat(2, 1fr)",
            gap: "12px",
          }}
        >
          {/* Date Filter - Calendar Picker */}
          <div>
            <label
              style={{
                display: "block",
                marginBottom: "6px",
                fontSize: "12px",
                fontWeight: 500,
                color: "#374151",
              }}
            >
              Execution Date
            </label>
            <input
              type="date"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              style={{
                width: "100%",
                padding: "6px 10px",
                borderRadius: "6px",
                border: "1px solid #d1d5db",
                background: "white",
                fontSize: "12px",
                cursor: "pointer",
              }}
            />
          </div>

          {/* Status Filter */}
          <div>
            <label
              style={{
                display: "block",
                marginBottom: "6px",
                fontSize: "12px",
                fontWeight: 500,
                color: "#374151",
              }}
            >
              Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{
                width: "100%",
                padding: "6px 10px",
                borderRadius: "6px",
                border: "1px solid #d1d5db",
                background: "white",
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              <option value="">All Status</option>
              <option value="pass">✅ Pass</option>
              <option value="fail">❌ Fail</option>
              <option value="warning">⚠️ Warning</option>
            </select>
          </div>
        </div>

        {/* Empty State - No Project Selected */}
        {!projectId && !loading && (
          <div
            style={{
              background: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
              padding: "60px 20px",
              textAlign: "center",
              marginBottom: "20px",
            }}
          >
            <div
              style={{
                fontSize: "48px",
                color: "#6c757d",
                marginBottom: "20px",
              }}
            >
              <i className="fas fa-project-diagram"></i>
            </div>
            <div
              style={{
                fontSize: "18px",
                fontWeight: "bold",
                color: "#374151",
                marginBottom: "10px",
              }}
            >
              No Project Selected
            </div>
            <div style={{ fontSize: "14px", color: "#6c757d" }}>
              Please select a project from the dropdown above to view execution summary.
            </div>
          </div>
        )}

        {/* Loading State */}
        {projectId && loading && (
          <div
            style={{
              background: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
              padding: "60px 20px",
              textAlign: "center",
              marginBottom: "20px",
            }}
          >
            <div
              style={{
                fontSize: "48px",
                color: "#0d6efd",
                marginBottom: "20px",
              }}
            >
              <i className="fas fa-spinner fa-spin"></i>
            </div>
            <div style={{ fontSize: "18px", color: "#6c757d" }}>
              Loading execution data...
            </div>
          </div>
        )}

        {/* Error State */}
        {projectId && error && !loading && (
          <div
            style={{
              background: "#fdecea",
              border: "1px solid #f5c6cb",
              borderRadius: "8px",
              padding: "20px",
              marginBottom: "20px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <i
                className="fas fa-exclamation-triangle"
                style={{ fontSize: "24px", color: "#dc3545" }}
              ></i>
              <div>
                <div
                  style={{
                    fontSize: "16px",
                    fontWeight: "bold",
                    color: "#dc3545",
                    marginBottom: "5px",
                  }}
                >
                  Error Loading Data
                </div>
                <div style={{ fontSize: "14px", color: "#6c757d" }}>
                  {error}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Empty State - No Executions */}
        {projectId && !loading && !error && executionData.length === 0 && (
          <div
            style={{
              background: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
              padding: "60px 20px",
              textAlign: "center",
              marginBottom: "20px",
            }}
          >
            <div
              style={{
                fontSize: "48px",
                color: "#6c757d",
                marginBottom: "20px",
              }}
            >
              <i className="fas fa-inbox"></i>
            </div>
            <div
              style={{
                fontSize: "18px",
                fontWeight: "bold",
                color: "#374151",
                marginBottom: "10px",
              }}
            >
              No Executions Found
            </div>
            <div style={{ fontSize: "14px", color: "#6c757d" }}>
              There are no test executions for this project yet.
            </div>
          </div>
        )}

        {/* Execution Table */}
        {projectId && !loading && !error && executionData.length > 0 && (
          <div
            style={{
              background: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
              overflow: "hidden",
              marginBottom: "20px",
            }}
          >
            {filteredExecutionData.length === 0 ? (
              <div
                style={{
                  padding: "60px 20px",
                  textAlign: "center",
                }}
              >
                <div
                  style={{
                    fontSize: "48px",
                    color: "#6c757d",
                    marginBottom: "20px",
                  }}
                >
                  <i className="fas fa-filter"></i>
                </div>
                <div
                  style={{
                    fontSize: "18px",
                    fontWeight: "bold",
                    color: "#374151",
                    marginBottom: "10px",
                  }}
                >
                  No Results Found
                </div>
                <div style={{ fontSize: "14px", color: "#6c757d" }}>
                  No executions match the selected filters. Try adjusting your filter criteria.
                </div>
              </div>
            ) : (
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  {/* Table Header */}
                  <thead>
                    <tr
                      style={{
                        background: "#1e293b",
                        color: "white",
                      }}
                    >
                      <th
                        style={{
                          padding: "8px 12px",
                          textAlign: "center",
                          fontWeight: "bold",
                          fontSize: "12px",
                        }}
                      >
                        Module Name
                      </th>
                      <th
                        style={{
                          padding: "8px 12px",
                          textAlign: "center",
                          fontWeight: "bold",
                          fontSize: "12px",
                        }}
                      >
                        Passed
                      </th>
                      <th
                        style={{
                          padding: "8px 12px",
                          textAlign: "center",
                          fontWeight: "bold",
                          fontSize: "12px",
                        }}
                      >
                        Failed
                      </th>
                      <th
                        style={{
                          padding: "8px 12px",
                          textAlign: "center",
                          fontWeight: "bold",
                          fontSize: "12px",
                        }}
                      >
                        Total
                      </th>
                      <th
                        style={{
                          padding: "8px 12px",
                          textAlign: "center",
                          fontWeight: "bold",
                          fontSize: "12px",
                        }}
                      >
                        Duration
                      </th>
                      <th
                        style={{
                          padding: "8px 12px",
                          textAlign: "center",
                          fontWeight: "bold",
                          fontSize: "12px",
                        }}
                      >
                        Status
                      </th>
                      <th
                        style={{
                          padding: "8px 12px",
                          textAlign: "center",
                          fontWeight: "bold",
                          fontSize: "12px",
                        }}
                      >
                        Actions
                      </th>
                    </tr>
                  </thead>

                  {/* Table Body */}
                  <tbody>
                    {filteredExecutionData.map((row) => (
                      <tr
                        key={row.id}
                        style={{
                          background: getRowColor(row.status),
                          transition: "background 0.2s ease",
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = "#e2e8f0";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = getRowColor(row.status);
                        }}
                      >
                      <td
                        style={{
                          padding: "8px 12px",
                          textAlign: "center",
                          fontWeight: "bold",
                          fontSize: "12px",
                        }}
                      >
                        {row.moduleName}
                      </td>
                      <td
                        style={{
                          padding: "8px 12px",
                          textAlign: "center",
                          fontSize: "12px",
                          color: "#28a745",
                          fontWeight: 500,
                        }}
                      >
                        {row.passed}
                      </td>
                      <td
                        style={{
                          padding: "8px 12px",
                          textAlign: "center",
                          fontSize: "12px",
                          color: "#dc3545",
                          fontWeight: 500,
                        }}
                      >
                        {row.failed}
                      </td>
                      <td
                        style={{
                          padding: "8px 12px",
                          textAlign: "center",
                          fontSize: "12px",
                        }}
                      >
                        {row.total}
                      </td>
                      <td
                        style={{
                          padding: "8px 12px",
                          textAlign: "center",
                          fontSize: "12px",
                        }}
                      >
                        {row.duration}
                      </td>
                      <td
                        style={{
                          padding: "8px 12px",
                          textAlign: "center",
                          fontSize: "14px",
                        }}
                      >
                        {getStatusIcon(row.status)}
                      </td>
                      <td
                        style={{
                          padding: "8px 12px",
                          textAlign: "center",
                        }}
                      >
                        <button
                          style={{
                            background: "#0d6efd",
                            color: "white",
                            border: "none",
                            borderRadius: "4px",
                            padding: "5px 10px",
                            fontSize: "11px",
                            cursor: "pointer",
                            transition: "background 0.2s ease",
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = "#0b5ed7";
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = "#0d6efd";
                          }}
                          onClick={() => {
                            // Find the execution to get module_id
                            const execution = executions.find(e => e.id === row.id);
                            if (execution && execution.module_id) {
                              console.log("View Module:", row.moduleName, "Module ID:", execution.module_id);
                              // Navigate to module-details with project and module preselected
                              router.push(
                                `/module-details?project=${projectId}&module=${execution.module_id}`
                              );
                            } else {
                              console.warn("Module ID not found for execution:", row.id);
                              // Navigate without module preselection if module_id is missing
                              router.push(`/module-details?project=${projectId}`);
                            }
                          }}
                        >
                          View Module
                        </button>
                      </td>
                    </tr>
                  ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div
          style={{
            textAlign: "center",
            fontSize: "0.9rem",
            color: "#6c757d",
            marginTop: "20px",
            paddingTop: "20px",
            borderTop: "1px solid #e5e7eb",
          }}
        >
          <i
            className="fas fa-sync-alt"
            style={{ marginRight: "8px" }}
          ></i>
          Last updated: {lastUpdated}
        </div>
      </div>
    </div>
  );
}
