'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
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

export function Sidebar() {
  const pathname = usePathname();

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
            <Link
              key={item.href}
              href={item.href}
              className={`nav-item-fixed ${isActive ? 'active' : ''}`}
              data-tooltip={item.name}
              aria-label={item.name}
              title={item.name}
            >
              <i className={`fas ${item.icon}`} />
            </Link>
          );
        })}
      </nav>

      {/* Footer Section */}
      <div className="sidebar-user">
        <div 
          className="user-avatar-fixed"
          data-tooltip="Admin User"
          aria-label="User profile"
        >
          <i className="fas fa-user-circle" />
        </div>
      </div>
    </div>
  );
}
