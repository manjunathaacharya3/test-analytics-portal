'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useCallback, type ReactNode } from 'react';
import './sidebar-fixed.css';

interface NavItem {
  name: string;
  href: string;
  icon: string;
}

const navItems: NavItem[] = [
  { name: 'Projects', href: '/projects', icon: 'fa-project-diagram' },
  { name: 'Execution Summary', href: '/execution-summary', icon: 'fa-chart-line' },
  { name: 'Trends', href: '/trends', icon: 'fa-chart-bar' },
  { name: 'Module Details', href: '/module-details', icon: 'fa-cogs' },
  { name: 'Defect Management', href: '/defect-management', icon: 'fa-bug' },
  { name: 'AI Insights', href: '/ai-failure-analysis', icon: 'fa-brain' },
  { name: 'Settings', href: '/settings', icon: 'fa-gear' },
];

/**
 * Single shared building block for every hoverable icon in the sidebar
 * (nav items AND the user avatar). All of them get identical markup
 * (<button>), identical tooltip behavior (data-tooltip + .sidebar-action
 * CSS), and only differ visually via modifier classes. This guarantees
 * the tooltip can never drift out of sync between sections again.
 */
function SidebarIconButton({
  tooltip,
  variant,
  isActive,
  onClick,
  children,
}: {
  tooltip: string;
  variant: 'nav' | 'avatar';
  isActive?: boolean;
  onClick?: () => void;
  children: ReactNode;
}) {
  const variantClass = variant === 'nav' ? 'sidebar-action--nav' : 'sidebar-action--avatar';
  return (
    <button
      type="button"
      className={`sidebar-action ${variantClass} ${isActive ? 'active' : ''}`}
      data-tooltip={tooltip}
      aria-label={tooltip}
      aria-current={isActive ? 'page' : undefined}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const navigate = useCallback(
    (href: string) => {
      router.push(href);
    },
    [router]
  );

  return (
    <div className="sidebar-fixed">
      {/* Header/Brand Section */}
      <div className="sidebar-brand">
        <div className="brand-icon-fixed">
          <div className="brand-icon-img" />
        </div>
      </div>

      {/* Navigation Section */}
      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');
          return (
            <SidebarIconButton
              key={item.href}
              tooltip={item.name}
              variant="nav"
              isActive={isActive}
              onClick={() => navigate(item.href)}
            >
              <i className={`fas ${item.icon}`} />
            </SidebarIconButton>
          );
        })}
      </nav>

      {/* Footer Section */}
      <div className="sidebar-user">
        <SidebarIconButton tooltip="Admin User" variant="avatar">
          <i className="fas fa-user-circle" />
        </SidebarIconButton>
      </div>
    </div>
  );
}
