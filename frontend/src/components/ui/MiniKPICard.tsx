import { cn } from '@/lib/utils';

interface MiniKPICardProps {
  icon: string; // Font Awesome class (e.g., 'fa-chart-pie')
  value: string | number;
  label: string;
  iconColor?: string;
  className?: string;
}

/**
 * Mini KPI Card Component
 * Used in project cards to display key metrics
 * Matches demo app specifications with hover effects
 */
export function MiniKPICard({
  icon,
  value,
  label,
  iconColor = '#6366f1',
  className
}: MiniKPICardProps) {
  return (
    <div className={cn('kpi-card', className)}>
      <i className={`fas ${icon}`} style={{ color: iconColor }} />
      <strong>{value}</strong>
      <small>{label}</small>
    </div>
  );
}
