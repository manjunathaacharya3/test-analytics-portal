'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiService, Defect, Project } from '@/services/api';

// Type for UI defect (mapped from backend)
interface UIDefect {
  id: string;
  title: string;
  severity: string;
  priority: string;
  status: string;
  assignedTo: string;
  reportedBy: string;
  created: string;
  updated: string;
  module: string;
  description: string;
  project_id?: number;
  scenario_id?: number;
}

const severityColors: Record<string, string> = {
  critical: '#b91c1c',
  high: '#f97316',
  medium: '#facc15',
  low: '#22c55e',
};

const statusColors: Record<string, string> = {
  open: '#dc2626',
  in_progress: '#eab308',
  fixed: '#16a34a',
  closed: '#6b7280',
};

// Helper function to capitalize first letter
const capitalize = (str: string) => {
  return str.charAt(0).toUpperCase() + str.slice(1).replace('_', ' ');
};

export default function DefectManagementPage() {
  const router = useRouter();
  const [selectedProject, setSelectedProject] = useState('All');
  const [selectedStatus, setSelectedStatus] = useState('All');
  const [selectedDefect, setSelectedDefect] = useState<UIDefect | null>(null);
  
  // State for API data
  const [defects, setDefects] = useState<UIDefect[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch data on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        console.log('Fetching defects and projects from backend...');
        
        // Fetch defects and projects in parallel
        const [defectsData, projectsData] = await Promise.all([
          apiService.defects.getAll(),
          apiService.projects.getAll(),
        ]);
        
        console.log('Backend defects response:', defectsData);
        console.log('Backend projects response:', projectsData);
        
        // Map backend defects to UI format - ensure defectsData is an array
        const defectsArray = Array.isArray(defectsData) ? defectsData : [];
        const mappedDefects: UIDefect[] = defectsArray.map((defect: Defect) => ({
          id: `DEF-${defect.id.toString().padStart(3, '0')}`,
          title: defect.title,
          severity: capitalize(defect.severity),
          priority: 'High', // Backend doesn't have priority field, using default
          status: defect.status.split('_').map(capitalize).join(' '),
          assignedTo: defect.assignee || 'Unassigned',
          reportedBy: 'System', // Backend doesn't have reportedBy field
          created: defect.created_at,
          updated: defect.updated_at || defect.created_at,
          module: 'General', // Backend doesn't have module field
          description: defect.description || 'No description provided',
          project_id: defect.project_id,
          scenario_id: defect.scenario_id,
        }));
        
        console.log('Mapped defects for UI:', mappedDefects);
        
        setDefects(mappedDefects);
        setProjects(projectsData);
      } catch (err: any) {
        console.error('Error fetching data:', err);
        setError(err.message || 'Failed to fetch data from backend');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  // Filter defects based on selected filters
  const filteredDefects = defects.filter((defect) => {
    if (selectedProject !== 'All' && defect.project_id?.toString() !== selectedProject) return false;
    if (selectedStatus !== 'All' && defect.status !== selectedStatus) return false;
    return true;
  });

  // Calculate summary stats
  const totalDefects = filteredDefects.length;
  const openDefects = filteredDefects.filter((d) => d.status === 'Open').length;
  const inProgressDefects = filteredDefects.filter((d) => d.status === 'In Progress').length;
  const fixedDefects = filteredDefects.filter((d) => d.status === 'Fixed').length;

  // Loading state
  if (loading) {
    return (
      <div style={{ padding: '30px', background: 'var(--bg-primary)', minHeight: '100vh' }}>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
          <div style={{ textAlign: 'center' }}>
            <i className="fa fa-spinner fa-spin" style={{ fontSize: '48px', color: '#7c3aed', marginBottom: '16px' }}></i>
            <div style={{ fontSize: '18px', color: 'var(--text-secondary)' }}>Loading defects...</div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div style={{ padding: '30px', background: 'var(--bg-primary)', minHeight: '100vh' }}>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
          <div style={{ textAlign: 'center', maxWidth: '500px' }}>
            <i className="fa fa-exclamation-triangle" style={{ fontSize: '48px', color: '#dc2626', marginBottom: '16px' }}></i>
            <div style={{ fontSize: '18px', color: 'var(--text-primary)', fontWeight: 600, marginBottom: '8px' }}>Error Loading Data</div>
            <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>{error}</div>
            <button
              onClick={() => window.location.reload()}
              style={{
                marginTop: '20px',
                padding: '10px 20px',
                fontSize: '14px',
                fontWeight: 500,
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                background: '#7c3aed',
                color: 'white',
                transition: 'background 0.2s ease',
              }}
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '18px', background: 'var(--bg-primary)', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ marginBottom: '18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {/* Title */}
        <h1
          style={{
            fontSize: '20px',
            fontWeight: 700,
            color: 'var(--text-primary)',
            margin: 0,
          }}
        >
          Defect Management
        </h1>
        
        {/* Back Button */}
        <button
          onClick={() => router.push('/projects')}
          style={{
            background: '#374151',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            padding: '5px 10px',
            fontSize: '12px',
            fontWeight: 500,
            cursor: 'pointer',
            transition: 'background 0.2s ease',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = '#111827')}
          onMouseLeave={(e) => (e.currentTarget.style.background = '#374151')}
        >
          ← Back to Projects
        </button>
      </div>

      {/* Filters */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '12px',
          marginBottom: '15px',
          background: 'var(--bg-secondary)',
          padding: '12px',
          borderRadius: '6px',
        }}
      >
        {/* Project Dropdown */}
        <div>
          <label
            style={{
              display: 'block',
              fontSize: '11px',
              fontWeight: 500,
              color: 'var(--text-secondary)',
              marginBottom: '5px',
            }}
          >
            Project
          </label>
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            style={{
              width: '100%',
              padding: '6px 8px',
              fontSize: '11px',
              border: '1px solid #e2e8f0',
              borderRadius: '4px',
              background: 'white',
              color: 'var(--text-primary)',
              height: '36px',
            }}
          >
            <option value="All">All Projects</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </div>

        {/* Status Dropdown */}
        <div>
          <label
            style={{
              display: 'block',
              fontSize: '11px',
              fontWeight: 500,
              color: 'var(--text-secondary)',
              marginBottom: '5px',
            }}
          >
            Status
          </label>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            style={{
              width: '100%',
              padding: '6px 8px',
              fontSize: '11px',
              border: '1px solid #e2e8f0',
              borderRadius: '4px',
              background: 'white',
              color: 'var(--text-primary)',
              height: '36px',
            }}
          >
            <option value="All">All</option>
            <option value="Open">Open</option>
            <option value="In Progress">In Progress</option>
            <option value="Fixed">Fixed</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '12px',
          marginBottom: '15px',
        }}
      >
        {/* Total Defects */}
        <div
          style={{
            background: 'white',
            borderRadius: '8px',
            padding: '12px',
            boxShadow: 'var(--shadow-demo-md)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{ fontSize: '20px', fontWeight: 700, color: '#7c3aed' }}>{totalDefects}</div>
            <div style={{ fontSize: '10px', color: 'var(--text-secondary)', marginTop: '2px' }}>Total</div>
          </div>
          <i className="fa fa-layer-group" style={{ fontSize: '20px', color: '#7c3aed' }}></i>
        </div>

        {/* Open Defects */}
        <div
          style={{
            background: 'white',
            borderRadius: '8px',
            padding: '12px',
            boxShadow: 'var(--shadow-demo-md)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{ fontSize: '20px', fontWeight: 700, color: '#dc2626' }}>{openDefects}</div>
            <div style={{ fontSize: '10px', color: 'var(--text-secondary)', marginTop: '2px' }}>Open</div>
          </div>
          <i className="fa fa-exclamation-circle" style={{ fontSize: '20px', color: '#dc2626' }}></i>
        </div>

        {/* In Progress Defects */}
        <div
          style={{
            background: 'white',
            borderRadius: '8px',
            padding: '12px',
            boxShadow: 'var(--shadow-demo-md)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{ fontSize: '20px', fontWeight: 700, color: '#eab308' }}>{inProgressDefects}</div>
            <div style={{ fontSize: '10px', color: 'var(--text-secondary)', marginTop: '2px' }}>In Progress</div>
          </div>
          <i className="fa fa-spinner" style={{ fontSize: '20px', color: '#eab308' }}></i>
        </div>

        {/* Fixed Defects */}
        <div
          style={{
            background: 'white',
            borderRadius: '8px',
            padding: '12px',
            boxShadow: 'var(--shadow-demo-md)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{ fontSize: '20px', fontWeight: 700, color: '#16a34a' }}>{fixedDefects}</div>
            <div style={{ fontSize: '10px', color: 'var(--text-secondary)', marginTop: '2px' }}>Fixed</div>
          </div>
          <i className="fa fa-check-circle" style={{ fontSize: '20px', color: '#16a34a' }}></i>
        </div>
      </div>

      {/* Main Content Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: selectedDefect ? '1fr 1fr' : '1fr',
          gap: '12px',
        }}
      >
        {/* Defect List Table */}
        <div
          style={{
            background: 'white',
            borderRadius: '8px',
            overflow: 'hidden',
            boxShadow: 'var(--shadow-demo-md)',
          }}
        >
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#1e293b' }}>
                  <th
                    style={{
                      padding: '7px',
                      color: 'white',
                      fontWeight: 'bold',
                      textAlign: 'left',
                      fontSize: '10px',
                    }}
                  >
                    ID
                  </th>
                  <th
                    style={{
                      padding: '7px',
                      color: 'white',
                      fontWeight: 'bold',
                      textAlign: 'left',
                      fontSize: '10px',
                    }}
                  >
                    Title
                  </th>
                  <th
                    style={{
                      padding: '7px',
                      color: 'white',
                      fontWeight: 'bold',
                      textAlign: 'center',
                      fontSize: '10px',
                    }}
                  >
                    Severity
                  </th>
                  <th
                    style={{
                      padding: '7px',
                      color: 'white',
                      fontWeight: 'bold',
                      textAlign: 'center',
                      fontSize: '10px',
                    }}
                  >
                    Priority
                  </th>
                  <th
                    style={{
                      padding: '7px',
                      color: 'white',
                      fontWeight: 'bold',
                      textAlign: 'center',
                      fontSize: '10px',
                    }}
                  >
                    Status
                  </th>
                  <th
                    style={{
                      padding: '7px',
                      color: 'white',
                      fontWeight: 'bold',
                      textAlign: 'left',
                      fontSize: '10px',
                    }}
                  >
                    Assigned To
                  </th>
                  <th
                    style={{
                      padding: '7px',
                      color: 'white',
                      fontWeight: 'bold',
                      textAlign: 'center',
                      fontSize: '10px',
                    }}
                  >
                    Created
                  </th>
                  <th
                    style={{
                      padding: '7px',
                      color: 'white',
                      fontWeight: 'bold',
                      textAlign: 'left',
                      fontSize: '10px',
                    }}
                  >
                    Module
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredDefects.length === 0 ? (
                  <tr>
                    <td colSpan={8} style={{ padding: '40px', textAlign: 'center' }}>
                      <div style={{ color: 'var(--text-secondary)' }}>
                        <i className="fa fa-inbox" style={{ fontSize: '48px', marginBottom: '16px', display: 'block', opacity: 0.5 }}></i>
                        <div style={{ fontSize: '16px', fontWeight: 500 }}>No defects found</div>
                        <div style={{ fontSize: '14px', marginTop: '8px' }}>Try adjusting your filters or create a new defect</div>
                      </div>
                    </td>
                  </tr>
                ) : (
                  filteredDefects.map((defect) => {
                  const isSelected = selectedDefect?.id === defect.id;
                  const rowBg =
                    defect.status === 'Open'
                      ? '#fef2f2'
                      : defect.status === 'Fixed'
                      ? '#ecfdf5'
                      : 'white';

                  return (
                    <tr
                      key={defect.id}
                      onClick={() => setSelectedDefect(defect)}
                      style={{
                        background: isSelected ? '#e0e7ff' : rowBg,
                        cursor: 'pointer',
                        transition: 'background 0.2s ease',
                      }}
                      onMouseEnter={(e) => {
                        if (!isSelected) {
                          e.currentTarget.style.background = '#f1f5f9';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!isSelected) {
                          e.currentTarget.style.background = rowBg;
                        }
                      }}
                    >
                      <td
                        style={{
                          padding: '7px',
                          borderBottom: '1px solid #e2e8f0',
                          fontSize: '10px',
                          fontWeight: 600,
                          color: 'var(--text-primary)',
                        }}
                      >
                        {defect.id}
                      </td>
                      <td
                        style={{
                          padding: '7px',
                          borderBottom: '1px solid #e2e8f0',
                          fontSize: '10px',
                          color: 'var(--text-primary)',
                        }}
                      >
                        {defect.title}
                      </td>
                      <td
                        style={{
                          padding: '7px',
                          borderBottom: '1px solid #e2e8f0',
                          fontSize: '10px',
                          textAlign: 'center',
                        }}
                      >
                        <span
                          style={{
                            padding: '3px 6px',
                            borderRadius: '3px',
                            fontSize: '9px',
                            fontWeight: 600,
                            color: 'white',
                            background: severityColors[defect.severity.toLowerCase()],
                          }}
                        >
                          {defect.severity}
                        </span>
                      </td>
                      <td
                        style={{
                          padding: '7px',
                          borderBottom: '1px solid #e2e8f0',
                          fontSize: '10px',
                          textAlign: 'center',
                          color: 'var(--text-primary)',
                        }}
                      >
                        {defect.priority}
                      </td>
                      <td
                        style={{
                          padding: '7px',
                          borderBottom: '1px solid #e2e8f0',
                          fontSize: '10px',
                          textAlign: 'center',
                        }}
                      >
                        <span
                          style={{
                            padding: '3px 6px',
                            borderRadius: '3px',
                            fontSize: '9px',
                            fontWeight: 600,
                            color: 'white',
                            background: statusColors[defect.status.toLowerCase().replace(' ', '_')],
                          }}
                        >
                          {defect.status}
                        </span>
                      </td>
                      <td
                        style={{
                          padding: '7px',
                          borderBottom: '1px solid #e2e8f0',
                          fontSize: '10px',
                          color: 'var(--text-primary)',
                        }}
                      >
                        {defect.assignedTo}
                      </td>
                      <td
                        style={{
                          padding: '7px',
                          borderBottom: '1px solid #e2e8f0',
                          fontSize: '10px',
                          textAlign: 'center',
                          color: 'var(--text-secondary)',
                        }}
                      >
                        {new Date(defect.created).toLocaleDateString()}
                      </td>
                      <td
                        style={{
                          padding: '7px',
                          borderBottom: '1px solid #e2e8f0',
                          fontSize: '10px',
                          color: 'var(--text-primary)',
                        }}
                      >
                        {defect.module}
                      </td>
                    </tr>
                  );
                })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Defect Details Card */}
        {selectedDefect && (
          <div
            style={{
              background: 'white',
              borderRadius: '8px',
              padding: '12px',
              boxShadow: 'var(--shadow-demo-md)',
            }}
          >
            {/* Header */}
            <div style={{ marginBottom: '12px', borderBottom: '2px solid #e2e8f0', paddingBottom: '9px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '5px' }}>
                <i className="fa fa-bug" style={{ fontSize: '16px', color: '#dc2626' }}></i>
                <h2
                  style={{
                    fontSize: '14px',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    margin: 0,
                  }}
                >
                  {selectedDefect.id}: {selectedDefect.title}
                </h2>
              </div>
            </div>

            {/* Details Grid */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '12px',
                marginBottom: '12px',
              }}
            >
              {/* Left Column */}
              <div>
                <div style={{ marginBottom: '9px' }}>
                  <div style={{ fontSize: '9px', color: 'var(--text-secondary)', marginBottom: '3px' }}>
                    Severity
                  </div>
                  <span
                    style={{
                      padding: '3px 6px',
                      borderRadius: '3px',
                      fontSize: '9px',
                      fontWeight: 600,
                      color: 'white',
                      background: severityColors[selectedDefect.severity.toLowerCase()],
                    }}
                  >
                    {selectedDefect.severity}
                  </span>
                </div>
                <div style={{ marginBottom: '9px' }}>
                  <div style={{ fontSize: '9px', color: 'var(--text-secondary)', marginBottom: '3px' }}>
                    Priority
                  </div>
                  <div style={{ fontSize: '10px', color: 'var(--text-primary)', fontWeight: 600 }}>
                    {selectedDefect.priority}
                  </div>
                </div>
                <div style={{ marginBottom: '9px' }}>
                  <div style={{ fontSize: '9px', color: 'var(--text-secondary)', marginBottom: '3px' }}>
                    Status
                  </div>
                  <span
                    style={{
                      padding: '3px 6px',
                      borderRadius: '3px',
                      fontSize: '9px',
                      fontWeight: 600,
                      color: 'white',
                      background: statusColors[selectedDefect.status.toLowerCase().replace(' ', '_')],
                    }}
                  >
                    {selectedDefect.status}
                  </span>
                </div>
                <div style={{ marginBottom: '9px' }}>
                  <div style={{ fontSize: '9px', color: 'var(--text-secondary)', marginBottom: '3px' }}>
                    Module
                  </div>
                  <div style={{ fontSize: '10px', color: 'var(--text-primary)', fontWeight: 600 }}>
                    {selectedDefect.module}
                  </div>
                </div>
              </div>

              {/* Right Column */}
              <div>
                <div style={{ marginBottom: '9px' }}>
                  <div style={{ fontSize: '9px', color: 'var(--text-secondary)', marginBottom: '3px' }}>
                    Assigned To
                  </div>
                  <div style={{ fontSize: '10px', color: 'var(--text-primary)', fontWeight: 600 }}>
                    {selectedDefect.assignedTo}
                  </div>
                </div>
                <div style={{ marginBottom: '9px' }}>
                  <div style={{ fontSize: '9px', color: 'var(--text-secondary)', marginBottom: '3px' }}>
                    Reported By
                  </div>
                  <div style={{ fontSize: '10px', color: 'var(--text-primary)', fontWeight: 600 }}>
                    {selectedDefect.reportedBy}
                  </div>
                </div>
                <div style={{ marginBottom: '9px' }}>
                  <div style={{ fontSize: '9px', color: 'var(--text-secondary)', marginBottom: '3px' }}>
                    Created
                  </div>
                  <div style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>
                    {new Date(selectedDefect.created).toLocaleDateString()}
                  </div>
                </div>
                <div style={{ marginBottom: '9px' }}>
                  <div style={{ fontSize: '9px', color: 'var(--text-secondary)', marginBottom: '3px' }}>
                    Updated
                  </div>
                  <div style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>
                    {new Date(selectedDefect.updated).toLocaleDateString()}
                  </div>
                </div>
              </div>
            </div>

            {/* Description */}
            <div style={{ marginBottom: '12px' }}>
              <div
                style={{
                  fontSize: '9px',
                  color: 'var(--text-secondary)',
                  marginBottom: '5px',
                  fontWeight: 600,
                }}
              >
                Description
              </div>
              <p
                style={{
                  fontSize: '10px',
                  color: 'var(--text-primary)',
                  lineHeight: '1.5',
                  margin: 0,
                }}
              >
                {selectedDefect.description}
              </p>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              <button
                style={{
                  padding: '5px 10px',
                  fontSize: '10px',
                  fontWeight: 500,
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  background: '#3b82f6',
                  color: 'white',
                  transition: 'background 0.2s ease',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = '#2563eb')}
                onMouseLeave={(e) => (e.currentTarget.style.background = '#3b82f6')}
              >
                Edit
              </button>
              <button
                style={{
                  padding: '5px 10px',
                  fontSize: '10px',
                  fontWeight: 500,
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  background: '#06b6d4',
                  color: 'white',
                  transition: 'background 0.2s ease',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = '#0891b2')}
                onMouseLeave={(e) => (e.currentTarget.style.background = '#06b6d4')}
              >
                Reassign
              </button>
              <button
                style={{
                  padding: '5px 10px',
                  fontSize: '10px',
                  fontWeight: 500,
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  background: '#6b7280',
                  color: 'white',
                  transition: 'background 0.2s ease',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = '#4b5563')}
                onMouseLeave={(e) => (e.currentTarget.style.background = '#6b7280')}
              >
                Change Status
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
