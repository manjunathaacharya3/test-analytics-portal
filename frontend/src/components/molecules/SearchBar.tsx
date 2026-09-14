"use client"

import * as React from "react"
import { Search, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export interface SearchBarProps {
  /**
   * Current search value
   */
  value: string
  /**
   * Callback when search value changes
   */
  onChange: (value: string) => void
  /**
   * Placeholder text
   * @default "Search..."
   */
  placeholder?: string
  /**
   * Debounce delay in milliseconds
   * @default 300
   */
  debounceMs?: number
  /**
   * Whether to show clear button
   * @default true
   */
  showClearButton?: boolean
  /**
   * Callback when search is cleared
   */
  onClear?: () => void
  /**
   * Additional CSS classes
   */
  className?: string
  /**
   * Disable the search input
   * @default false
   */
  disabled?: boolean
}

/**
 * SearchBar component with debounced input
 * 
 * @example
 * ```tsx
 * const [searchQuery, setSearchQuery] = useState("")
 * 
 * <SearchBar
 *   value={searchQuery}
 *   onChange={setSearchQuery}
 *   placeholder="Search projects..."
 *   debounceMs={300}
 * />
 * ```
 */
export function SearchBar({
  value,
  onChange,
  placeholder = "Search...",
  debounceMs = 300,
  showClearButton = true,
  onClear,
  className,
  disabled = false,
}: SearchBarProps) {
  const [localValue, setLocalValue] = React.useState(value)
  const debounceTimerRef = React.useRef<NodeJS.Timeout | null>(null)
  const inputRef = React.useRef<HTMLInputElement>(null)

  // Sync local value with prop value
  React.useEffect(() => {
    setLocalValue(value)
  }, [value])

  // Debounced onChange
  const handleChange = (newValue: string) => {
    setLocalValue(newValue)

    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    // Set new timer
    debounceTimerRef.current = setTimeout(() => {
      onChange(newValue)
    }, debounceMs)
  }

  // Clear search
  const handleClear = () => {
    setLocalValue("")
    onChange("")
    onClear?.()
    inputRef.current?.focus()
  }

  // Cleanup timer on unmount
  React.useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [])

  const showClear = showClearButton && localValue.length > 0

  return (
    <div
      className={cn(
        "relative flex items-center rounded-lg border bg-background",
        disabled && "opacity-50",
        className
      )}
      role="search"
    >
      <div className="pointer-events-none absolute left-3 flex items-center">
        <Search
          className="h-4 w-4 text-muted-foreground"
          aria-hidden="true"
        />
      </div>
      <input
        ref={inputRef}
        type="text"
        value={localValue}
        onChange={(e) => handleChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className={cn(
          "h-10 w-full rounded-lg bg-transparent pl-10 pr-10 text-sm outline-none placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed",
          !showClear && "pr-3"
        )}
        aria-label={placeholder}
      />
      {showClear && (
        <div className="absolute right-1 flex items-center">
          <Button
            variant="ghost"
            size="icon-xs"
            onClick={handleClear}
            disabled={disabled}
            aria-label="Clear search"
            type="button"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </Button>
        </div>
      )}
    </div>
  )
}
