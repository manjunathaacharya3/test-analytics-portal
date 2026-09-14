"use client";

import * as React from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { AlertCircle } from "lucide-react";
import { DashboardLayout } from "@/components/templates/DashboardLayout";
import { ExecutionTable } from "@/components/organisms/ExecutionTable";
import { SearchBar } from "@/components/molecules/SearchBar";
import {
  FilterBar,
  type FilterGroup,
  type Filters,
} from "@/components/molecules/FilterBar";
import { SummaryCards } from "@/components/molecules/SummaryCards";
import { Button } from "@/components/ui/button";
import { CardSkeleton } from "@/components/ui/loading-skeleton";
import { useProjectExecutions } from "@/hooks/useExecutions";
import { useProjectModules } from "@/hooks/useProjects";
import type { ExecutionFilters } from "@/lib/types";

/**
 * Execution Summary Page
 * 
 * Displays all executions for a project with advanced filtering and table.
 * Features:
 * - URL-based filter state (shareable links)
 * - Server-side pagination
 * - Advanced filters (date range, status, module)
 * - Export to CSV functionality
 * - Click row to navigate to execution detail
 * - Real-time data updates with TanStack Query
 */
export default function ExecutionSummaryPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const projectId = params.id as string;

  // Initialize filters from URL params
  const [searchQuery, setSearchQuery] = React.useState(
    searchParams.get("search") || ""
  );
  const [filters, setFilters] = React.useState<Filters>(() => ({
    dateRange: {
      from: searchParams.get("from")
        ? new Date(searchParams.get("from")!)
        : null,
      to: searchParams.get("to") ? new Date(searchParams.get("to")!) : null,
    },
    status: searchParams.get("status")?.split(",").filter(Boolean) || [],
    module: searchParams.get("module") || "",
  }));

  // Pagination state
  const [page, setPage] = React.useState(
    parseInt(searchParams.get("page") || "1", 10)
  );
  const [pageSize, setPageSize] = React.useState(
    parseInt(searchParams.get("size") || "20", 10)
  );

  // Build API filters from UI state
  const apiFilters: ExecutionFilters = React.useMemo(() => {
    const result: ExecutionFilters = {
      page,
      size: pageSize,
    };

    // Add status filter
    if (filters.status && filters.status.length > 0) {
      result.status = filters.status.join(",");
    }

    // Add module filter
    if (filters.module) {
      result.module_id = filters.module;
    }

    // Add date range filters
    if (filters.dateRange?.from) {
      result.date_from = filters.dateRange.from.toISOString().split("T")[0];
    }
    if (filters.dateRange?.to) {
      result.date_to = filters.dateRange.to.toISOString().split("T")[0];
    }

    return result;
  }, [filters, page, pageSize]);

  // Fetch executions with TanStack Query
  const {
    data: executionsResponse,
    isLoading: executionsLoading,
    error: executionsError,
    refetch: refetchExecutions,
  } = useProjectExecutions(projectId, apiFilters);

  // Fetch modules for filter dropdown
  const { data: modules, isLoading: modulesLoading } =
    useProjectModules(projectId);

  // Update URL when filters change
  React.useEffect(() => {
    const params = new URLSearchParams();

    if (searchQuery) params.set("search", searchQuery);
    if (filters.status && filters.status.length > 0) {
      params.set("status", filters.status.join(","));
    }
    if (filters.module) params.set("module", filters.module);
    if (filters.dateRange?.from) {
      params.set("from", filters.dateRange.from.toISOString().split("T")[0]);
    }
    if (filters.dateRange?.to) {
      params.set("to", filters.dateRange.to.toISOString().split("T")[0]);
    }
    if (page > 1) params.set("page", page.toString());
    if (pageSize !== 20) params.set("size", pageSize.toString());

    const queryString = params.toString();
    const newUrl = queryString
      ? `/projects/${projectId}/executions?${queryString}`
      : `/projects/${projectId}/executions`;

    router.replace(newUrl, { scroll: false });
  }, [searchQuery, filters, page, pageSize, projectId, router]);

  // Client-side search filtering (on already fetched data)
  const filteredExecutions = React.useMemo(() => {
    if (!executionsResponse?.executions) return [];

    return executionsResponse.executions.filter((execution) => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchesFileName = execution.file_name.toLowerCase().includes(query);
        const matchesModuleName = execution.module_name
          ?.toLowerCase()
          .includes(query);
        const matchesUploadedBy = execution.uploaded_by
          .toLowerCase()
          .includes(query);

        if (!matchesFileName && !matchesModuleName && !matchesUploadedBy) {
          return false;
        }
      }

      return true;
    });
  }, [executionsResponse, searchQuery]);

  // Calculate summary metrics
  const summaryMetrics = React.useMemo(() => {
    if (!filteredExecutions || filteredExecutions.length === 0) {
      return {
        totalExecutions: 0,
        totalTests: 0,
        averagePassRate: 0,
        failedExecutions: 0,
      };
    }

    const totalExecutions = filteredExecutions.length;
    const totalTests = filteredExecutions.reduce(
      (sum, exec) => sum + exec.total_scenarios,
      0
    );
    const averagePassRate =
      filteredExecutions.reduce((sum, exec) => sum + exec.pass_rate, 0) /
      totalExecutions;
    const failedExecutions = filteredExecutions.filter(
      (exec) => exec.status === "failed"
    ).length;

    return {
      totalExecutions,
      totalTests,
      averagePassRate,
      failedExecutions,
    };
  }, [filteredExecutions]);

  // Filter groups configuration
  const filterGroups: FilterGroup[] = React.useMemo(() => {
    const groups: FilterGroup[] = [
      {
        id: "status",
        label: "Status",
        options: [
          { label: "Passed", value: "passed", checked: false },
          { label: "Failed", value: "failed", checked: false },
          { label: "Mixed", value: "mixed", checked: false },
        ],
      },
    ];

    // Add module filter if modules are loaded
    if (modules && modules.length > 0) {
      groups.push({
        id: "module",
        label: "Module",
        options: modules.map((module) => ({
          label: module.name,
          value: module.id,
          checked: false,
        })),
      });
    }

    return groups;
  }, [modules]);

  const isLoading = executionsLoading || modulesLoading;

  return (
    <DashboardLayout>
      <div className="flex h-full flex-col">
        {/* Page Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            Execution Summary
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            View and analyze all test execution runs for this project
          </p>
        </div>

        {/* Summary Cards */}
        {!isLoading && !executionsError && (
          <div className="mb-6">
            <SummaryCards
              cards={[
                {
                  label: "Total Executions",
                  value: summaryMetrics.totalExecutions.toString(),
                  description: "Test runs in this period",
                  trend: undefined,
                },
                {
                  label: "Total Tests",
                  value: summaryMetrics.totalTests.toString(),
                  description: "Scenarios executed",
                  trend: undefined,
                },
                {
                  label: "Average Pass Rate",
                  value: `${summaryMetrics.averagePassRate.toFixed(1)}%`,
                  description: "Across all executions",
                  trend:
                    summaryMetrics.averagePassRate >= 80
                      ? "up"
                      : summaryMetrics.averagePassRate >= 60
                      ? "neutral"
                      : "down",
                },
                {
                  label: "Failed Executions",
                  value: summaryMetrics.failedExecutions.toString(),
                  description: "Runs with failures",
                  trend:
                    summaryMetrics.failedExecutions === 0
                      ? "up"
                      : summaryMetrics.failedExecutions < 3
                      ? "neutral"
                      : "down",
                },
              ]}
            />
          </div>
        )}

        {/* Search and Filters */}
        <div className="mb-6 flex flex-col gap-4">
          <SearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            placeholder="Search by file name, module, or uploaded by..."
            debounceMs={300}
          />
          <FilterBar
            filters={filters}
            onFilterChange={setFilters}
            filterGroups={filterGroups}
            showDateRange
          />
        </div>

        {/* Executions Table */}
        <div className="flex-1">
          {/* Loading State */}
          {isLoading && (
            <div className="space-y-4">
              {Array.from({ length: 5 }).map((_, index) => (
                <CardSkeleton key={index} />
              ))}
            </div>
          )}

          {/* Error State */}
          {executionsError && (
            <div className="flex flex-col items-center justify-center rounded-lg border border-destructive/50 bg-destructive/10 p-8 text-center">
              <AlertCircle
                className="mb-4 h-12 w-12 text-destructive"
                aria-hidden="true"
              />
              <h3 className="mb-2 text-lg font-semibold text-foreground">
                Failed to Load Executions
              </h3>
              <p className="mb-4 text-sm text-muted-foreground">
                {executionsError.detail ||
                  "An error occurred while fetching executions. Please try again."}
              </p>
              <Button onClick={() => refetchExecutions()} variant="outline">
                Try Again
              </Button>
            </div>
          )}

          {/* Executions Table */}
          {!isLoading && !executionsError && (
            <>
              <div className="mb-4 text-sm text-muted-foreground">
                Showing {filteredExecutions.length} of{" "}
                {executionsResponse?.total || 0} executions
              </div>
              <ExecutionTable
                data={filteredExecutions}
                projectId={projectId}
                enableExport
              />
              
              {/* Server-side Pagination Controls */}
              {executionsResponse && executionsResponse.total_pages > 1 && (
                <div className="mt-4 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">
                      Page {page} of {executionsResponse.total_pages}
                    </span>
                    <select
                      value={pageSize}
                      onChange={(e) => {
                        setPageSize(Number(e.target.value));
                        setPage(1); // Reset to first page when changing page size
                      }}
                      className="h-8 w-[70px] rounded-md border border-input bg-background px-2 py-1 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      aria-label="Rows per page"
                    >
                      {[10, 20, 30, 50, 100].map((size) => (
                        <option key={size} value={size}>
                          {size}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(page - 1)}
                      disabled={page <= 1}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(page + 1)}
                      disabled={page >= executionsResponse.total_pages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
