"use client"

import { KPICard, type KPICardProps } from "@/components/ui/kpi-card"
import { KPICardSkeleton } from "@/components/ui/loading-skeleton"
import { cn } from "@/lib/utils"

export interface SummaryCardsProps {
  /**
   * Array of KPI card data to display
   */
  cards: KPICardProps[]
  /**
   * Loading state
   * @default false
   */
  loading?: boolean
  /**
   * Number of columns in the grid
   * @default "auto" - responsive grid
   */
  columns?: 1 | 2 | 3 | 4 | "auto"
  /**
   * Additional CSS classes
   */
  className?: string
}

const columnClasses = {
  1: "grid-cols-1",
  2: "grid-cols-1 md:grid-cols-2",
  3: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
  4: "grid-cols-1 md:grid-cols-2 lg:grid-cols-4",
  auto: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4",
}

/**
 * SummaryCards component for displaying a grid of KPI cards
 * 
 * @example
 * ```tsx
 * const cards: KPICardProps[] = [
 *   {
 *     label: "Total Tests",
 *     value: 1245,
 *     trend: "up",
 *     trendValue: "+12%",
 *     icon: <TestTubeIcon />
 *   },
 *   {
 *     label: "Pass Rate",
 *     value: "87.5%",
 *     trend: "down",
 *     trendValue: "-2.3%",
 *   }
 * ]
 * 
 * <SummaryCards cards={cards} />
 * ```
 */
export function SummaryCards({
  cards,
  loading = false,
  columns = "auto",
  className,
}: SummaryCardsProps) {
  if (loading) {
    return (
      <div
        className={cn(
          "grid gap-4",
          columnClasses[columns],
          className
        )}
        role="status"
        aria-label="Loading summary cards"
        aria-live="polite"
      >
        {Array.from({ length: 4 }).map((_, index) => (
          <KPICardSkeleton key={index} />
        ))}
      </div>
    )
  }

  if (cards.length === 0) {
    return (
      <div
        className={cn(
          "flex min-h-[200px] items-center justify-center rounded-lg border border-dashed",
          className
        )}
        role="status"
      >
        <p className="text-sm text-muted-foreground">No metrics available</p>
      </div>
    )
  }

  return (
    <div
      className={cn(
        "grid gap-4",
        columnClasses[columns],
        className
      )}
      role="region"
      aria-label="Summary metrics"
    >
      {cards.map((card, index) => (
        <KPICard
          key={`${card.label}-${index}`}
          {...card}
        />
      ))}
    </div>
  )
}
