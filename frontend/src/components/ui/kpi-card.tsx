import * as React from "react"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"
import { cn } from "@/lib/utils"

export type TrendDirection = "up" | "down" | "neutral"

export interface KPICardProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * The label/title of the metric
   */
  label: string
  /**
   * The main value to display
   */
  value: string | number
  /**
   * Optional trend direction
   */
  trend?: TrendDirection
  /**
   * Optional trend value (e.g., "+12%", "-5%")
   */
  trendValue?: string
  /**
   * Optional icon to display
   */
  icon?: React.ReactNode
  /**
   * Optional description or subtitle
   */
  description?: string
}

const trendConfig = {
  up: {
    icon: TrendingUp,
    color: "text-green-600 dark:text-green-500",
    bgColor: "bg-green-50 dark:bg-green-950/30",
    ariaLabel: "Trending up",
  },
  down: {
    icon: TrendingDown,
    color: "text-red-600 dark:text-red-500",
    bgColor: "bg-red-50 dark:bg-red-950/30",
    ariaLabel: "Trending down",
  },
  neutral: {
    icon: Minus,
    color: "text-gray-600 dark:text-gray-400",
    bgColor: "bg-gray-50 dark:bg-gray-950/30",
    ariaLabel: "No change",
  },
}

/**
 * KPICard component for displaying key performance indicators
 * 
 * @example
 * ```tsx
 * <KPICard
 *   label="Total Tests"
 *   value={1245}
 *   trend="up"
 *   trendValue="+12%"
 *   icon={<TestTubeIcon />}
 * />
 * ```
 */
function KPICard({
  label,
  value,
  trend,
  trendValue,
  icon,
  description,
  className,
  ...props
}: KPICardProps) {
  const trendInfo = trend ? trendConfig[trend] : null
  const TrendIcon = trendInfo?.icon

  return (
    <div
      className={cn(
        "rounded-lg border bg-card p-6 text-card-foreground shadow-sm transition-all hover:shadow-md",
        className
      )}
      role="article"
      aria-label={`${label}: ${value}`}
      {...props}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-muted-foreground">{label}</p>
          <div className="mt-2 flex items-baseline gap-2">
            <h3 className="text-3xl font-bold tracking-tight">{value}</h3>
            {trendInfo && trendValue && TrendIcon && (
              <div
                className={cn(
                  "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
                  trendInfo.bgColor
                )}
                role="status"
                aria-label={`${trendInfo.ariaLabel}: ${trendValue}`}
              >
                <TrendIcon className={cn("h-3 w-3", trendInfo.color)} aria-hidden="true" />
                <span className={trendInfo.color}>{trendValue}</span>
              </div>
            )}
          </div>
          {description && (
            <p className="mt-2 text-xs text-muted-foreground">{description}</p>
          )}
        </div>
        {icon && (
          <div
            className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary"
            aria-hidden="true"
          >
            {icon}
          </div>
        )}
      </div>
    </div>
  )
}

export { KPICard, trendConfig }
