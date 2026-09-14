'use client';

import React, { memo } from 'react';
import { Header } from '@/components/organisms/Header';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

function DashboardLayoutComponent({ children }: DashboardLayoutProps) {
  return (
    <>
      {/* Header */}
      <Header onMobileMenuToggle={() => {}} />

      {/* Main Content - matches other pages structure */}
      <main style={{
        padding: '24px',
        minHeight: 'calc(100vh - 64px)',
        background: 'var(--bg-primary)'
      }}>
        {children}
      </main>
    </>
  );
}

// Memoize to prevent unnecessary re-renders
export const DashboardLayout = memo(DashboardLayoutComponent);
DashboardLayout.displayName = 'DashboardLayout';
