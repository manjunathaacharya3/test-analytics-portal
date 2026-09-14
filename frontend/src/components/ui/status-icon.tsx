import * as React from "react"
import { CheckCircle2, XCircle, MinusCircle, Circle, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

export type StatusType = "passed" | "failed" | "skipped" | "pending" | "running"

export interface StatusIconProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * The status type to display
   */
  status: StatusType
  /**
   * Size of the icon
   * @default "md"
   */
  size?: "sm" | "md" | "lg"
  /**
   * Whether to show the status label text
   * @default false
   */
  showLabel?: boolean
}

const iconSizes = {
  sm: "h-4 w-4",
  md: "h-5 w-5",
  lg: "h-6 w-6",
}

const statusConfig = {
  passed: {
    icon: CheckCircle2,
    color: "text-green-600 dark:text-green-500",
    label: "Passed",
    ariaLabel: "Test passed",
  },
  failed: {
    icon: XCircle,
    color: "text-red-600 dark:text-red-500",
    label: "Failed",
    ariaLabel: "Test failed",
  },
  skipped: {
    icon: MinusCircle,
    color: "text-yellow-600 dark:text-yellow-500",
    label: "Skipped",
    ariaLabel: "Test skipped",
  },
  pending: {
    icon: Circle,
    color: "text-gray-600 dark:text-gray-400",
    label: "Pending",
    ariaLabel: "Test pending",
  },
  running: {
    icon: Loader2,
    color: "text-blue-600 dark:text-blue-500 animate-spin",
    label: "Running",
    ariaLabel: "Test running",
  },
}

/**
 * StatusIcon component for displaying test execution status
 * 
 * @example
 * ```tsx
 * <StatusIcon status="passed" />
 * <StatusIcon status="failed" size="lg" />
 * <StatusIcon status="skipped" showLabel />
 * ```
 */
function StatusIcon({
  status,
  size = "md",
  showLabel = false,
  className,
  ...props
}: StatusIconProps) {
  const config = statusConfig[status]
  const Icon = config.icon

  return (
    <div
      className={cn("inline-flex items-center gap-1.5", className)}
      role="img"
      aria-label={config.ariaLabel}
      {...props}
    >
      <Icon
        className={cn(iconSizes[size], config.color)}
        aria-hidden="true"
      />
      {showLabel && (
        <span className={cn("text-sm font-medium", config.color)}>
          {config.label}
        </span>
      )}
    </div>
  )
}

export { StatusIcon, statusConfig }
