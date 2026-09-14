'use client';

import { useState } from 'react';

// Mock data for AI failures
const mockAIFailures = [
  {
    id: 1,
    scenario: 'User Login with Invalid Credentials',
    tags: ['Authentication', 'Critical'],
    duration: '45s',
    status: 'Failed',
    failedStep: 'Verify error message display',
    aiInsight: {
      confidence: 92,
      rootCause: 'Element selector changed in latest build',
      pattern: 'Recurring across 3 test runs',
      historicalContext: [
        { date: '2024-01-20', run: 'Build #145', status: 'Passed' },
        { date: '2024-01-21', run: 'Build #146', status: 'Failed' },
        { date: '2024-01-22', run: 'Build #147', status: 'Failed' },
      ],
      similarFailures: [
        { scenario: 'User Registration Flow', similarity: 85, issue: 'Same selector pattern' },
        { scenario: 'Password Reset', similarity: 78, issue: 'Element not found' },
        { scenario: 'Social Login', similarity: 72, issue: 'Timeout on element' },
      ],
      suggestedFix: `// Updated selector fix\nconst errorMessage = await page.waitForSelector('[data-testid="error-message"]', {\n  timeout: 5000,\n  state: 'visible'\n});\n\n// Add retry logic\nfor (let i = 0; i < 3; i++) {\n  try {\n    await errorMessage.textContent();\n    break;\n  } catch (e) {\n    if (i === 2) throw e;\n    await page.waitForTimeout(1000);\n  }\n}`,
    },
  },
  {
    id: 2,
    scenario: 'Shopping Cart Checkout Flow',
    tags: ['E-commerce', 'Payment'],
    duration: '2m 15s',
    status: 'Failed',
    failedStep: 'Payment gateway integration',
    aiInsight: {
      confidence: 88,
      rootCause: 'Network timeout during API call',
      pattern: 'Flaky - passes 60% of time',
      historicalContext: [
        { date: '2024-01-19', run: 'Build #142', status: 'Passed' },
        { date: '2024-01-20', run: 'Build #143', status: 'Failed' },
        { date: '2024-01-21', run: 'Build #144', status: 'Passed' },
      ],
      similarFailures: [
        { scenario: 'One-Click Purchase', similarity: 91, issue: 'API timeout' },
        { scenario: 'Subscription Payment', similarity: 84, issue: 'Gateway delay' },
      ],
      suggestedFix: `// Increase timeout and add retry mechanism\nconst paymentResponse = await page.waitForResponse(\n  response => response.url().includes('/api/payment') && response.status() === 200,\n  { timeout: 30000 } // Increased from 10s to 30s\n);\n\n// Add exponential backoff\nconst retry = async (fn, retries = 3, delay = 1000) => {\n  try {\n    return await fn();\n  } catch (err) {\n    if (retries === 0) throw err;\n    await new Promise(resolve => setTimeout(resolve, delay));\n    return retry(fn, retries - 1, delay * 2);\n  }\n};`,
    },
  },
  {
    id: 3,
    scenario: 'Dashboard Data Refresh',
    tags: ['Dashboard', 'API'],
    duration: '1m 30s',
    status: 'Failed',
    failedStep: 'Validate updated metrics',
    aiInsight: {
      confidence: 95,
      rootCause: 'Race condition in async data loading',
      pattern: 'New regression in Build #148',
      historicalContext: [
        { date: '2024-01-18', run: 'Build #140', status: 'Passed' },
        { date: '2024-01-19', run: 'Build #141', status: 'Passed' },
        { date: '2024-01-22', run: 'Build #148', status: 'Failed' },
      ],
      similarFailures: [
        { scenario: 'Analytics Widget Load', similarity: 89, issue: 'Race condition' },
        { scenario: 'Live Data Updates', similarity: 81, issue: 'Async timing' },
      ],
      suggestedFix: `// Add proper wait for data load completion\nawait page.waitForFunction(\n  () => {\n    const loadingSpinner = document.querySelector('[data-loading]');\n    const dataElements = document.querySelectorAll('[data-metric]');\n    return !loadingSpinner && dataElements.length > 0;\n  },\n  { timeout: 10000 }\n);\n\n// Verify data stability\nawait page.waitForTimeout(500); // Wait for animations\nconst initialValue = await page.textContent('[data-metric="total"]');\nawait page.waitForTimeout(500);\nconst finalValue = await page.textContent('[data-metric="total"]');\nassert.equal(initialValue, finalValue, 'Data should be stable');`,
    },
  },
  {
    id: 4,
    scenario: 'File Upload Validation',
    tags: ['Upload', 'Validation'],
    duration: '55s',
    status: 'Failed',
    failedStep: 'Verify file upload success',
    aiInsight: {
      confidence: 87,
      rootCause: 'File size limit exceeded silently',
      pattern: 'Recurring - 4 consecutive failures',
      historicalContext: [
        { date: '2024-01-20', run: 'Build #145', status: 'Failed' },
        { date: '2024-01-21', run: 'Build #146', status: 'Failed' },
        { date: '2024-01-22', run: 'Build #147', status: 'Failed' },
      ],
      similarFailures: [
        { scenario: 'Profile Picture Upload', similarity: 94, issue: 'Size validation' },
        { scenario: 'Document Attachment', similarity: 88, issue: 'Upload timeout' },
      ],
      suggestedFix: `// Add file size validation before upload\nconst fileInput = await page.locator('input[type="file"]');\nconst filePath = path.join(__dirname, 'fixtures', 'test-file.pdf');\nconst stats = fs.statSync(filePath);\nconst maxSize = 5 * 1024 * 1024; // 5MB\n\nif (stats.size > maxSize) {\n  // Use smaller test file\n  filePath = path.join(__dirname, 'fixtures', 'small-test-file.pdf');\n}\n\nawait fileInput.setInputFiles(filePath);\n\n// Wait for upload completion\nawait page.waitForSelector('[data-upload-status="success"]', {\n  timeout: 15000\n});`,
    },
  },
];

