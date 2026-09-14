'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { apiService, type Project, type TrendData } from '@/services/api';

interface ChartData {
  date: string;
  passRate?: number;
  duration?: number;
}

export default function TrendsPage() {
  const router = useRouter();
  const [viewMode, setViewMode] = useState<'project' | 'module'>('project');
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [selectedModule, setSelectedModule] = useState<string>('');
  const [timePeriod, setTimePeriod] = useState('Last 14 Days');
  
  // State for data fetching
  const [projects, setProjects] = useState<Project[]>([]);
  const [modules, setModules] = useState<string[]>([]);
  const [passRateData, setPassRateData] = useState<ChartData[]>([]);
  const [durationData, setDurationData] = useState<ChartData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Calculate days from time period
  const getDaysFromTimePeriod = (period: string): number => {
    switch (period) {
      case 'Last 7 Days':
        return 7;
      case 'Last 14 Days':
        return 14;
      case 'Last 30 Days':
        return 30;
      default:
        return 14;
    }
  };

  // Transform backend trend data to chart format
  const transformTrendData = (trends: TrendData[]): { passRate: ChartData[], duration: ChartData[] } => {
    console.log('[TrendsPage] Transforming trend data:', trends);
    
    const passRate = trends.map(item => ({
      date: item.date,
      passRate: item.pass_rate ?? 0,
    }));
    
    const duration = trends.map(item => ({
      date: item.date,
      duration: item.duration ? Math.round(item.duration / 60) : 0, // Convert seconds to minutes
    }));
    
    console.log('[TrendsPage] Transformed passRate data:', passRate);
    console.log('[TrendsPage] Transformed duration data:', duration);
    
    return { passRate, duration };
  };

  // Fetch projects on mount
  useEffect(() => {
    const fetchProjects = async () => {
      try {
        console.log('[TrendsPage] Fetching projects...');
        const projectsData = await apiService.projects.getAll();
        console.log('[TrendsPage] Projects fetched:', projectsData);
        
        setProjects(projectsData);
        
        // Set first project as default if available
        if (projectsData.length > 0) {
          setSelectedProject(projectsData[0].id);
        }
      } catch (err) {
        console.error('[TrendsPage] Error fetching projects:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch projects');
      }
    };
    
    fetchProjects();
  }, []);

  // Fetch trend data when filters change
  useEffect(() => {
    const fetchTrendData = async () => {
      if (!selectedProject) {
        console.log('[TrendsPage] No project selected, skipping trend fetch');
        setIsLoading(false);
        return;
      }
      
      try {
        setIsLoading(true);
        setError(null);
        
        const days = getDaysFromTimePeriod(timePeriod);
        
        console.log('[TrendsPage] Fetching trends with params:', { project_id: selectedProject, days });
        
        const trends = await apiService.analytics.getTrends({
          project_id: selectedProject,
          days: days,
        });
        
        console.log('[TrendsPage] Trends data received:', trends);
        
        if (trends && trends.length > 0) {
          const { passRate, duration } = transformTrendData(trends);
          setPassRateData(passRate);
          setDurationData(duration);
        } else {
          console.log('[TrendsPage] No trend data available');
          setPassRateData([]);
          setDurationData([]);
        }
        
      } catch (err) {
        console.error('[TrendsPage] Error fetching trends:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch trend data');
        setPassRateData([]);
        setDurationData([]);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchTrendData();
  }, [selectedProject, timePeriod]);

  // Fetch modules when project is selected
  useEffect(() => {
    const fetchModules = async () => {
      if (!selectedProject) {
        setModules([]);
        setSelectedModule('');
        return;
      }
      
      try {
        console.log('[TrendsPage] Fetching modules for project:', selectedProject);
        const modulesData = await apiService.modules.getByProject(selectedProject);
        console.log('[TrendsPage] Modules fetched:', modulesData);
        
        // Add "All Modules" option at the beginning
        const moduleNames = ['All Modules', ...modulesData.map(m => m.name)];
        setModules(moduleNames);
        setSelectedModule('All Modules');
      } catch (err) {
        console.error('[TrendsPage] Error fetching modules:', err);
        setModules(['All Modules']);
        setSelectedModule('All Modules');
      }
    };
    
    fetchModules();
  }, [selectedProject]);

  // Loading state
  if (isLoading && projects.length === 0) {
    return (
      <div style={{ padding: '30px', background: 'var(--bg-primary)', minHeight: '100vh' }}>
        <div style={{ textAlign: 'center', marginTop: '100px' }}>
          <div style={{ fontSize: '18px', color: 'var(--text-secondary)' }}>Loading trends data...</div>
        </div>
      </div>
    );
  }

  // Error state
  if (error && projects.length === 0) {
    return (
      <div style={{ padding: '30px', background: 'var(--bg-primary)', minHeight: '100vh' }}>
        <div style={{ textAlign: 'center', marginTop: '100px' }}>
          <div style={{ fontSize: '18px', color: '#ef4444', marginBottom: '10px' }}>Error Loading Data</div>
          <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>{error}</div>
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
          Quality Trends
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

      {/* View Mode Toggle */}
      <div style={{ marginBottom: '15px' }}>
        <div
          style={{
            display: 'inline-flex',
            borderRadius: '4px',
            overflow: 'hidden',
            border: '1px solid #e2e8f0',
          }}
        >
          <button
            onClick={() => setViewMode('project')}
            style={{
              padding: '5px 12px',
              fontSize: '11px',
              fontWeight: 500,
              border: 'none',
              cursor: 'pointer',
              background: viewMode === 'project' ? '#10b981' : 'white',
              color: viewMode === 'project' ? 'white' : '#64748b',
              transition: 'all 0.2s ease',
            }}
          >
            Project
          </button>
          <button
            onClick={() => setViewMode('module')}
            style={{
              padding: '5px 12px',
              fontSize: '11px',
              fontWeight: 500,
              border: 'none',
              borderLeft: '1px solid #e2e8f0',
              cursor: 'pointer',
              background: viewMode === 'module' ? '#10b981' : 'white',
              color: viewMode === 'module' ? 'white' : '#64748b',
              transition: 'all 0.2s ease',
            }}
          >
            Module
          </button>
        </div>
      </div>

      {/* Filter Row */}
      <div
        className="filter-row"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '12px',
          marginBottom: '15px',
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
            disabled={projects.length === 0}
            style={{
              width: '100%',
              padding: '6px 8px',
              fontSize: '11px',
              border: '1px solid #e2e8f0',
              borderRadius: '4px',
              background: projects.length === 0 ? '#f1f5f9' : 'white',
              color: projects.length === 0 ? '#94a3b8' : 'var(--text-primary)',
              cursor: projects.length === 0 ? 'not-allowed' : 'pointer',
              height: '36px',
            }}
          >
            {projects.length === 0 ? (
              <option value="">No projects available</option>
            ) : (
              projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))
            )}
          </select>
        </div>

        {/* Module Dropdown */}
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
            Module
          </label>
          <select
            value={selectedModule}
            onChange={(e) => setSelectedModule(e.target.value)}
            disabled={viewMode === 'project' || modules.length === 0}
            style={{
              width: '100%',
              padding: '6px 8px',
              fontSize: '11px',
              border: '1px solid #e2e8f0',
              borderRadius: '4px',
              background: viewMode === 'project' || modules.length === 0 ? '#f1f5f9' : 'white',
              color: viewMode === 'project' || modules.length === 0 ? '#94a3b8' : 'var(--text-primary)',
              cursor: viewMode === 'project' || modules.length === 0 ? 'not-allowed' : 'pointer',
              height: '36px',
            }}
          >
            {modules.map((module) => (
              <option key={module} value={module}>
                {module}
              </option>
            ))}
          </select>
        </div>

        {/* Time Period Dropdown */}
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
            Time Period
          </label>
          <select
            value={timePeriod}
            onChange={(e) => setTimePeriod(e.target.value)}
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
            <option value="Last 7 Days">Last 7 Days</option>
            <option value="Last 14 Days">Last 14 Days</option>
            <option value="Last 30 Days">Last 30 Days</option>
          </select>
        </div>
      </div>

      {/* Charts Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '12px',
        }}
      >
        {/* Pass Rate Trend Chart */}
        <div
          style={{
            background: 'white',
            borderRadius: '8px',
            padding: '12px',
            boxShadow: 'var(--shadow-demo-md)',
          }}
        >
          <h3
            style={{
              fontSize: '13px',
              fontWeight: 600,
              color: 'var(--text-primary)',
              marginBottom: '12px',
            }}
          >
            Pass Rate Trend
          </h3>
          {isLoading ? (
            <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Loading chart data...</div>
            </div>
          ) : error ? (
            <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '14px', color: '#ef4444', marginBottom: '5px' }}>Error loading data</div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{error}</div>
              </div>
            </div>
          ) : passRateData.length === 0 ? (
            <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>No trend data available for the selected period</div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={passRateData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: '#64748b', fontSize: 12 }}
                  tickFormatter={(value) => {
                    const date = new Date(value);
                    return `${date.getMonth() + 1}/${date.getDate()}`;
                  }}
                />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fill: '#64748b', fontSize: 12 }}
                  label={{
                    value: 'Pass Rate (%)',
                    angle: -90,
                    position: 'insideLeft',
                    style: { fill: '#64748b', fontSize: 12 },
                  }}
                />
                <Tooltip
                  contentStyle={{
                    background: 'white',
                    border: '1px solid #e2e8f0',
                    borderRadius: '6px',
                    fontSize: '12px',
                  }}
                  formatter={(value: any) => [`${value}%`, 'Pass Rate']}
                  labelFormatter={(label: any) => {
                    const date = new Date(label as string);
                    return date.toLocaleDateString();
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="passRate"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={{ fill: '#10b981', r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Duration Trend Chart */}
        <div
          style={{
            background: 'white',
            borderRadius: '8px',
            padding: '12px',
            boxShadow: 'var(--shadow-demo-md)',
          }}
        >
          <h3
            style={{
              fontSize: '13px',
              fontWeight: 600,
              color: 'var(--text-primary)',
              marginBottom: '12px',
            }}
          >
            Duration Trend
          </h3>
          {isLoading ? (
            <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Loading chart data...</div>
            </div>
          ) : error ? (
            <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '14px', color: '#ef4444', marginBottom: '5px' }}>Error loading data</div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{error}</div>
              </div>
            </div>
          ) : durationData.length === 0 ? (
            <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>No trend data available for the selected period</div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={durationData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: '#64748b', fontSize: 12 }}
                  tickFormatter={(value) => {
                    const date = new Date(value);
                    return `${date.getMonth() + 1}/${date.getDate()}`;
                  }}
                />
                <YAxis
                  tick={{ fill: '#64748b', fontSize: 12 }}
                  label={{
                    value: 'Duration (minutes)',
                    angle: -90,
                    position: 'insideLeft',
                    style: { fill: '#64748b', fontSize: 12 },
                  }}
                />
                <Tooltip
                  contentStyle={{
                    background: 'white',
                    border: '1px solid #e2e8f0',
                    borderRadius: '6px',
                    fontSize: '12px',
                  }}
                  formatter={(value: any) => [`${value} min`, 'Duration']}
                  labelFormatter={(label: any) => {
                    const date = new Date(label as string);
                    return date.toLocaleDateString();
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="duration"
                  stroke="#6366f1"
                  strokeWidth={2}
                  dot={{ fill: '#6366f1', r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}
