"use client"

import * as React from "react"
import { Folder, Calendar, User } from "lucide-react"
import { type StatusType } from "@/components/ui/status-icon"
import { Button } from "@/components/ui/button"
import { MiniKPICard } from "@/components/ui/MiniKPICard"
import { PulsingStatusDot } from "@/components/ui/PulsingStatusDot"
import { cn } from "@/lib/utils"

export interface ProjectCardProps {
  /**
   * Project ID
   */
  id: string | number
  /**
   * Project name
   */
  name: string
  /**
   * Project description
   */
  description?: string
  /**
   * Project status
   */
  status: "active" | "inactive" | "archived"
  /**
   * Project owner/creator
   */
  owner?: string
  /**
   * Last updated date
   */
  lastUpdated?: Date | string
  /**
   * Total test count
   */
  totalTests?: number
  /**
   * Pass rate percentage
   */
  passRate?: number
  /**
   * Module count
   */
  moduleCount?: number
  /**
   * Defect count
   */
  defects?: number
  /**
   * Latest execution status
   */
  latestStatus?: StatusType
  /**
   * Repository URL
   */
  repoUrl?: string
  /**
   * Callback when card is clicked
   */
  onClick?: () => void
  /**
   * Callback when Summary button is clicked
   */
  onSummaryClick?: () => void
  /**
   * Callback when Modules button is clicked
   */
  onModulesClick?: () => void
  /**
   * Callback when Trends button is clicked
   */
  onTrendsClick?: () => void
  /**
   * Callback when Settings button is clicked
   */
  onSettingsClick?: () => void
  /**
   * Additional CSS classes
   */
  className?: string
}

/**
 * ProjectCard component for displaying project information with status
 * 
 * @example
 * ```tsx
 * <ProjectCard
 *   id="proj-1"
 *   name="E-commerce Platform"
 *   description="Main e-commerce application"
 *   status="active"
 *   owner="John Doe"
 *   lastUpdated={new Date()}
 *   totalTests={1245}
 *   passRate={87.5}
 *   latestStatus="passed"
 *   onClick={() => router.push('/projects/proj-1')}
 * />
 * ```
 */
export function ProjectCard({
  id: _id,
  name,
  description,
  status,
  owner,
  lastUpdated,
  totalTests = 0,
  passRate = 0,
  moduleCount = 0,
  defects = 0,
  latestStatus: _latestStatus,
  repoUrl: _repoUrl,
  onClick,
  onSummaryClick,
  onModulesClick,
  onTrendsClick,
  onSettingsClick,
  className,
}: ProjectCardProps) {
  const getPassRateColor = (rate: number) => {
    if (rate >= 80) return '#10b981'; // Green
    if (rate >= 60) return '#f59e0b'; // Yellow
    return '#ef4444'; // Red
  }

  const getStatusFromText = (statusText: string): 'passed' | 'failed' | 'warning' | 'pending' | 'running' => {
    switch (statusText) {
      case 'active': return 'running';
      case 'inactive': return 'pending';
      case 'archived': return 'pending';
      default: return 'pending';
    }
  }

  const getStatusBgColor = (statusText: string) => {
    switch (statusText) {
      case 'active': return 'var(--status-green-bg)';
      case 'inactive': return 'var(--status-yellow-bg)';
      case 'archived': return 'var(--status-grey-bg)';
      default: return 'var(--status-grey-bg)';
    }
  }

  const getStatusColor = (statusText: string) => {
    switch (statusText) {
      case 'active': return 'var(--status-green)';
      case 'inactive': return 'var(--status-yellow)';
      case 'archived': return 'var(--status-grey)';
      default: return 'var(--status-grey)';
    }
  }

  const formattedDate = React.useMemo(() => {
    if (!lastUpdated) return null
    const date = typeof lastUpdated === "string" ? new Date(lastUpdated) : lastUpdated
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    })
  }, [lastUpdated])

  return (
    <article
      className={cn(
        "group relative flex flex-col rounded-lg border bg-card p-5 transition-all",
        "shadow-[var(--shadow-demo-md)] hover:shadow-[var(--shadow-card-hover)]",
        "hover:-translate-y-1 hover:scale-[1.01]",
        onClick && "cursor-pointer hover:border-primary",
        className
      )}
      onClick={onClick}
      onKeyDown={(e) => {
        if (onClick && (e.key === "Enter" || e.key === " ")) {
          e.preventDefault()
          onClick()
        }
      }}
      role={onClick ? "button" : "article"}
      tabIndex={onClick ? 0 : undefined}
      aria-label={`Project: ${name}`}
    >
      {/* Header */}
      <div className="mb-4 flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 flex-1">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary shrink-0"
            aria-hidden="true"
          >
            <Folder className="h-5 w-5" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-semibold leading-tight text-foreground truncate">
              {name}
            </h3>
            {description && (
              <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">
                {description}
              </p>
            )}
          </div>
        </div>
        {/* Status Badge with Pulsing Dot */}
        <div 
          className="shrink-0 flex items-center gap-1.5 px-3 py-1 rounded-full"
          style={{
            backgroundColor: getStatusBgColor(status)
          }}
        >
          <PulsingStatusDot status={getStatusFromText(status)} size="sm" />
          <span className="text-[11px] font-medium capitalize" style={{ color: getStatusColor(status) }}>
            {status}
          </span>
        </div>
      </div>

      {/* KPI Mini-Cards Row */}
      <div className="mb-4 grid grid-cols-4 gap-2">
        <MiniKPICard
          icon="fa-chart-pie"
          value={`${passRate.toFixed(0)}%`}
          label="Pass Rate"
          iconColor={getPassRateColor(passRate)}
        />
        <MiniKPICard
          icon="fa-cubes"
          value={moduleCount}
          label="Modules"
          iconColor="#6366f1"
        />
        <MiniKPICard
          icon="fa-vials"
          value={totalTests.toLocaleString()}
          label="Total Tests"
          iconColor="#6366f1"
        />
        <MiniKPICard
          icon="fa-bug"
          value={defects}
          label="Defects"
          iconColor="#ef4444"
        />
      </div>

      {/* Metadata Row */}
      <div className="mb-4 flex items-center justify-between text-xs text-muted-foreground border-t pt-3">
        {owner && (
          <div className="flex items-center gap-1.5">
            <User className="h-3.5 w-3.5" aria-hidden="true" />
            <span>{owner}</span>
          </div>
        )}
        {formattedDate && (
          <div className="flex items-center gap-1.5">
            <Calendar className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Last Run: {formattedDate}</span>
          </div>
        )}
      </div>

      {/* Action Buttons Row */}
      <div className="grid grid-cols-4 gap-2 mt-auto">
        <Button
          variant="outline"
          size="sm"
          className="text-xs h-8"
          onClick={(e) => {
            e.stopPropagation()
            onSummaryClick?.()
          }}
        >
          Summary
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="text-xs h-8"
          onClick={(e) => {
            e.stopPropagation()
            onModulesClick?.()
          }}
        >
          Modules
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="text-xs h-8"
          onClick={(e) => {
            e.stopPropagation()
            onTrendsClick?.()
          }}
        >
          Trends
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="text-xs h-8"
          onClick={(e) => {
            e.stopPropagation()
            onSettingsClick?.()
          }}
        >
          Settings
        </Button>
      </div>
    </article>
  )
}
