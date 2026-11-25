'use client';

import { useState, useEffect } from 'react';
import * as ReactDOM from 'react-dom';
import { PageHeader, PageContainer } from '@/components/molecules';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface FailedScenario {
  id: string;
  name: string;
  status: string;
  duration: number | null;
  error_message: string | null;
  stack_trace: string | null;
  tags: string[];
  feature: string | null;
  created_at: string;
  project_id: string;
  project_name: string;
  module_id: string;
  module_name: string;
}

interface FailedScenarioListResponse {
  scenarios: FailedScenario[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

interface Project {
  id: string;
  name: string;
}

interface Module {
  id: string;
  name: string;
}

interface ViewDetailsModalState {
  isOpen: boolean;
  title: string;
  content: string;
  type: 'error' | 'stacktrace';
}

export default function AIFailureAnalysisPage() {
  const [failures, setFailures] = useState<FailedScenario[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [modules, setModules] = useState<Module[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [selectedProject, setSelectedProject] = useState<string>('all');
  const [selectedModule, setSelectedModule] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalFailures, setTotalFailures] = useState(0);
  
  // AI Insights Modal state
  const [showAIInsightsModal, setShowAIInsightsModal] = useState(false);
  const [selectedScenarioForAI, setSelectedScenarioForAI] = useState<FailedScenario | null>(null);
  
  // View details modal state (error/stacktrace)
  const [viewDetailsModal, setViewDetailsModal] = useState<ViewDetailsModalState>({
    isOpen: false,
    title: '',
    content: '',
    type: 'error',
  });
  
  // State to track if component is mounted (for portal)
  const [mounted, setMounted] = useState(false);

  const pageSize = 50;

  // Set mounted to true after component mounts (for portal)
  useEffect(() => {
    setMounted(true);
  }, []);

  // Fetch projects for filter
  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/projects');
        if (!response.ok) throw new Error('Failed to fetch projects');
        const data = await response.json();
        setProjects(data.map((p: any) => ({ id: p.id, name: p.name })));
      } catch (err) {
        console.error('Error fetching projects:', err);
      }
    };
    fetchProjects();
  }, []);

  // Fetch modules for filter
  useEffect(() => {
    if (selectedProject && selectedProject !== 'all') {
      const fetchModules = async () => {
        try {
          const response = await fetch(`http://localhost:8000/api/v1/projects/${selectedProject}/modules`);
          if (!response.ok) throw new Error('Failed to fetch modules');
          const data = await response.json();
          setModules(data.map((m: any) => ({ id: m.id, name: m.name })));
        } catch (err) {
          console.error('Error fetching modules:', err);
        }
      };
      fetchModules();
    } else {
      setModules([]);
      setSelectedModule('all');
    }
  }, [selectedProject]);

  // Fetch failed scenarios
  useEffect(() => {
    const fetchFailures = async () => {
      try {
        setLoading(true);
        setError(null);

        const params = new URLSearchParams({
          page: currentPage.toString(),
          size: pageSize.toString(),
        });

        if (selectedProject && selectedProject !== 'all') {
          params.append('project_id', selectedProject);
        }
        if (selectedModule && selectedModule !== 'all') {
          params.append('module_id', selectedModule);
        }
        if (searchQuery.trim()) {
          params.append('search', searchQuery.trim());
        }

        const response = await fetch(`http://localhost:8000/api/v1/scenarios/failures?${params.toString()}`);
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: Failed to fetch failed scenarios`);
        }

        const data: FailedScenarioListResponse = await response.json();
        setFailures(data.scenarios);
        setTotalFailures(data.total);
        setTotalPages(data.pages);
      } catch (err) {
        console.error('Error fetching failures:', err);
        setError(err instanceof Error ? err.message : 'Failed to load failure data');
        setFailures([]);
      } finally {
        setLoading(false);
      }
    };

    fetchFailures();
  }, [currentPage, selectedProject, selectedModule, searchQuery]);

  const handleAIInsights = (scenario: FailedScenario) => {
    setSelectedScenarioForAI(scenario);
    setShowAIInsightsModal(true);
  };

  // Handle view details modal (error/stacktrace)
  const handleViewDetails = (content: string, type: 'error' | 'stacktrace') => {
    setViewDetailsModal({
      isOpen: true,
      title: type === 'error' ? 'Error Message' : 'Stack Trace',
      content,
      type,
    });
  };

  const formatDuration = (seconds: number | null): string => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}m ${secs}s`;
  };

  // AI Insights modal component to render in portal
  const renderAIInsightsModal = () => {
    if (!showAIInsightsModal || !selectedScenarioForAI || !mounted) return null;
    
    return ReactDOM.createPortal(
      <div 
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 999999,
        }}
        onClick={() => setShowAIInsightsModal(false)}
      >
        <div 
          style={{
            width: '100%',
            maxWidth: '32rem',
            backgroundColor: 'white',
            borderRadius: '0.5rem',
            padding: '1.5rem',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: '#111827', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <i className="fa fa-brain" style={{ color: '#8b5cf6', fontSize: '20px' }} />
              AI Insights
            </h3>
            <button
              onClick={() => setShowAIInsightsModal(false)}
              style={{
                background: 'transparent',
                border: 'none',
                fontSize: '24px',
                cursor: 'pointer',
                padding: '4px',
                lineHeight: 1,
                color: '#6b7280',
              }}
            >
              ×
            </button>
          </div>
          
          <div style={{ marginBottom: '1rem' }}>
            <p style={{ fontSize: '0.875rem', color: '#4b5563', marginBottom: '0.5rem' }}>
              Scenario: <span style={{ fontWeight: 600, color: '#111827' }}>{selectedScenarioForAI.name}</span>
            </p>
            <p style={{ fontSize: '0.75rem', color: '#6b7280' }}>
              {selectedScenarioForAI.project_name} / {selectedScenarioForAI.module_name}
            </p>
          </div>

          {/* Under Construction Message */}
          <div style={{ borderRadius: '0.5rem', border: '2px dashed #fcd34d', backgroundColor: '#fef3c7', padding: '2rem', textAlign: 'center' }}>
            <div style={{ marginBottom: '1rem' }}>
              <i className="fa fa-hard-hat" style={{ fontSize: '48px', color: '#f59e0b' }} />
            </div>
            <h4 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#78350f', marginBottom: '0.5rem' }}>
              🚧 Work Under Construction
            </h4>
            <p style={{ fontSize: '0.875rem', color: '#92400e', marginBottom: '1rem' }}>
              AI-powered failure analysis and insights are currently being developed.
            </p>
            <div style={{ fontSize: '0.75rem', color: '#a16207', backgroundColor: '#fef9c3', borderRadius: '0.25rem', padding: '0.5rem 0.75rem', display: 'inline-block' }}>
              <i className="fa fa-lightbulb" style={{ marginRight: '6px' }} />
              Coming Soon: Root cause analysis, similar failure patterns, suggested fixes, and more!
            </div>
          </div>

          <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="default"
              onClick={() => setShowAIInsightsModal(false)}
            >
              Close
            </Button>
          </div>
        </div>
      </div>,
      document.body
    );
  };

  // View details modal component to render in portal
  const renderViewDetailsModal = () => {
    if (!viewDetailsModal.isOpen || !mounted) return null;
    
    return ReactDOM.createPortal(
      <div 
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 999999,
        }}
        onClick={() => setViewDetailsModal({ isOpen: false, title: '', content: '', type: 'error' })}
      >
        <div 
          style={{
            width: '100%',
            maxWidth: '48rem',
            maxHeight: '80vh',
            backgroundColor: 'white',
            borderRadius: '0.5rem',
            padding: '1.5rem',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
            display: 'flex',
            flexDirection: 'column',
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: '#111827', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <i 
                className={viewDetailsModal.type === 'error' ? 'fas fa-exclamation-circle' : 'fas fa-code'} 
                style={{ color: viewDetailsModal.type === 'error' ? '#dc2626' : '#6b7280', fontSize: '20px' }}
              />
              {viewDetailsModal.title}
            </h3>
            <button
              onClick={() => setViewDetailsModal({ isOpen: false, title: '', content: '', type: 'error' })}
              style={{
                background: 'transparent',
                border: 'none',
                fontSize: '24px',
                cursor: 'pointer',
                padding: '4px',
                lineHeight: 1,
                color: '#6b7280',
              }}
            >
              ×
            </button>
          </div>
          
          <div 
            style={{
              flex: 1,
              overflowY: 'auto',
              backgroundColor: '#f9fafb',
              borderRadius: '0.375rem',
              padding: '1rem',
              border: '1px solid #e5e7eb',
            }}
          >
            <pre style={{ 
              margin: 0, 
              whiteSpace: 'pre-wrap', 
              wordBreak: 'break-word', 
              fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
              fontSize: '0.875rem',
              lineHeight: '1.5',
              color: '#111827',
            }}>
              {viewDetailsModal.content}
            </pre>
          </div>

          <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="default"
              onClick={() => setViewDetailsModal({ isOpen: false, title: '', content: '', type: 'error' })}
            >
              Close
            </Button>
          </div>
        </div>
      </div>,
      document.body
    );
  };

  return (
    <PageContainer>
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
            <div style={{ color: '#991b1b', fontWeight: 600, fontSize: '14px' }}>Error Loading Data</div>
            <div style={{ color: '#7f1d1d', fontSize: '13px' }}>{error}</div>
          </div>
        </div>
      )}

      {/* Header - Clean, No Extra Labels */}
      <PageHeader
        title="Failure Analysis"
        subtitle="Analyze failed test scenarios, error patterns, and diagnostics"
      />

      {/* Filters */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '16px',
          marginBottom: '20px',
          background: '#f1f5f9',
          padding: '16px',
          borderRadius: '8px',
        }}
      >
        {/* Project Dropdown */}
        <div>
          <label
            style={{
              display: 'block',
              fontSize: '13px',
              fontWeight: 600,
              color: '#0f172a',
              marginBottom: '6px',
            }}
          >
            Project
          </label>
          <select
            value={selectedProject}
            onChange={(e) => {
              setSelectedProject(e.target.value);
              setCurrentPage(1);
            }}
            style={{
              width: '100%',
              padding: '7px 10px',
              fontSize: '13px',
              border: '1px solid #e2e8f0',
              borderRadius: '6px',
              background: 'white',
              color: '#0f172a',
            }}
          >
            <option value="all">All Projects</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </div>

        {/* Module Dropdown */}
        <div>
          <label
            style={{
              display: 'block',
              fontSize: '13px',
              fontWeight: 600,
              color: '#0f172a',
              marginBottom: '6px',
            }}
          >
            Module
          </label>
          <select
            value={selectedModule}
            onChange={(e) => {
              setSelectedModule(e.target.value);
              setCurrentPage(1);
            }}
            disabled={selectedProject === 'all'}
            style={{
              width: '100%',
              padding: '7px 10px',
              fontSize: '13px',
              border: '1px solid #e2e8f0',
              borderRadius: '6px',
              background: selectedProject === 'all' ? '#f1f5f9' : 'white',
              color: '#0f172a',
              cursor: selectedProject === 'all' ? 'not-allowed' : 'pointer',
            }}
          >
            <option value="all">All Modules</option>
            {modules.map((module) => (
              <option key={module.id} value={module.id}>
                {module.name}
              </option>
            ))}
          </select>
        </div>

        {/* Search */}
        <div>
          <label
            style={{
              display: 'block',
              fontSize: '13px',
              fontWeight: 600,
              color: '#0f172a',
              marginBottom: '6px',
            }}
          >
            Search
          </label>
          <input
            type="text"
            placeholder="Search scenario name or error..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(1);
            }}
            style={{
              width: '100%',
              padding: '7px 10px',
              fontSize: '13px',
              border: '1px solid #e2e8f0',
              borderRadius: '6px',
              background: 'white',
              color: '#0f172a',
            }}
          />
        </div>
      </div>

      {/* Failures Table - Using Module Details Table Style */}
      {loading ? (
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '40px 20px',
          textAlign: 'center',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        }}>
          <i className="fa fa-spinner fa-spin" style={{ fontSize: '24px', color: '#3b82f6', marginBottom: '12px' }} />
          <div style={{ fontSize: '14px', color: '#64748b' }}>Loading failure data...</div>
        </div>
      ) : failures.length === 0 ? (
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '40px 20px',
          textAlign: 'center',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        }}>
          <i className="fa fa-check-circle" style={{ fontSize: '36px', color: '#22c55e', marginBottom: '12px' }} />
          <div style={{ fontSize: '16px', fontWeight: 600, color: '#0f172a', marginBottom: '6px' }}>
            No Failed Scenarios
          </div>
          <div style={{ fontSize: '13px', color: '#64748b' }}>
            {searchQuery || selectedProject !== 'all' || selectedModule !== 'all'
              ? 'No failures match your current filters.'
              : 'All tests are passing! Great job!'}
          </div>
        </div>
      ) : (
        <div className="mb-6">
          <div className="rounded-lg border border-border bg-card shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr style={{ backgroundColor: '#1e293b' }}>
                    <th className="px-3 py-2 text-left text-xs font-semibold text-white">
                      Scenario
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-semibold text-white">
                      Tags
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-semibold text-white">
                      Duration
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-semibold text-white">
                      Status
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-semibold text-white">
                      Feature
                    </th>
                    <th className="px-3 py-2 text-center text-xs font-semibold text-white">
                      Error
                    </th>
                    <th className="px-3 py-2 text-center text-xs font-semibold text-white">
                      Stack Trace
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-semibold text-white">
                      AI Insights
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {failures.map((scenario) => (
                    <tr
                      key={scenario.id}
                      className="border-b border-border transition-colors hover:bg-muted/50"
                    >
                      <td className="px-3 py-2 text-xs text-foreground">
                        <div>{scenario.name}</div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {scenario.project_name} / {scenario.module_name}
                        </div>
                      </td>
                      <td className="px-3 py-2 text-xs text-muted-foreground">
                        {scenario.tags && scenario.tags.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {scenario.tags.slice(0, 2).map((tag, idx) => (
                              <span
                                key={idx}
                                className="inline-block rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800"
                              >
                                {tag}
                              </span>
                            ))}
                            {scenario.tags.length > 2 && (
                              <span className="text-xs text-muted-foreground">+{scenario.tags.length - 2}</span>
                            )}
                          </div>
                        ) : (
                          "-"
                        )}
                      </td>
                      <td className="px-3 py-2 text-xs text-foreground">
                        {formatDuration(scenario.duration)}
                      </td>
                      <td className="px-3 py-2 text-xs">
                        <Badge 
                          variant="error"
                          style={{ fontSize: '10px', padding: '2px 6px' }}
                        >
                          FAILED
                        </Badge>
                      </td>
                      <td className="px-3 py-2 text-xs text-muted-foreground">
                        {scenario.feature || "-"}
                      </td>
                      <td className="px-3 py-2 text-center text-xs">
                        {scenario.error_message ? (
                          <button
                            onClick={() => handleViewDetails(scenario.error_message!, 'error')}
                            style={{
                              background: 'transparent',
                              border: 'none',
                              cursor: 'pointer',
                              padding: '4px',
                            }}
                          >
                            <i 
                              className="fas fa-eye cursor-pointer text-red-600 hover:text-red-700" 
                              style={{ fontSize: '14px' }}
                            />
                          </button>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-center text-xs">
                        {scenario.stack_trace ? (
                          <button
                            onClick={() => handleViewDetails(scenario.stack_trace!, 'stacktrace')}
                            style={{
                              background: 'transparent',
                              border: 'none',
                              cursor: 'pointer',
                              padding: '4px',
                            }}
                          >
                            <i 
                              className="fas fa-eye cursor-pointer text-gray-600 hover:text-gray-700" 
                              style={{ fontSize: '14px' }}
                            />
                          </button>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-xs">
                        <button
                          onClick={() => handleAIInsights(scenario)}
                          style={{
                            padding: '4px 8px',
                            fontSize: '11px',
                            fontWeight: 500,
                            color: 'white',
                            background: '#495057',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            transition: 'background 0.2s ease',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = '#343a40';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = '#495057';
                          }}
                        >
                          <i className="fa fa-brain" />
                          AI Insights
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '12px 0',
              marginTop: '16px',
            }}>
              <div style={{ fontSize: '13px', color: '#64748b' }}>
                {((currentPage - 1) * pageSize) + 1}-{Math.min(currentPage * pageSize, totalFailures)} of {totalFailures}
              </div>
              <div style={{ display: 'flex', gap: '6px' }}>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  style={{ fontSize: '13px' }}
                >
                  Previous
                </Button>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '0 8px' }}>
                  <span style={{ fontSize: '13px', color: '#64748b' }}>Page {currentPage} of {totalPages}</span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  style={{ fontSize: '13px' }}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Render modals via portal */}
      {renderAIInsightsModal()}
      {renderViewDetailsModal()}
    </PageContainer>
  );
}

