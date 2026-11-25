"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { executionsAPI, projectsAPI } from "@/lib/api";
import type { Execution } from "@/lib/types";
import { PageHeader, PageContainer } from "@/components/molecules";

/**
 * Execution Summary Page
 * 
 * Displays execution summary for a specific project with:
 * - Back button to navigate to projects
 * - Page title with project name
 * - 3 summary cards (Pass Rate, Total Test Cases, Total Duration)
 * - Filter row with Date, Module, and Status dropdowns
 * - Execution table with module-wise test results (latest execution per module per day)
 * - Actions column with View Module button
 * - Footer with last updated timestamp
 */

// Interface for transformed execution data for UI
interface ExecutionRowData {
  id: string;
  moduleId: string;
  moduleName: string;
  passed: number;
  failed: number;
  total: number;
  duration: string;
  status: "pass" | "fail" | "warning";
  createdAt: string;
}

// Format duration from seconds to readable format - moved outside component
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

// Format error message - handle arrays, objects, strings
const formatErrorMessage = (error: any): string => {
  if (!error) return "An unknown error occurred";
  
  if (typeof error === 'string') return error;
  
  if (Array.isArray(error)) {
    return error.map(e => 
      typeof e === 'object' ? e.msg || e.message || JSON.stringify(e) : String(e)
    ).join(', ');
  }
  
  if (typeof error === 'object') {
    return error.message || error.msg || error.detail || JSON.stringify(error);
  }
  
  return String(error);
};

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
        
        // Backend has a max page size of 100, so fetch in batches if needed
        const response = await executionsAPI.getProjectExecutions(projectId, {
          page: 1,
          size: 100, // Max allowed by backend validation
        });
        
        console.log("Executions API response:", response);
        setExecutions(response.executions || []);
      } catch (err: any) {
        console.error("Error fetching executions:", err);
        // Format error properly - handle arrays, objects, strings
        const errorMessage = formatErrorMessage(err.detail || err);
        setError(errorMessage);
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

  // Navigate to module details page
  const handleViewModule = (moduleId: string, moduleName: string) => {
    router.push(`/module-details?project=${projectId}&projectName=${encodeURIComponent(projectName)}&module=${moduleId}&moduleName=${encodeURIComponent(moduleName)}`);
  };

  // Get latest execution per module per day
  const latestExecutionsPerModulePerDay = React.useMemo(() => {
    // Group executions by date and module
    const grouped = new Map<string, Execution>();

    executions.forEach((exec) => {
      const executionDate = new Date(exec.created_at).toISOString().split('T')[0];
      const key = `${executionDate}_${exec.module_id}`;
      
      const existing = grouped.get(key);
      if (!existing || new Date(exec.created_at) > new Date(existing.created_at)) {
        grouped.set(key, exec);
      }
    });

    return Array.from(grouped.values());
  }, [executions]);

  console.log("Latest executions per module per day:", latestExecutionsPerModulePerDay);

  // Calculate summary data from latest executions only
  const summaryData = React.useMemo(() => {
    if (latestExecutionsPerModulePerDay.length === 0) {
      return {
        passRate: "0%",
        totalTests: "0",
        totalDuration: "0s",
      };
    }

    const totalTests = latestExecutionsPerModulePerDay.reduce((sum, exec) => sum + exec.total_scenarios, 0);
    const totalPassed = latestExecutionsPerModulePerDay.reduce((sum, exec) => sum + exec.passed_scenarios, 0);
    const totalDuration = latestExecutionsPerModulePerDay.reduce((sum, exec) => sum + (exec.duration || 0), 0);
    const passRate = totalTests > 0 ? ((totalPassed / totalTests) * 100).toFixed(1) : "0";

    console.log("Summary calculations:", { totalTests, totalPassed, totalDuration, passRate });

    return {
      passRate: `${passRate}%`,
      totalTests: totalTests.toLocaleString(),
      totalDuration: formatDuration(totalDuration),
    };
  }, [latestExecutionsPerModulePerDay]);

  // Get latest execution date for preselection
  const latestExecutionDate = React.useMemo(() => {
    if (latestExecutionsPerModulePerDay.length === 0) return "";
    
    const sortedExecutions = [...latestExecutionsPerModulePerDay].sort((a, b) => 
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
    
    const latestDate = new Date(sortedExecutions[0].created_at);
    return latestDate.toISOString().split('T')[0]; // Format as YYYY-MM-DD
  }, [latestExecutionsPerModulePerDay]);

  // Auto-select latest execution date when executions load
  React.useEffect(() => {
    if (latestExecutionDate && !dateFilter) {
      setDateFilter(latestExecutionDate);
    }
  }, [latestExecutionDate, dateFilter]);

  // Transform executions to row data format (using latest executions only)
  const executionData: ExecutionRowData[] = React.useMemo(() => {
    return latestExecutionsPerModulePerDay.map((exec) => {
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
        moduleId: exec.module_id,
        moduleName: exec.module_name || "Unknown Module",
        passed,
        failed,
        total,
        duration: formatDuration(exec.duration),
        status,
        createdAt: exec.created_at,
      };
    });
  }, [latestExecutionsPerModulePerDay]);

  console.log("Transformed execution data:", executionData);

  // Apply filters to execution data
  const filteredExecutionData = React.useMemo(() => {
    return executionData.filter((row) => {
      // Status filter
      if (statusFilter && row.status !== statusFilter) {
        return false;
      }
      
      // Date filter
      if (dateFilter) {
        const executionDate = new Date(row.createdAt).toISOString().split('T')[0];
        if (executionDate !== dateFilter) {
          return false;
        }
      }
      
      return true;
    });
  }, [executionData, dateFilter, statusFilter]);

  // Get current timestamp
  const lastUpdated = new Date().toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

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
    <PageContainer>
      <div className="flex h-full flex-col">
        {/* Header with Title and Back Button */}
        <PageHeader
          title={`Execution Summary${projectName !== "Project" ? `: ${projectName}` : ""}`}
        />

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

        {/* Latest Execution Indicator */}
        {projectId && !loading && latestExecutionsPerModulePerDay.length > 0 && (
          <div style={{
            background: "#eff6ff",
            border: "1px solid #bfdbfe",
            borderRadius: "6px",
            padding: "10px 14px",
            marginBottom: "16px",
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            maxWidth: "fit-content",
          }}>
            <i className="fas fa-info-circle" style={{ color: "#3b82f6", fontSize: "14px" }} />
            <span style={{ fontSize: "13px", color: "#1e40af", fontWeight: 500 }}>
              Showing latest execution per module per day
            </span>
          </div>
        )}

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
              className="fas fa-vials"
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
                  color: "#fd7e14",
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
              className="fas fa-stopwatch"
              style={{ fontSize: "18px", color: "#fd7e14" }}
            ></i>
          </div>
        </div>

        {/* Filter Row - Date and Status */}
        <div
          style={{
            background: "white",
            border: "1px solid #e5e7eb",
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
                    marginBottom: "4px",
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
        {projectId && !loading && !error && filteredExecutionData.length === 0 && (
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
              No Execution Data Found
            </div>
            <div style={{ fontSize: "14px", color: "#6c757d" }}>
              {dateFilter || statusFilter
                ? "Try adjusting your filters to see more results."
                : "No executions have been run for this project yet."}
            </div>
          </div>
        )}

        {/* Execution Table */}
        {projectId && !loading && !error && filteredExecutionData.length > 0 && (
          <div
            style={{
              background: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
              overflow: "hidden",
              marginBottom: "20px",
            }}
          >
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ backgroundColor: "#1e293b" }}>
                    <th
                      style={{
                        padding: "10px 12px",
                        textAlign: "left",
                        color: "white",
                        fontSize: "12px",
                        fontWeight: "bold",
                      }}
                    >
                      Module
                    </th>
                    <th
                      style={{
                        padding: "10px 12px",
                        textAlign: "center",
                        color: "white",
                        fontSize: "12px",
                        fontWeight: "bold",
                      }}
                    >
                      Passed
                    </th>
                    <th
                      style={{
                        padding: "10px 12px",
                        textAlign: "center",
                        color: "white",
                        fontSize: "12px",
                        fontWeight: "bold",
                      }}
                    >
                      Failed
                    </th>
                    <th
                      style={{
                        padding: "10px 12px",
                        textAlign: "center",
                        color: "white",
                        fontSize: "12px",
                        fontWeight: "bold",
                      }}
                    >
                      Total
                    </th>
                    <th
                      style={{
                        padding: "10px 12px",
                        textAlign: "center",
                        color: "white",
                        fontSize: "12px",
                        fontWeight: "bold",
                      }}
                    >
                      Duration
                    </th>
                    <th
                      style={{
                        padding: "10px 12px",
                        textAlign: "center",
                        color: "white",
                        fontSize: "12px",
                        fontWeight: "bold",
                      }}
                    >
                      Status
                    </th>
                    <th
                      style={{
                        padding: "10px 12px",
                        textAlign: "center",
                        color: "white",
                        fontSize: "12px",
                        fontWeight: "bold",
                      }}
                    >
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredExecutionData.map((row) => (
                    <tr
                      key={row.id}
                      style={{
                        backgroundColor: getRowColor(row.status),
                        borderBottom: "1px solid #e5e7eb",
                        transition: "background-color 0.2s ease",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.opacity = "0.8";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.opacity = "1";
                      }}
                    >
                      <td
                        style={{
                          padding: "10px 12px",
                          fontSize: "13px",
                          fontWeight: 500,
                          color: "#1f2937",
                        }}
                      >
                        {row.moduleName}
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "center",
                          fontSize: "13px",
                          fontWeight: "bold",
                          color: "#28a745",
                        }}
                      >
                        {row.passed}
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "center",
                          fontSize: "13px",
                          fontWeight: "bold",
                          color: "#dc3545",
                        }}
                      >
                        {row.failed}
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "center",
                          fontSize: "13px",
                          color: "#6c757d",
                        }}
                      >
                        {row.total}
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "center",
                          fontSize: "13px",
                          color: "#6c757d",
                        }}
                      >
                        {row.duration}
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "center",
                          fontSize: "16px",
                        }}
                      >
                        {getStatusIcon(row.status)}
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "center",
                        }}
                      >
                        <button
                          onClick={() => handleViewModule(row.moduleId, row.moduleName)}
                          style={{
                            padding: "4px 8px",
                            fontSize: "11px",
                            fontWeight: 500,
                            color: "white",
                            background: "#495057",
                            border: "none",
                            borderRadius: "4px",
                            cursor: "pointer",
                            transition: "background 0.2s ease",
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = "#343a40";
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = "#495057";
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
          </div>
        )}

        {/* Footer - Last Updated */}
        {projectId && !loading && !error && filteredExecutionData.length > 0 && (
          <div
            style={{
              padding: "12px",
              textAlign: "center",
              fontSize: "11px",
              color: "#6c757d",
            }}
          >
            Last updated: {lastUpdated}
          </div>
        )}
      </div>
    </PageContainer>
  );
}
