/**
 * UI Components - Atom Components
 * 
 * This file exports all reusable UI atom components for the TAPS application.
 * These components follow shadcn/ui design patterns and are built with:
 * - TypeScript for type safety
 * - Tailwind CSS for styling
 * - Accessibility standards (WCAG 2.1 AA)
 * - Proper ARIA labels and keyboard navigation
 */

// Badge component for status indicators
export { Badge, badgeVariants } from "./badge"
export type { BadgeProps } from "./badge"

// Button component (already exists from shadcn/ui)
export { Button, buttonVariants } from "./button"

// StatusIcon component for test execution status
export { StatusIcon, statusConfig } from "./status-icon"
export type { StatusIconProps, StatusType } from "./status-icon"

// KPICard component for displaying metrics
export { KPICard, trendConfig } from "./kpi-card"
export type { KPICardProps, TrendDirection } from "./kpi-card"

// Loading skeleton components
export {
  Skeleton,
  CardSkeleton,
  TableSkeleton,
  KPICardSkeleton,
  ChartSkeleton,
} from "./loading-skeleton"
export type { SkeletonProps } from "./loading-skeleton"

// MiniKPICard component for project card metrics
export { MiniKPICard } from "./MiniKPICard"

// PulsingStatusDot component for animated status indicators
export { PulsingStatusDot } from "./PulsingStatusDot"

// Other shadcn/ui components (already exist)
export { Sheet } from "./sheet"
export { DropdownMenu } from "./dropdown-menu"
export { Breadcrumb } from "./breadcrumb"
