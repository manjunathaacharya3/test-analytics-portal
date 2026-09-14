"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { type ColumnDef } from "@tanstack/react-table";
import { Download } from "lucide-react";
import { DataTable } from "@/components/molecules/DataTable";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatusIcon } from "@/components/ui/status-icon";
import type { Execution } from "@/lib/types";
import {
  formatDate,
  formatDuration,
  formatPassRate,
  getStatusVariant,
} from "@/lib/utils";
import { exportToCSV } from "@/lib/export";

export interface ExecutionTableProps {
  /**
   * Execution data to display
   */
  data: Execution[];
  /**
   * Project ID for navigation
   */
  projectId: string;
  /**
   * Enable export functionality
   * @default true
   */
  enableExport?: boolean;
  /**
   * Custom empty message
   */
  emptyMessage?: string;
}

/**
 * ExecutionTable component
 * 
 * Displays execution data in a sortable, paginated table with export functionality.
 * Clicking a row navigates to the execution detail page.
 * 
 * @example
 * ```tsx
 * <ExecutionTable
 *   data={executions}
 *   isLoading={isLoading}
 *   projectId="project-123"
 *   enableExport
 * />
 * ```
 */
export function ExecutionTable({
  data,
  projectId,
  enableExport = true,
  emptyMessage = "No executions found. Upload a test report to get started.",
}: ExecutionTableProps) {
  const router = useRouter();

  // Define table columns
  const columns: ColumnDef<Execution>[] = React.useMemo(
    () => [
      {
        accessorKey: "file_name",
        header: "Module",
        cell: ({ row }) => {
          const fileName = row.original.file_name;
          const moduleName = row.original.module_name;
          return (
            <div className="flex flex-col">
              <span className="font-medium text-foreground">
                {moduleName || "Unknown Module"}
              </span>
              <span className="text-xs text-muted-foreground">
                {fileName}
              </span>
            </div>
          );
        },
      },
      {
        accessorKey: "created_at",
        header: "Date",
        cell: ({ row }) => (
          <span className="text-sm text-foreground">
            {formatDate(row.original.created_at)}
          </span>
        ),
        enableSorting: true,
      },
      {
        accessorKey: "total_scenarios",
        header: "Total Tests",
        cell: ({ row }) => (
          <span className="font-medium text-foreground">
            {row.original.total_scenarios}
          </span>
        ),
        enableSorting: true,
      },
      {
        accessorKey: "passed_scenarios",
        header: "Passed",
        cell: ({ row }) => (
          <span className="font-medium text-green-600 dark:text-green-400">
            {row.original.passed_scenarios}
          </span>
        ),
        enableSorting: true,
      },
      {
        accessorKey: "failed_scenarios",
        header: "Failed",
        cell: ({ row }) => (
          <span className="font-medium text-red-600 dark:text-red-400">
            {row.original.failed_scenarios}
          </span>
        ),
        enableSorting: true,
      },
      {
        accessorKey: "pass_rate",
        header: "Pass Rate",
        cell: ({ row }) => (
          <span className="font-medium text-foreground">
            {formatPassRate(row.original.pass_rate)}
          </span>
        ),
        enableSorting: true,
      },
      {
        accessorKey: "duration",
        header: "Duration",
        cell: ({ row }) => (
          <span className="text-sm text-muted-foreground">
            {formatDuration(row.original.duration)}
          </span>
        ),
        enableSorting: true,
      },
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => {
          const status = row.original.status;
          // Map execution status to StatusIcon compatible type
          const iconStatus: "passed" | "failed" | "skipped" | "pending" | "running" = 
            status === "mixed" ? "failed" : status;
          
          return (
            <Badge variant={getStatusVariant(status)}>
              <StatusIcon status={iconStatus} className="mr-1 h-3 w-3" />
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </Badge>
          );
        },
        enableSorting: true,
      },
    ],
    []
  );

  // Handle row click - navigate to execution detail
  const handleRowClick = (row: any) => {
    const executionId = row.original.id;
    router.push(`/projects/${projectId}/executions/${executionId}`);
  };

  // Handle export to CSV
  const handleExport = () => {
    const exportData = data.map((execution) => ({
      Module: execution.module_name || "Unknown",
      File: execution.file_name,
      Date: formatDate(execution.created_at),
      "Total Tests": execution.total_scenarios,
      Passed: execution.passed_scenarios,
      Failed: execution.failed_scenarios,
      Skipped: execution.skipped_scenarios,
      "Pass Rate": formatPassRate(execution.pass_rate),
      Duration: formatDuration(execution.duration),
      Status: execution.status,
      "Uploaded By": execution.uploaded_by,
    }));

    exportToCSV(exportData, `executions-project-${projectId}`);
  };

  return (
    <div className="space-y-4">
      {/* Export Button */}
      {enableExport && data.length > 0 && (
        <div className="flex justify-end">
          <Button
            onClick={handleExport}
            variant="outline"
            size="sm"
            className="gap-2"
            aria-label="Export to CSV"
          >
            <Download className="h-4 w-4" aria-hidden="true" />
            Export to CSV
          </Button>
        </div>
      )}

      {/* Data Table */}
      <DataTable
        columns={columns}
        data={data}
        pagination
        sorting
        onRowClick={handleRowClick}
        pageSize={20}
        emptyMessage={emptyMessage}
        className="rounded-lg border"
      />
    </div>
  );
}
