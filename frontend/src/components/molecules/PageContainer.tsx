import type { ReactNode } from 'react';

export interface PageContainerProps {
  children: ReactNode;
}

/**
 * PageContainer
 *
 * Standard outer wrapper for every top-level page. Enforces the same
 * background color and padding so pages don't drift stylistically
 * from one another.
 */
export function PageContainer({ children }: PageContainerProps) {
  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'var(--bg-primary)',
        padding: '24px',
      }}
    >
      {children}
    </div>
  );
}
