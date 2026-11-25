'use client';

import { useRouter } from 'next/navigation';
import type { ReactNode } from 'react';

export interface PageHeaderProps {
  /** Main page title, e.g. "Projects", "Execution Summary" */
  title: string;
  /** Optional supporting text shown under the title */
  subtitle?: string;
  /** Whether to render the "Back to Projects" navigation button (default: true) */
  showBackButton?: boolean;
  /** Destination for the back button (default: "/projects") */
  backHref?: string;
  /** Extra content rendered next to the back button (e.g. last-updated chip, badges) */
  rightContent?: ReactNode;
}

/**
 * PageHeader
 *
 * Shared top-of-page header enforcing a single, consistent schema across every
 * page in the portal: same title typography, same back-navigation position/style,
 * and same spacing. Use this on every top-level page instead of hand-rolled headers.
 */
export function PageHeader({
  title,
  subtitle,
  showBackButton = true,
  backHref = '/projects',
  rightContent,
}: PageHeaderProps) {
  const router = useRouter();

  return (
    <div style={{ marginBottom: '24px' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: '16px',
          flexWrap: 'wrap',
        }}
      >
        <div style={{ minWidth: 0 }}>
          <h1
            style={{
              fontSize: '24px',
              fontWeight: 700,
              color: 'var(--text-primary)',
              letterSpacing: '-0.5px',
              margin: 0,
              lineHeight: 1.3,
            }}
          >
            {title}
          </h1>
          {subtitle && (
            <p
              style={{
                fontSize: '13px',
                color: 'var(--text-secondary)',
                marginTop: '6px',
                marginBottom: 0,
              }}
            >
              {subtitle}
            </p>
          )}
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            flexShrink: 0,
          }}
        >
          {rightContent}
          {showBackButton && (
            <button
              onClick={() => router.push(backHref)}
              style={{
                background: '#374151',
                borderRadius: '6px',
                padding: '8px 16px',
                fontSize: '13px',
                fontWeight: 500,
                color: 'white',
                border: 'none',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'background 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#111827';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = '#374151';
              }}
            >
              ← Back to Projects
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
