"use client";

import React, { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { apiService, ApiError } from '@/services/api';
import { PageHeader, PageContainer } from '@/components/molecules';

// Backend API response structure (matches ProjectOverviewResponse from backend)
interface BackendProject {
  id: string; // UUID from backend
  name: string;
  description?: string;
  repository_url?: string;
  owner: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  // Aggregated metrics from ProjectOverviewResponse
  modules: number;
  total_tests: number;
  pass_rate: number;
  last_status?: string;
  last_run?: string;
}

// Frontend display structure
interface Project {
  id: string; // Changed from number to string (UUID)
  name: string;
  status: 'active' | 'inactive';
  passRate: number;
  moduleCount: number;
  totalTests: number;
  defects: number;
  owner: string;
  lastRun: string;
}

// Mock data removed - frontend now uses ONLY real backend data

const ProjectsPage: React.FC = () => {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const [_loading, setLoading] = useState(true); // Prefixed with _ to indicate intentionally unused
  const [error, setError] = useState<string | null>(null);

  // Fetch projects from API
  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch from real API (no fallback to mock data)
      const apiProjects = await apiService.projects.getAll() as unknown as BackendProject[];
      
      console.log('API Projects Response:', apiProjects); // Debug log
      
      // Map API response to match our frontend structure
      const mappedProjects: Project[] = apiProjects.map(p => ({
        id: p.id, // Now UUID string
        name: p.name,
        status: p.is_active ? 'active' : 'inactive', // Use is_active from backend
        passRate: p.pass_rate || 0,
        moduleCount: p.modules || 0, // Use 'modules' from ProjectOverviewResponse
        totalTests: p.total_tests || 0, // Use 'total_tests' from ProjectOverviewResponse
        defects: 0, // TODO: Add from defects API
        owner: p.owner || 'Unknown',
        lastRun: p.last_run ? new Date(p.last_run).toLocaleString('en-US', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit'
        }) : 'Never'
      }));
      
      console.log('Mapped Projects:', mappedProjects); // Debug log
      setProjects(mappedProjects);
      
      const now = new Date();
      setLastUpdated(now.toLocaleString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }));
    } catch (err) {
      console.error('Failed to fetch projects:', err);
      
      // Show error but don't fallback to mock data
      if (err instanceof ApiError) {
        setError(`API Error (${err.status}): ${err.message}`);
      } else {
        setError('Failed to connect to backend API. Please check if the backend is running.');
      }
      
      // Set empty array instead of mock data
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  // Sort projects: active projects first, then inactive; alphabetically by name within each group
  const sortedProjects = useMemo(() => {
    return [...projects].sort((a, b) => {
      if (a.status !== b.status) {
        return a.status === 'active' ? -1 : 1;
      }
      return a.name.localeCompare(b.name, undefined, { sensitivity: 'base' });
    });
  }, [projects]);

  // Calculate summary metrics
  const activeProjectsCount = projects.filter(p => p.status === 'active').length;
  const totalTestCases = projects.reduce((sum, p) => sum + p.totalTests, 0);

  // Get pass rate color based on percentage
  const getPassRateColor = (rate: number): string => {
    if (rate >= 90) return '#10b981';
    if (rate >= 70) return '#f59e0b';
    return '#ef4444';
  };

  // Handle refresh
  const handleRefresh = () => {
    fetchProjects(); // Refetch data from API
  };

  // Navigation handlers
  const handleSummaryClick = (projectId: string) => {
    const project = projects.find(p => p.id === projectId);
    const projectName = project?.name || 'Project';
    router.push(`/execution-summary?project=${projectId}&projectName=${encodeURIComponent(projectName)}`);
  };

  const handleModulesClick = (projectId: string) => {
    router.push(`/module-details?project=${projectId}`);
  };

  const handleTrendsClick = (projectId: string) => {
    router.push(`/trends?project=${projectId}`);
  };

  const handleSettingsClick = (projectId: string) => {
    router.push(`/settings?project=${projectId}`);
  };

  return (
    <PageContainer>
      <style jsx global>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }

        .pulse-dot {
          animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }

        .summary-card {
          transition: all 0.25s ease-in-out;
        }

        .summary-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 10px 20px rgba(0, 0, 0, 0.12);
        }

        .project-card {
          transition: all 0.25s ease-in-out;
        }

        .project-card:hover {
          transform: translateY(-5px) scale(1.01);
          box-shadow: 0 10px 20px rgba(0, 0, 0, 0.12);
        }

        .kpi-mini-card {
          transition: all 0.25s ease-in-out;
        }

        .kpi-mini-card:hover {
          transform: translateY(-3px);
          box-shadow: 0 6px 14px rgba(0, 0, 0, 0.1);
        }
      `}</style>

      {/* Error Banner */}
      {error && (
        <div style={{
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '8px',
          padding: '12px 16px',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <i className="fas fa-exclamation-circle" style={{ color: '#ef4444', fontSize: '18px' }} />
          <div>
            <div style={{ color: '#991b1b', fontWeight: 600, fontSize: '14px' }}>Connection Warning</div>
            <div style={{ color: '#7f1d1d', fontSize: '13px' }}>{error}</div>
          </div>
        </div>
      )}

      {/* Page Header */}
      <PageHeader
        title="Projects"
        subtitle="Monitor and manage your automation testing projects"
        showBackButton={false}
        rightContent={
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            backgroundColor: '#f1f5f9',
            padding: '8px 16px',
            borderRadius: '6px'
          }}>
            <i className="fas fa-sync-alt" style={{
              fontSize: '11px',
              color: '#64748b',
              marginRight: '8px',
              cursor: 'pointer'
            }} onClick={handleRefresh}></i>
            <span style={{
              fontSize: '11px',
              color: '#64748b'
            }}>
              Last updated: {lastUpdated}
            </span>
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-6">
        {/* Card 1: Active Projects */}
        <div className="summary-card" style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '12px',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <div style={{
              fontSize: '22px',
              fontWeight: 700,
              color: '#0f172a',
              marginBottom: '4px'
            }}>
              {activeProjectsCount}
            </div>
            <div style={{
              fontSize: '12px',
              color: '#64748b'
            }}>
              Active Projects
            </div>
          </div>
          <i className="fas fa-check-circle" style={{
            fontSize: '22px',
            color: '#28a745'
          }}></i>
        </div>

        {/* Card 2: Total Test Cases */}
        <div className="summary-card" style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '12px',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <div style={{
              fontSize: '22px',
              fontWeight: 700,
              color: '#2563eb',
              marginBottom: '4px'
            }}>
              {totalTestCases.toLocaleString()}
            </div>
            <div style={{
              fontSize: '12px',
              color: '#64748b'
            }}>
              Total Test Cases
            </div>
          </div>
          <i className="fas fa-vials" style={{
            fontSize: '22px',
            color: '#17a2b8'
          }}></i>
        </div>
      </div>

      {/* Section Heading */}
      <h2 style={{
        fontSize: '16px',
        fontWeight: 600,
        color: '#0f172a',
        margin: '20px 0'
      }}>
        All projects
      </h2>

      {/* Project Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {sortedProjects.map((project) => (
          <div key={project.id} className="project-card" style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            overflow: 'hidden',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
          }}>
            {/* Card Header */}
            <div style={{
              padding: '10px 12px',
              backgroundColor: '#f9fafb',
              borderBottom: '1px solid #e2e8f0',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <i className="fas fa-cube" style={{
                  fontSize: '14px',
                  color: '#6366f1',
                  marginRight: '8px'
                }}></i>
                <span style={{
                  fontSize: '14px',
                  fontWeight: 700,
                  color: '#0f172a',
                  letterSpacing: '-0.2px'
                }}>
                  {project.name}
                </span>
              </div>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
                <div className="pulse-dot" style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: project.status === 'active' ? '#10b981' : '#94a3b8',
                  boxShadow: `0 0 8px ${project.status === 'active' ? '#10b981' : '#94a3b8'}`
                }}></div>
                <span style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  color: project.status === 'active' ? '#10b981' : '#94a3b8',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px'
                }}>
                  {project.status}
                </span>
              </div>
            </div>

            {/* KPI Mini-Cards Row */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: '8px',
              padding: '10px'
            }}>
              {/* Pass Rate */}
              <div className="kpi-mini-card" style={{
                padding: '8px',
                borderRadius: '8px',
                border: '1px solid #e2e8f0',
                boxShadow: '0 2px 6px rgba(0, 0, 0, 0.05)',
                textAlign: 'center'
              }}>
                <i className="fas fa-chart-pie" style={{
                  fontSize: '16px',
                  color: getPassRateColor(project.passRate),
                  display: 'block',
                  marginBottom: '6px'
                }}></i>
                <div style={{
                  fontSize: '16px',
                  fontWeight: 700,
                  color: getPassRateColor(project.passRate),
                  marginBottom: '3px'
                }}>
                  {project.passRate}%
                </div>
                <div style={{
                  fontSize: '11px',
                  color: '#64748b'
                }}>
                  Pass Rate
                </div>
              </div>

              {/* Modules */}
              <div className="kpi-mini-card" style={{
                padding: '8px',
                borderRadius: '8px',
                border: '1px solid #e2e8f0',
                boxShadow: '0 2px 6px rgba(0, 0, 0, 0.05)',
                textAlign: 'center'
              }}>
                <i className="fas fa-cubes" style={{
                  fontSize: '16px',
                  color: '#6366f1',
                  display: 'block',
                  marginBottom: '6px'
                }}></i>
                <div style={{
                  fontSize: '16px',
                  fontWeight: 700,
                  color: '#0f172a',
                  marginBottom: '3px'
                }}>
                  {project.moduleCount}
                </div>
                <div style={{
                  fontSize: '11px',
                  color: '#64748b'
                }}>
                  Modules
                </div>
              </div>

              {/* Total Tests */}
              <div className="kpi-mini-card" style={{
                padding: '8px',
                borderRadius: '8px',
                border: '1px solid #e2e8f0',
                boxShadow: '0 2px 6px rgba(0, 0, 0, 0.05)',
                textAlign: 'center'
              }}>
                <i className="fas fa-vials" style={{
                  fontSize: '16px',
                  color: '#6366f1',
                  display: 'block',
                  marginBottom: '6px'
                }}></i>
                <div style={{
                  fontSize: '16px',
                  fontWeight: 700,
                  color: '#0f172a',
                  marginBottom: '3px'
                }}>
                  {project.totalTests.toLocaleString()}
                </div>
                <div style={{
                  fontSize: '11px',
                  color: '#64748b'
                }}>
                  Total Tests
                </div>
              </div>

              {/* Defects */}
              <div className="kpi-mini-card" style={{
                padding: '8px',
                borderRadius: '8px',
                border: '1px solid #e2e8f0',
                boxShadow: '0 2px 6px rgba(0, 0, 0, 0.05)',
                textAlign: 'center'
              }}>
                <i className="fas fa-bug" style={{
                  fontSize: '16px',
                  color: '#ef4444',
                  display: 'block',
                  marginBottom: '6px'
                }}></i>
                <div style={{
                  fontSize: '16px',
                  fontWeight: 700,
                  color: '#ef4444',
                  marginBottom: '3px'
                }}>
                  {project.defects}
                </div>
                <div style={{
                  fontSize: '11px',
                  color: '#64748b'
                }}>
                  Defects
                </div>
              </div>
            </div>

            {/* Metadata Row */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              padding: '0 10px',
              marginBottom: '8px'
            }}>
              <div>
                <div style={{
                  fontSize: '10px',
                  color: '#64748b',
                  marginBottom: '2px'
                }}>
                  Owner
                </div>
                <div style={{
                  fontSize: '11px',
                  color: '#64748b'
                }}>
                  {project.owner}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{
                  fontSize: '10px',
                  color: '#64748b',
                  marginBottom: '2px'
                }}>
                  Last Run
                </div>
                <div style={{
                  fontSize: '11px',
                  color: '#64748b'
                }}>
                  {project.lastRun}
                </div>
              </div>
            </div>

            {/* Action Buttons Row */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: '6px',
              padding: '8px 10px',
              borderTop: '1px solid #f1f5f9',
              backgroundColor: '#f9fafb'
            }}>
              <button
                onClick={() => handleSummaryClick(project.id)}
                style={{
                  display: 'flex',
                  flexDirection: 'row',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '4px',
                  padding: '6px 8px',
                  border: '1px solid #3b82f6',
                  backgroundColor: 'transparent',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#3b82f6';
                  const icon = e.currentTarget.querySelector('i');
                  const span = e.currentTarget.querySelector('span');
                  if (icon) (icon as HTMLElement).style.color = 'white';
                  if (span) (span as HTMLElement).style.color = 'white';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  const icon = e.currentTarget.querySelector('i');
                  const span = e.currentTarget.querySelector('span');
                  if (icon) (icon as HTMLElement).style.color = '#3b82f6';
                  if (span) (span as HTMLElement).style.color = '#3b82f6';
                }}
              >
                <i className="fas fa-chart-line" style={{
                  fontSize: '11px',
                  color: '#3b82f6',
                  flexShrink: 0
                }}></i>
                <span style={{
                  fontSize: '9px',
                  color: '#3b82f6',
                  fontWeight: 500
                }}>
                  Summary
                </span>
              </button>

              <button
                onClick={() => handleModulesClick(project.id)}
                style={{
                  display: 'flex',
                  flexDirection: 'row',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '4px',
                  padding: '6px 8px',
                  border: '1px solid #6c757d',
                  backgroundColor: 'transparent',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#6c757d';
                  const icon = e.currentTarget.querySelector('i');
                  const span = e.currentTarget.querySelector('span');
                  if (icon) (icon as HTMLElement).style.color = 'white';
                  if (span) (span as HTMLElement).style.color = 'white';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  const icon = e.currentTarget.querySelector('i');
                  const span = e.currentTarget.querySelector('span');
                  if (icon) (icon as HTMLElement).style.color = '#6c757d';
                  if (span) (span as HTMLElement).style.color = '#6c757d';
                }}
              >
                <i className="fas fa-cog" style={{
                  fontSize: '11px',
                  color: '#6c757d',
                  flexShrink: 0
                }}></i>
                <span style={{
                  fontSize: '9px',
                  color: '#6c757d',
                  fontWeight: 500
                }}>
                  Modules
                </span>
              </button>

              <button
                onClick={() => handleTrendsClick(project.id)}
                style={{
                  display: 'flex',
                  flexDirection: 'row',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '4px',
                  padding: '6px 8px',
                  border: '1px solid #17a2b8',
                  backgroundColor: 'transparent',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#17a2b8';
                  const icon = e.currentTarget.querySelector('i');
                  const span = e.currentTarget.querySelector('span');
                  if (icon) (icon as HTMLElement).style.color = 'white';
                  if (span) (span as HTMLElement).style.color = 'white';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  const icon = e.currentTarget.querySelector('i');
                  const span = e.currentTarget.querySelector('span');
                  if (icon) (icon as HTMLElement).style.color = '#17a2b8';
                  if (span) (span as HTMLElement).style.color = '#17a2b8';
                }}
              >
                <i className="fas fa-chart-bar" style={{
                  fontSize: '11px',
                  color: '#17a2b8',
                  flexShrink: 0
                }}></i>
                <span style={{
                  fontSize: '9px',
                  color: '#17a2b8',
                  fontWeight: 500
                }}>
                  Trends
                </span>
              </button>

              <button
                onClick={() => handleSettingsClick(project.id)}
                style={{
                  display: 'flex',
                  flexDirection: 'row',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '4px',
                  padding: '6px 8px',
                  border: '1px solid #ffc107',
                  backgroundColor: 'transparent',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#ffc107';
                  const icon = e.currentTarget.querySelector('i');
                  const span = e.currentTarget.querySelector('span');
                  if (icon) (icon as HTMLElement).style.color = 'white';
                  if (span) (span as HTMLElement).style.color = 'white';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  const icon = e.currentTarget.querySelector('i');
                  const span = e.currentTarget.querySelector('span');
                  if (icon) (icon as HTMLElement).style.color = '#ffc107';
                  if (span) (span as HTMLElement).style.color = '#ffc107';
                }}
              >
                <i className="fas fa-gear" style={{
                  fontSize: '11px',
                  color: '#ffc107',
                  flexShrink: 0
                }}></i>
                <span style={{
                  fontSize: '9px',
                  color: '#ffc107',
                  fontWeight: 500
                }}>
                  Settings
                </span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </PageContainer>
  );
};

export default ProjectsPage;
