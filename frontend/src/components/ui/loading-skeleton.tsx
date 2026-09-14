import * as React from "react"
import { cn } from "@/lib/utils"

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * The variant/shape of the skeleton
   * @default "default"
   */
  variant?: "default" | "text" | "circular" | "rectangular"
  /**
   * Width of the skeleton
   */
  width?: string | number
  /**
   * Height of the skeleton
   */
  height?: string | number
  /**
   * Whether to animate the skeleton
   * @default true
   */
  animate?: boolean
}

const variantStyles = {
  default: "rounded-md",
  text: "rounded h-4",
  circular: "rounded-full",
  rectangular: "rounded-none",
}

/**
 * Skeleton component for loading states
 * 
 * @example
 * ```tsx
 * <Skeleton className="h-12 w-12" variant="circular" />
 * <Skeleton className="h-4 w-full" variant="text" />
 * <Skeleton className="h-32 w-full" />
 * ```
 */
function Skeleton({
  className,
  variant = "default",
  width,
  height,
  animate = true,
  ...props
}: SkeletonProps) {
  const style: React.CSSProperties = {
    width: typeof width === "number" ? `${width}px` : width,
    height: typeof height === "number" ? `${height}px` : height,
  }

  return (
    <div
      className={cn(
        "bg-muted",
        variantStyles[variant],
        animate && "animate-pulse",
        className
      )}
      style={style}
      role="status"
      aria-label="Loading..."
      aria-live="polite"
      {...props}
    >
      <span className="sr-only">Loading...</span>
    </div>
  )
}

/**
 * CardSkeleton component for loading card layouts
 */
function CardSkeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("space-y-3 rounded-lg border bg-card p-6", className)}
      role="status"
      aria-label="Loading card..."
      {...props}
    >
      <Skeleton className="h-5 w-2/5" />
      <Skeleton className="h-4 w-4/5" />
      <Skeleton className="h-4 w-3/5" />
    </div>
  )
}

/**
 * TableSkeleton component for loading table rows
 */
function TableSkeleton({
  rows = 5,
  columns = 4,
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { rows?: number; columns?: number }) {
  return (
    <div
      className={cn("space-y-2", className)}
      role="status"
      aria-label="Loading table..."
      {...props}
    >
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex gap-4">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton key={colIndex} className="h-8 flex-1" />
          ))}
        </div>
      ))}
    </div>
  )
}

/**
 * KPICardSkeleton component for loading KPI cards
 */
function KPICardSkeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("rounded-lg border bg-card p-6", className)}
      role="status"
      aria-label="Loading metric..."
      {...props}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-32" />
        </div>
        <Skeleton className="h-10 w-10" variant="circular" />
      </div>
    </div>
  )
}

/**
 * ChartSkeleton component for loading charts
 */
function ChartSkeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("space-y-3 rounded-lg border bg-card p-6", className)}
      role="status"
      aria-label="Loading chart..."
      {...props}
    >
      <Skeleton className="h-6 w-48" />
      <Skeleton className="h-64 w-full" />
      <div className="flex justify-center gap-4">
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-4 w-20" />
      </div>
    </div>
  )
}

export {
  Skeleton,
  CardSkeleton,
  TableSkeleton,
  KPICardSkeleton,
  ChartSkeleton,
}
