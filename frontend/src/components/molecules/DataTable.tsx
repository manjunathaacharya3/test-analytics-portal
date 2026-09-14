"use client"

import * as React from "react"
import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type ColumnFiltersState,
  type SortingState,
  type VisibilityState,
  type Row,
} from "@tanstack/react-table"
import {
  ChevronDown,
  ChevronUp,
  ChevronsUpDown,
  ChevronLeft,
  ChevronRight,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export interface DataTableProps<TData, TValue = unknown> {
  /**
   * Column definitions for the table
   */
  columns: ColumnDef<TData, TValue>[]
  /**
   * Data to display in the table
   */
  data: TData[]
  /**
   * Enable pagination
   * @default true
   */
  pagination?: boolean
  /**
   * Enable sorting
   * @default true
   */
  sorting?: boolean
  /**
   * Enable filtering
   * @default false
   */
  filtering?: boolean
  /**
   * Enable row selection
   * @default false
   */
  rowSelection?: boolean
  /**
   * Callback when a row is clicked
   */
  onRowClick?: (row: Row<TData>) => void
  /**
   * Initial page size
   * @default 10
   */
  pageSize?: number
  /**
   * Custom empty state message
   */
  emptyMessage?: string
  /**
   * Additional CSS classes for the table container
   */
  className?: string
}

/**
 * DataTable component with sorting, pagination, and row selection
 * Built with TanStack Table (React Table v8)
 * 
 * @example
 * ```tsx
 * const columns: ColumnDef<User>[] = [
 *   {
 *     accessorKey: "name",
 *     header: "Name",
 *   },
 *   {
 *     accessorKey: "email",
 *     header: "Email",
 *   },
 * ]
 * 
 * <DataTable
 *   columns={columns}
 *   data={users}
 *   pagination
 *   sorting
 *   onRowClick={(row) => console.log(row.original)}
 * />
 * ```
 */
export function DataTable<TData, TValue = unknown>({
  columns,
  data,
  pagination = true,
  sorting = true,
  filtering = false,
  rowSelection = false,
  onRowClick,
  pageSize = 10,
  emptyMessage = "No results found.",
  className,
}: DataTableProps<TData, TValue>) {
  const [sortingState, setSortingState] = React.useState<SortingState>([])
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    []
  )
  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({})
  const [rowSelectionState, setRowSelectionState] = React.useState({})

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: pagination ? getPaginationRowModel() : undefined,
    getSortedRowModel: sorting ? getSortedRowModel() : undefined,
    getFilteredRowModel: filtering ? getFilteredRowModel() : undefined,
    onSortingChange: sorting ? setSortingState : undefined,
    onColumnFiltersChange: filtering ? setColumnFilters : undefined,
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: rowSelection ? setRowSelectionState : undefined,
    state: {
      sorting: sortingState,
      columnFilters,
      columnVisibility,
      rowSelection: rowSelectionState,
    },
    initialState: {
      pagination: {
        pageSize,
      },
    },
    enableRowSelection: rowSelection,
  })

  return (
    <div className={cn("w-full space-y-4", className)}>
      <div className="rounded-md border">
        <div className="relative w-full overflow-auto">
          <table
            className="w-full caption-bottom text-sm"
            role="table"
            aria-label="Data table"
          >
            <thead className="[&_tr]:border-b">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id} role="row">
                  {headerGroup.headers.map((header) => {
                    const canSort = header.column.getCanSort()
                    const isSorted = header.column.getIsSorted()

                    return (
                      <th
                        key={header.id}
                        className="h-12 px-4 text-left align-middle font-bold text-white [&:has([role=checkbox])]:pr-0"
                        style={{ backgroundColor: 'var(--dark-primary)' }}
                        role="columnheader"
                        aria-sort={
                          isSorted === "asc"
                            ? "ascending"
                            : isSorted === "desc"
                            ? "descending"
                            : "none"
                        }
                      >
                        {header.isPlaceholder ? null : (
                          <div
                            className={cn(
                              "flex items-center gap-2",
                              canSort && "cursor-pointer select-none"
                            )}
                            onClick={
                              canSort
                                ? header.column.getToggleSortingHandler()
                                : undefined
                            }
                            onKeyDown={
                              canSort
                                ? (e) => {
                                    if (e.key === "Enter" || e.key === " ") {
                                      e.preventDefault()
                                      header.column.getToggleSortingHandler()?.(e)
                                    }
                                  }
                                : undefined
                            }
                            role={canSort ? "button" : undefined}
                            tabIndex={canSort ? 0 : undefined}
                            aria-label={
                              canSort
                                ? `Sort by ${header.column.id}`
                                : undefined
                            }
                          >
                            {flexRender(
                              header.column.columnDef.header,
                              header.getContext()
                            )}
                            {canSort && (
                              <span aria-hidden="true">
                                {isSorted === "asc" ? (
                                  <ChevronUp className="h-4 w-4" />
                                ) : isSorted === "desc" ? (
                                  <ChevronDown className="h-4 w-4" />
                                ) : (
                                  <ChevronsUpDown className="h-4 w-4 opacity-50" />
                                )}
                              </span>
                            )}
                          </div>
                        )}
                      </th>
                    )
                  })}
                </tr>
              ))}
            </thead>
            <tbody className="[&_tr:last-child]:border-0">
              {table.getRowModel().rows?.length ? (
                table.getRowModel().rows.map((row) => {
                  // Get status from row data for conditional styling
                  const rowData = row.original as any;
                  const status = rowData?.status?.toLowerCase() || rowData?.latestStatus?.toLowerCase() || '';
                  
                  // Determine background color based on status
                  const getRowBgClass = () => {
                    if (status.includes('pass') || status === '✅') return 'bg-[var(--status-green-bg)]';
                    if (status.includes('fail') || status === '❌') return 'bg-[var(--status-red-bg)]';
                    if (status.includes('warn') || status.includes('skip') || status === '⚠️') return 'bg-[var(--status-yellow-bg)]';
                    return '';
                  };
                  
                  return (
                  <tr
                    key={row.id}
                    data-state={row.getIsSelected() && "selected"}
                    className={cn(
                      "border-b transition-colors data-[state=selected]:bg-muted",
                      "hover:!bg-[#e2e8f0]",
                      getRowBgClass(),
                      onRowClick && "cursor-pointer"
                    )}
                    onClick={() => onRowClick?.(row)}
                    onKeyDown={(e) => {
                      if (onRowClick && (e.key === "Enter" || e.key === " ")) {
                        e.preventDefault()
                        onRowClick(row)
                      }
                    }}
                    role="row"
                    tabIndex={onRowClick ? 0 : undefined}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td
                        key={cell.id}
                        className="p-4 align-middle [&:has([role=checkbox])]:pr-0"
                        role="cell"
                      >
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext()
                        )}
                      </td>
                    ))}
                  </tr>
                )})
              ) : (
                <tr>
                  <td
                    colSpan={columns.length}
                    className="h-24 text-center"
                    role="cell"
                  >
                    <div className="text-muted-foreground">{emptyMessage}</div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {pagination && (
        <DataTablePagination
          table={table}
          rowSelectionEnabled={rowSelection}
        />
      )}
    </div>
  )
}