const mockProjects = ['E-commerce Platform', 'Mobile App', 'API Gateway', 'Admin Dashboard'];
const mockModules = ['Login Module', 'Checkout Module', 'Dashboard', 'User Profile', 'Payment Gateway'];

export default function AIFailureAnalysisPage() {
  const [selectedProject, setSelectedProject] = useState('All');
  const [selectedModule, setSelectedModule] = useState('All');
  const [selectedFailure, setSelectedFailure] = useState<typeof mockAIFailures[0] | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [showHistoricalContext, setShowHistoricalContext] = useState(false);
  const [showAIFix, setShowAIFix] = useState(false);
  const [isGeneratingFix, setIsGeneratingFix] = useState(false);

  // Calculate summary stats
  const totalFailures = mockAIFailures.length;
  const uniquePatterns = 3;
  const flakyTests = 1;
  const recentRegressions = 1;
  const criticalPriority = 2;
  const avgAIConfidence = Math.round(
    mockAIFailures.reduce((sum, f) => sum + f.aiInsight.confidence, 0) / mockAIFailures.length
  );

  const handleViewAIInsight = (failure: typeof mockAIFailures[0]) => {
    setSelectedFailure(failure);
    setShowModal(true);
    setShowAIFix(false);
    setShowHistoricalContext(false);
  };

  const handleGenerateAIFix = () => {
    setIsGeneratingFix(true);
    // Simulate AI generation delay
    setTimeout(() => {
      setShowAIFix(true);
      setIsGeneratingFix(false);
    }, 1500);
  };

  return (
    <div style={{ padding: '30px', background: 'var(--bg-primary)', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ marginBottom: '30px' }}>
        <h1
          style={{
            fontSize: 'var(--text-2xl)',
            fontWeight: 700,
            color: 'var(--text-primary)',
            marginBottom: '8px',
          }}
        >
          AI-Powered Failure Analysis
        </h1>
        <p
          style={{
            fontSize: 'var(--text-base)',
            color: 'var(--text-secondary)',
            marginBottom: '16px',
          }}
        >
          Intelligent pattern detection, root cause analysis, and predictive insights
        </p>
        {/* Badges */}
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <span
            style={{
              padding: '6px 12px',
              borderRadius: '20px',
              fontSize: '13px',
              fontWeight: 600,
              color: 'white',
              background: '#16a34a',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: '#22c55e',
                animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
              }}
            />
            Live Analysis
          </span>
          <span
            style={{
              padding: '6px 12px',
              borderRadius: '20px',
              fontSize: '13px',
              fontWeight: 600,
              color: 'white',
              background: '#3b82f6',
            }}
          >
            <i className="fa fa-brain" style={{ marginRight: '6px' }} />
            ML Insights Active
          </span>
        </div>
      </div>

      {/* Filters */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '20px',
          marginBottom: '25px',
          background: 'var(--bg-secondary)',
          padding: '20px',
          borderRadius: '8px',
        }}
      >
        {/* Project Dropdown */}
        <div>
          <label
            style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: 500,
              color: 'var(--text-secondary)',
              marginBottom: '8px',
            }}
          >
            Project
          </label>
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px',
              fontSize: '14px',
              border: '1px solid #e2e8f0',
              borderRadius: '6px',
              background: 'white',
              color: 'var(--text-primary)',
            }}
          >
            <option value="All">All Projects</option>
            {mockProjects.map((project) => (
              <option key={project} value={project}>
                {project}
              </option>
            ))}
          </select>
        </div>

        {/* Module Dropdown */}
        <div>
          <label
            style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: 500,
              color: 'var(--text-secondary)',
              marginBottom: '8px',
            }}
          >
            Module
          </label>
          <select
            value={selectedModule}
            onChange={(e) => setSelectedModule(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px',
              fontSize: '14px',
              border: '1px solid #e2e8f0',
              borderRadius: '6px',
              background: 'white',
              color: 'var(--text-primary)',
            }}
          >
            <option value="All">All Modules</option>
            {mockModules.map((module) => (
              <option key={module} value={module}>
                {module}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(6, 1fr)',
          gap: '20px',
          marginBottom: '25px',
        }}
      >
        {/* Total Failures */}
        <div
          style={{
            gridColumn: 'span 2',
            background: 'white',
            borderRadius: '12px',
            padding: '20px',
            boxShadow: 'var(--shadow-demo-md)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{ fontSize: '28px', fontWeight: 700, color: '#ef4444' }}>{totalFailures}</div>
            <div style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Total Failures
            </div>
          </div>
          <i className="fa fa-bug" style={{ fontSize: '28px', color: '#ef4444' }}></i>
        </div>

        {/* Unique Patterns */}
        <div
          style={{
            gridColumn: 'span 2',
            background: 'white',
            borderRadius: '12px',
            padding: '20px',
            boxShadow: 'var(--shadow-demo-md)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{ fontSize: '28px', fontWeight: 700, color: '#8b5cf6' }}>{uniquePatterns}</div>
            <div style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Unique Patterns
            </div>
          </div>
          <i className="fa fa-project-diagram" style={{ fontSize: '28px', color: '#8b5cf6' }}></i>
        </div>

        {/* Flaky Tests */}
        <div
          style={{
            gridColumn: 'span 2',
            background: 'white',
            borderRadius: '12px',
            padding: '20px',
            boxShadow: 'var(--shadow-demo-md)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{ fontSize: '28px', fontWeight: 700, color: '#f59e0b' }}>{flakyTests}</div>
            <div style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Flaky Tests
            </div>
          </div>
          <i className="fa fa-random" style={{ fontSize: '28px', color: '#f59e0b' }}></i>
        </div>

        {/* Recent Regressions */}
        <div
          style={{
            gridColumn: 'span 2',
            background: 'white',
            borderRadius: '12px',
            padding: '20px',
            boxShadow: 'var(--shadow-demo-md)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{ fontSize: '28px', fontWeight: 700, color: '#ef4444' }}>{recentRegressions}</div>
            <div style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Recent Regressions
            </div>
          </div>
          <i className="fa fa-exclamation-circle" style={{ fontSize: '28px', color: '#ef4444' }}></i>
        </div>

        {/* Critical Priority */}
        <div
          style={{
            gridColumn: 'span 2',
            background: 'white',
            borderRadius: '12px',
            padding: '20px',
            boxShadow: 'var(--shadow-demo-md)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{ fontSize: '28px', fontWeight: 700, color: '#dc2626' }}>{criticalPriority}</div>
            <div style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Critical Priority
            </div>
          </div>
          <i className="fa fa-fire" style={{ fontSize: '28px', color: '#dc2626' }}></i>
        </div>

        {/* AI Confidence */}
        <div
          style={{
            gridColumn: 'span 2',
            background: 'white',
            borderRadius: '12px',
            padding: '20px',
            boxShadow: 'var(--shadow-demo-md)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{ fontSize: '28px', fontWeight: 700, color: '#22c55e' }}>{avgAIConfidence}%</div>
            <div style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              AI Confidence
            </div>
          </div>
          <i className="fa fa-brain" style={{ fontSize: '28px', color: '#22c55e' }}></i>
        </div>
      </div>

      {/* AI Failures Table */}
      <div
        style={{
          background: 'white',
          borderRadius: '12px',
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
                    padding: '12px',
                    color: 'white',
                    fontWeight: 'bold',
                    textAlign: 'left',
                    fontSize: '14px',
                  }}
                >
                  Scenario
                </th>
                <th
                  style={{
                    padding: '12px',
                    color: 'white',
                    fontWeight: 'bold',
                    textAlign: 'left',
                    fontSize: '14px',
                  }}
                >
                  Tags
                </th>
                <th
                  style={{
                    padding: '12px',
                    color: 'white',
                    fontWeight: 'bold',
                    textAlign: 'center',
                    fontSize: '14px',
                  }}
                >
                  Duration
                </th>
                <th
                  style={{
                    padding: '12px',
                    color: 'white',
                    fontWeight: 'bold',
                    textAlign: 'center',
                    fontSize: '14px',
                  }}
                >
                  Status
                </th>
                <th
                  style={{
                    padding: '12px',
                    color: 'white',
                    fontWeight: 'bold',
                    textAlign: 'left',
                    fontSize: '14px',
                  }}
                >
                  Failed Step
                </th>
                <th
                  style={{
                    padding: '12px',
                    color: 'white',
                    fontWeight: 'bold',
                    textAlign: 'center',
                    fontSize: '14px',
                  }}
                >
                  AI Insight
                </th>
              </tr>
            </thead>
            <tbody>
              {mockAIFailures.map((failure) => (
                <tr
                  key={failure.id}
                  style={{
                    background: 'white',
                    transition: 'background 0.2s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = '#f1f5f9';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'white';
                  }}
                >
                  <td
                    style={{
                      padding: '12px',
                      borderBottom: '1px solid #e2e8f0',
                      fontSize: '14px',
                      fontWeight: 600,
                      color: 'var(--text-primary)',
                    }}
                  >
                    {failure.scenario}
                  </td>
                  <td
                    style={{
                      padding: '12px',
                      borderBottom: '1px solid #e2e8f0',
                      fontSize: '14px',
                    }}
                  >
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      {failure.tags.map((tag) => (
                        <span
                          key={tag}
                          style={{
                            padding: '3px 8px',
                            borderRadius: '4px',
                            fontSize: '11px',
                            fontWeight: 600,
                            color: '#3b82f6',
                            background: '#dbeafe',
                          }}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td
                    style={{
                      padding: '12px',
                      borderBottom: '1px solid #e2e8f0',
                      fontSize: '14px',
                      textAlign: 'center',
                      color: 'var(--text-secondary)',
                    }}
                  >
                    {failure.duration}
                  </td>
                  <td
                    style={{
                      padding: '12px',
                      borderBottom: '1px solid #e2e8f0',
                      fontSize: '14px',
                      textAlign: 'center',
                    }}
                  >
                    <span
                      style={{
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: 600,
                        color: 'white',
                        background: '#dc2626',
                      }}
                    >
                      {failure.status}
                    </span>
                  </td>
                  <td
                    style={{
                      padding: '12px',
                      borderBottom: '1px solid #e2e8f0',
                      fontSize: '14px',
                      color: 'var(--text-primary)',
                    }}
                  >
                    {failure.failedStep}
                  </td>
                  <td
                    style={{
                      padding: '12px',
                      borderBottom: '1px solid #e2e8f0',
                      textAlign: 'center',
                    }}
                  >
                    <button
                      onClick={() => handleViewAIInsight(failure)}
                      style={{
                        padding: '8px 16px',
                        fontSize: '13px',
                        fontWeight: 600,
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
                        color: 'white',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '8px',
                        transition: 'all 0.3s ease',
                        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'translateY(-2px)';
                        e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'translateY(0)';
                        e.currentTarget.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)';
                      }}
                    >
                      <i
                        className="fa fa-brain"
                        style={{
                          animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                        }}
                      />
                      View Insight
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* AI Analysis Modal */}
      {showModal && selectedFailure && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: '20px',
          }}
          onClick={() => setShowModal(false)}
        >
          <div
            style={{
              background: 'white',
              borderRadius: '12px',
              width: '100%',
              maxWidth: '900px',
              maxHeight: '90vh',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div
              style={{
                padding: '24px',
                borderBottom: '1px solid #e2e8f0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <h2
                style={{
                  fontSize: '20px',
                  fontWeight: 700,
                  color: 'var(--text-primary)',
                  margin: 0,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                }}
              >
                <i className="fa fa-brain" style={{ color: '#8b5cf6' }} />
                AI Analysis: {selectedFailure.scenario}
              </h2>
              <button
                onClick={() => setShowModal(false)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  fontSize: '24px',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  padding: '0',
                  width: '30px',
                  height: '30px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  borderRadius: '6px',
                  transition: 'all 0.2s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = '#f1f5f9';
                  e.currentTarget.style.color = 'var(--text-primary)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = 'var(--text-secondary)';
                }}
              >
                ×
              </button>
            </div>

            {/* Modal Body */}
            <div
              style={{
                padding: '24px',
                overflowY: 'auto',
                maxHeight: '70vh',
              }}
            >
              {/* AI Confidence Badge */}
              <div style={{ marginBottom: '20px' }}>
                <div
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 16px',
                    background: '#ecfdf5',
                    borderRadius: '8px',
                    border: '1px solid #86efac',
                  }}
                >
                  <i className="fa fa-check-circle" style={{ color: '#22c55e' }} />
                  <span style={{ fontSize: '14px', fontWeight: 600, color: '#16a34a' }}>
                    AI Confidence: {selectedFailure.aiInsight.confidence}%
                  </span>
                </div>
              </div>

              {/* Root Cause */}
              <div style={{ marginBottom: '24px' }}>
                <h3
                  style={{
                    fontSize: '16px',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    marginBottom: '8px',
                  }}
                >
                  🎯 Root Cause Analysis
                </h3>
                <p
                  style={{
                    fontSize: '14px',
                    color: 'var(--text-primary)',
                    lineHeight: '1.6',
                    background: '#fef3c7',
                    padding: '12px',
                    borderRadius: '6px',
                    borderLeft: '4px solid #f59e0b',
                  }}
                >
                  {selectedFailure.aiInsight.rootCause}
                </p>
              </div>

              {/* Pattern */}
              <div style={{ marginBottom: '24px' }}>
                <h3
                  style={{
                    fontSize: '16px',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    marginBottom: '8px',
                  }}
                >
                  📊 Pattern Detection
                </h3>
                <p
                  style={{
                    fontSize: '14px',
                    color: 'var(--text-primary)',
                    lineHeight: '1.6',
                    background: '#dbeafe',
                    padding: '12px',
                    borderRadius: '6px',
                    borderLeft: '4px solid #3b82f6',
                  }}
                >
                  {selectedFailure.aiInsight.pattern}
                </p>
              </div>

              {/* Historical Context Accordion */}
              <div style={{ marginBottom: '24px' }}>
                <button
                  onClick={() => setShowHistoricalContext(!showHistoricalContext)}
                  style={{
                    width: '100%',
                    padding: '12px',
                    background: '#f8fafc',
                    border: '1px solid #e2e8f0',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '16px',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = '#f1f5f9';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = '#f8fafc';
                  }}
                >
                  <span>📈 Historical Context</span>
                  <i
                    className={`fa fa-chevron-${showHistoricalContext ? 'up' : 'down'}`}
                    style={{ fontSize: '14px' }}
                  />
                </button>
                {showHistoricalContext && (
                  <div
                    style={{
                      marginTop: '12px',
                      padding: '16px',
                      background: '#f8fafc',
                      borderRadius: '6px',
                      animation: 'slideIn 0.3s ease-out',
                    }}
                  >
                    {selectedFailure.aiInsight.historicalContext.map((context, idx) => (
                      <div
                        key={idx}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '8px 0',
                          borderBottom:
                            idx < selectedFailure.aiInsight.historicalContext.length - 1
                              ? '1px solid #e2e8f0'
                              : 'none',
                        }}
                      >
                        <div style={{ fontSize: '14px', color: 'var(--text-primary)' }}>
                          <strong>{context.date}</strong> - {context.run}
                        </div>
                        <span
                          style={{
                            padding: '4px 8px',
                            borderRadius: '4px',
                            fontSize: '12px',
                            fontWeight: 600,
                            color: 'white',
                            background: context.status === 'Passed' ? '#22c55e' : '#dc2626',
                          }}
                        >
                          {context.status}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Similar Failures */}
              <div style={{ marginBottom: '24px' }}>
                <h3
                  style={{
                    fontSize: '16px',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    marginBottom: '12px',
                  }}
                >
                  🔍 Similar Failures
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {selectedFailure.aiInsight.similarFailures.map((similar, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '12px',
                        background: '#fff7ed',
                        borderRadius: '6px',
                        border: '1px solid #fed7aa',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          marginBottom: '6px',
                        }}
                      >
                        <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                          {similar.scenario}
                        </span>
                        <span
                          style={{
                            padding: '4px 10px',
                            borderRadius: '20px',
                            fontSize: '12px',
                            fontWeight: 600,
                            color: '#ea580c',
                            background: '#fed7aa',
                          }}
                        >
                          {similar.similarity}% match
                        </span>
                      </div>
                      <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                        Issue: {similar.issue}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Generate AI Fix Button */}
              <div style={{ marginBottom: '24px' }}>
                <button
                  onClick={handleGenerateAIFix}
                  disabled={isGeneratingFix || showAIFix}
                  style={{
                    width: '100%',
                    padding: '14px 24px',
                    fontSize: '16px',
                    fontWeight: 600,
                    border: 'none',
                    borderRadius: '8px',
                    cursor: isGeneratingFix || showAIFix ? 'not-allowed' : 'pointer',
                    background:
                      isGeneratingFix || showAIFix
                        ? '#94a3b8'
                        : 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '10px',
                    transition: 'all 0.3s ease',
                    boxShadow: '0 4px 12px rgba(139, 92, 246, 0.3)',
                  }}
                  onMouseEnter={(e) => {
                    if (!isGeneratingFix && !showAIFix) {
                      e.currentTarget.style.transform = 'translateY(-2px)';
                      e.currentTarget.style.boxShadow = '0 6px 16px rgba(139, 92, 246, 0.4)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isGeneratingFix && !showAIFix) {
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = '0 4px 12px rgba(139, 92, 246, 0.3)';
                    }
                  }}
                >
                  {isGeneratingFix ? (
                    <>
                      <i className="fa fa-spinner fa-spin" />
                      Generating AI Fix...
                    </>
                  ) : showAIFix ? (
                    <>
                      <i className="fa fa-check-circle" />
                      Fix Generated
                    </>
                  ) : (
                    <>
                      <i className="fa fa-magic" />
                      Generate AI Fix
                    </>
                  )}
                </button>
              </div>

              {/* AI Fix Output */}
              {showAIFix && (
                <div
                  style={{
                    background: '#f0fdf4',
                    border: '2px solid #bbf7d0',
                    borderRadius: '12px',
                    padding: '20px',
                    boxShadow: '0 4px 12px rgba(34, 197, 94, 0.2)',
                    animation: 'slideIn 0.5s ease-out',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      marginBottom: '16px',
                    }}
                  >
                    <i className="fa fa-check-circle" style={{ color: '#22c55e', fontSize: '20px' }} />
                    <h3
                      style={{
                        fontSize: '16px',
                        fontWeight: 700,
                        color: '#16a34a',
                        margin: 0,
                      }}
                    >
                      ✨ Suggested Fix
                    </h3>
                  </div>
                  <pre
                    style={{
                      background: '#dcfce7',
                      padding: '16px',
                      borderRadius: '8px',
                      fontSize: '13px',
                      lineHeight: '1.6',
                      color: '#166534',
                      fontFamily: 'monospace',
                      overflowX: 'auto',
                      margin: 0,
                      border: '1px solid #86efac',
                    }}
                  >
                    {selectedFailure.aiInsight.suggestedFix}
                  </pre>
                  <div
                    style={{
                      marginTop: '12px',
                      padding: '12px',
                      background: '#dcfce7',
                      borderRadius: '6px',
                      fontSize: '13px',
                      color: '#166534',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                    }}
                  >
                    <i className="fa fa-info-circle" />
                    <span>
                      This fix has been generated by AI based on historical patterns and similar failures.
                      Please review and test before applying.
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
