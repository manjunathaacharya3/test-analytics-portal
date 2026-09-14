import { cn } from '@/lib/utils';

interface PulsingStatusDotProps {
  status: 'passed' | 'failed' | 'warning' | 'pending' | 'running';
  size?: 'sm' | 'md' | 'lg';
  withPulse?: boolean;
  className?: string;
}

const statusColors = {
  passed: '#10b981',
  failed: '#ef4444',
  warning: '#f59e0b',
  pending: '#94a3b8',
  running: '#6366f1'
};

const sizes = {
  sm: '6px',
  md: '8px',
  lg: '10px'
};

/**
 * Pulsing Status Dot Component
 * Displays an animated status indicator
 * Matches demo app specifications
 */
export function PulsingStatusDot({
  status,
  size = 'md',
  withPulse = true,
  className
}: PulsingStatusDotProps) {
  const color = statusColors[status];
  const dotSize = sizes[size];

  return (
    <div
      className={cn('status-dot', withPulse && 'pulse', className)}
      style={{
        width: dotSize,
        height: dotSize,
        backgroundColor: color,
        boxShadow: `0 0 8px ${color}`
      }}
    />
  );
}
