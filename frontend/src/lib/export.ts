/**
 * Export utilities for data export functionality
 * Supports CSV, JSON, and Excel formats
 */

import type { ExportOptions } from "./types";

/**
 * Convert array of objects to CSV string
 */
function arrayToCSV<T extends Record<string, any>>(
  data: T[],
  columns?: string[]
): string {
  if (data.length === 0) return "";

  // Determine columns to export
  const cols = columns || Object.keys(data[0]);

  // Create header row
  const header = cols.join(",");

  // Create data rows
  const rows = data.map((row) => {
    return cols
      .map((col) => {
        const value = row[col];
        // Handle null/undefined
        if (value === null || value === undefined) return "";
        // Escape quotes and wrap in quotes if contains comma, quote, or newline
        const stringValue = String(value);
        if (
          stringValue.includes(",") ||
          stringValue.includes('"') ||
          stringValue.includes("\n")
        ) {
          return `"${stringValue.replace(/"/g, '""')}"`;
        }
        return stringValue;
      })
      .join(",");
  });

  return [header, ...rows].join("\n");
}

/**
 * Download data as a file
 */
function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Export data to CSV file
 * 
 * @param data - Array of objects to export
 * @param filename - Name of the file (without extension)
 * @param columns - Optional array of column keys to export
 * 
 * @example
 * ```tsx
 * exportToCSV(executions, "executions-2024-01-15", ["module_name", "created_at", "status"]);
 * ```
 */
export function exportToCSV<T extends Record<string, any>>(
  data: T[],
  filename: string = "export",
  columns?: string[]
): void {
  const csv = arrayToCSV(data, columns);
  const timestamp = new Date().toISOString().split("T")[0];
  const fullFilename = `${filename}-${timestamp}.csv`;
  downloadFile(csv, fullFilename, "text/csv;charset=utf-8;");
}

/**
 * Export data to JSON file
 * 
 * @param data - Array of objects to export
 * @param filename - Name of the file (without extension)
 * @param columns - Optional array of column keys to export
 */
export function exportToJSON<T extends Record<string, any>>(
  data: T[],
  filename: string = "export",
  columns?: string[]
): void {
  let exportData = data;

  // Filter columns if specified
  if (columns) {
    exportData = data.map((row) => {
      const filtered: Record<string, any> = {};
      columns.forEach((col) => {
        filtered[col] = row[col];
      });
      return filtered as T;
    });
  }

  const json = JSON.stringify(exportData, null, 2);
  const timestamp = new Date().toISOString().split("T")[0];
  const fullFilename = `${filename}-${timestamp}.json`;
  downloadFile(json, fullFilename, "application/json;charset=utf-8;");
}

/**
 * Generic export function that handles multiple formats
 * 
 * @param data - Array of objects to export
 * @param options - Export options (format, filename, columns)
 * 
 * @example
 * ```tsx
 * exportData(executions, {
 *   format: "csv",
 *   filename: "project-executions",
 *   columns: ["module_name", "created_at", "status", "pass_rate"]
 * });
 * ```
 */
export function exportData<T extends Record<string, any>>(
  data: T[],
  options: ExportOptions
): void {
  const { format, filename = "export", columns } = options;

  switch (format) {
    case "csv":
      exportToCSV(data, filename, columns);
      break;
    case "json":
      exportToJSON(data, filename, columns);
      break;
    case "excel":
      // Excel export would require a library like xlsx
      // For now, fall back to CSV
      console.warn("Excel export not implemented, falling back to CSV");
      exportToCSV(data, filename, columns);
      break;
    default:
      throw new Error(`Unsupported export format: ${format}`);
  }
}