interface DataTablePaginationProps<TData> {
  table: ReturnType<typeof useReactTable<TData>>
  rowSelectionEnabled?: boolean
}

function DataTablePagination<TData>({
  table,
  rowSelectionEnabled,
}: DataTablePaginationProps<TData>) {
  return (
    <div
      className="flex items-center justify-between px-2"
      role="navigation"
      aria-label="Table pagination"
    >
      <div className="flex-1 text-sm text-muted-foreground">
        {rowSelectionEnabled && (
          <span>
            {table.getFilteredSelectedRowModel().rows.length} of{" "}
            {table.getFilteredRowModel().rows.length} row(s) selected.
          </span>
        )}
      </div>
      <div className="flex items-center space-x-6 lg:space-x-8">
        <div className="flex items-center space-x-2">
          <p className="text-sm font-medium">Rows per page</p>
          <select
            value={table.getState().pagination.pageSize}
            onChange={(e) => {
              table.setPageSize(Number(e.target.value))
            }}
            className="h-8 w-[70px] rounded-md border border-input bg-background px-2 py-1 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="Rows per page"
          >
            {[5, 10, 20, 30, 40, 50].map((pageSize) => (
              <option key={pageSize} value={pageSize}>
                {pageSize}
              </option>
            ))}
          </select>
        </div>
        <div className="flex w-[100px] items-center justify-center text-sm font-medium">
          Page {table.getState().pagination.pageIndex + 1} of{" "}
          {table.getPageCount()}
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="icon-sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            aria-label="Go to previous page"
          >
            <ChevronLeft className="h-4 w-4" aria-hidden="true" />
          </Button>
          <Button
            variant="outline"
            size="icon-sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            aria-label="Go to next page"
          >
            <ChevronRight className="h-4 w-4" aria-hidden="true" />
          </Button>
        </div>
      </div>
    </div>
  )
}

export { DataTablePagination }
