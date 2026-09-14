"use client"

import * as React from "react"
import { Calendar, Filter, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"

export interface DateRange {
  from: Date | null
  to: Date | null
}

export interface FilterOption {
  label: string
  value: string
  checked: boolean
}

export interface FilterGroup {
  id: string
  label: string
  options: FilterOption[]
}

export interface Filters {
  dateRange?: DateRange
  status?: string[]
  module?: string
  [key: string]: any
}

export interface FilterBarProps {
  /**
   * Current filter values
   */
  filters: Filters
  /**
   * Callback when filters change
   */
  onFilterChange: (filters: Filters) => void
  /**
   * Filter groups configuration
   */
  filterGroups?: FilterGroup[]
  /**
   * Whether to show date range picker
   * @default true
   */
  showDateRange?: boolean
  /**
   * Whether to show clear all button
   * @default true
   */
  showClearAll?: boolean
  /**
   * Additional CSS classes
   */
  className?: string
}

/**
 * FilterBar component for displaying filter controls with date picker and dropdowns
 * 
 * @example
 * ```tsx
 * const [filters, setFilters] = useState<Filters>({
 *   dateRange: { from: null, to: null },
 *   status: []
 * })
 * 
 * const filterGroups: FilterGroup[] = [
 *   {
 *     id: 'status',
 *     label: 'Status',
 *     options: [
 *       { label: 'Passed', value: 'passed', checked: false },
 *       { label: 'Failed', value: 'failed', checked: false },
 *     ]
 *   }
 * ]
 * 
 * <FilterBar
 *   filters={filters}
 *   onFilterChange={setFilters}
 *   filterGroups={filterGroups}
 * />
 * ```
 */
export function FilterBar({
  filters,
  onFilterChange,
  filterGroups = [],
  showDateRange = true,
  showClearAll = true,
  className,
}: FilterBarProps) {
  const [localFilters, setLocalFilters] = React.useState<Filters>(filters)

  React.useEffect(() => {
    setLocalFilters(filters)
  }, [filters])

  const handleFilterGroupChange = (groupId: string, selectedValues: string[]) => {
    const newFilters = {
      ...localFilters,
      [groupId]: selectedValues,
    }
    setLocalFilters(newFilters)
    onFilterChange(newFilters)
  }

  const handleDateRangeChange = (range: DateRange) => {
    const newFilters = {
      ...localFilters,
      dateRange: range,
    }
    setLocalFilters(newFilters)
    onFilterChange(newFilters)
  }

  const handleClearAll = () => {
    const clearedFilters: Filters = {
      dateRange: { from: null, to: null },
    }
    filterGroups.forEach((group) => {
      clearedFilters[group.id] = []
    })
    setLocalFilters(clearedFilters)
    onFilterChange(clearedFilters)
  }

  const getActiveFilterCount = () => {
    let count = 0
    if (localFilters.dateRange?.from || localFilters.dateRange?.to) count++
    filterGroups.forEach((group) => {
      const values = localFilters[group.id] as string[] | undefined
      if (values && values.length > 0) count += values.length
    })
    return count
  }

  const activeFilterCount = getActiveFilterCount()

  return (
    <div
      className={cn(
        "filter-row flex flex-wrap items-center gap-2 rounded-lg border",
        className
      )}
      role="search"
      aria-label="Filter controls"
    >
      <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
        <Filter className="h-4 w-4" aria-hidden="true" />
        <span>Filters</span>
        {activeFilterCount > 0 && (
          <Badge variant="info" className="ml-1">
            {activeFilterCount}
          </Badge>
        )}
      </div>

      <div className="flex flex-1 flex-wrap items-center gap-2">
        {showDateRange && (
          <DateRangeFilter
            value={localFilters.dateRange}
            onChange={handleDateRangeChange}
          />
        )}

        {filterGroups.map((group) => (
          <FilterDropdown
            key={group.id}
            group={group}
            selectedValues={(localFilters[group.id] as string[]) || []}
            onChange={(values) => handleFilterGroupChange(group.id, values)}
          />
        ))}
      </div>

      {showClearAll && activeFilterCount > 0 && (
        <Button
          variant="ghost"
          size="sm"
          onClick={handleClearAll}
          className="ml-auto"
          aria-label="Clear all filters"
        >
          <X className="h-4 w-4" />
          Clear All
        </Button>
      )}
    </div>
  )
}

interface DateRangeFilterProps {
  value?: DateRange
  onChange: (range: DateRange) => void
}

function DateRangeFilter({ value, onChange }: DateRangeFilterProps) {
  const [isOpen, setIsOpen] = React.useState(false)
  const [fromDate, setFromDate] = React.useState<string>(
    value?.from ? value.from.toISOString().split("T")[0] : ""
  )
  const [toDate, setToDate] = React.useState<string>(
    value?.to ? value.to.toISOString().split("T")[0] : ""
  )

  const handleApply = () => {
    onChange({
      from: fromDate ? new Date(fromDate) : null,
      to: toDate ? new Date(toDate) : null,
    })
    setIsOpen(false)
  }

  const hasDateRange = value?.from || value?.to

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={cn(
            "gap-2",
            hasDateRange && "border-primary text-primary"
          )}
          aria-label="Filter by date range"
        >
          <Calendar className="h-4 w-4" aria-hidden="true" />
          {hasDateRange ? (
            <span>
              {value?.from?.toLocaleDateString()} -{" "}
              {value?.to?.toLocaleDateString()}
            </span>
          ) : (
            <span>Date Range</span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-80">
        <DropdownMenuLabel>Select Date Range</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <div className="space-y-4 p-4">
          <div className="space-y-2">
            <label
              htmlFor="from-date"
              className="text-sm font-medium text-foreground"
            >
              From
            </label>
            <input
              id="from-date"
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-label="From date"
            />
          </div>
          <div className="space-y-2">
            <label
              htmlFor="to-date"
              className="text-sm font-medium text-foreground"
            >
              To
            </label>
            <input
              id="to-date"
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-label="To date"
            />
          </div>
          <Button onClick={handleApply} className="w-full" size="sm">
            Apply
          </Button>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

interface FilterDropdownProps {
  group: FilterGroup
  selectedValues: string[]
  onChange: (values: string[]) => void
}

function FilterDropdown({
  group,
  selectedValues,
  onChange,
}: FilterDropdownProps) {
  const handleToggle = (value: string) => {
    const newValues = selectedValues.includes(value)
      ? selectedValues.filter((v) => v !== value)
      : [...selectedValues, value]
    onChange(newValues)
  }

  const hasSelection = selectedValues.length > 0

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={cn(
            "gap-2",
            hasSelection && "border-primary text-primary"
          )}
          aria-label={`Filter by ${group.label}`}
        >
          {group.label}
          {hasSelection && (
            <Badge variant="info" className="ml-1">
              {selectedValues.length}
            </Badge>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        <DropdownMenuLabel>{group.label}</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {group.options.map((option) => (
          <DropdownMenuCheckboxItem
            key={option.value}
            checked={selectedValues.includes(option.value)}
            onCheckedChange={() => handleToggle(option.value)}
          >
            {option.label}
          </DropdownMenuCheckboxItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
