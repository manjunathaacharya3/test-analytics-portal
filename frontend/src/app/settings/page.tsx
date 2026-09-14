"use client";

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiService, ApiError, Project, Module } from '@/services/api';

type TabType = 'projects' | 'modules';

const SettingsPage: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const projectId = searchParams.get('id');
  const isEditMode = !!projectId;

  // Tab state
  const [activeTab, setActiveTab] = useState<TabType>('projects');

  // Project form state
  const [formData, setFormData] = useState({
    name: '',
    owner: '',
    description: '',
    repositoryUrl: ''
  });

  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [actionMessage, setActionMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Module management state
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [modules, setModules] = useState<Module[]>([]);
  const [isLoadingProjects, setIsLoadingProjects] = useState(false);
  const [isLoadingModules, setIsLoadingModules] = useState(false);
  const [moduleError, setModuleError] = useState<string | null>(null);
  const [showAddModule, setShowAddModule] = useState(false);
  const [newModule, setNewModule] = useState({ name: '', description: '' });
  const [editingModule, setEditingModule] = useState<{ id: string; name: string; description: string } | null>(null);
  const [moduleActionMessage, setModuleActionMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  // Load project data in edit mode
  useEffect(() => {
    const loadProject = async () => {
      if (isEditMode && projectId) {
        setIsLoading(true);
        console.log('[Settings] Loading project for editing, ID:', projectId);
        
        try {
          const project = await apiService.projects.getById(projectId as any);
          console.log('[Settings] Project loaded successfully:', project);
          
          setFormData({
            name: project.name,
            owner: project.owner,
            description: project.description || '',
            repositoryUrl: project.repository_url || ''
          });
        } catch (error) {
          console.error('[Settings] Error loading project:', error);
          
          const errorMessage = error instanceof ApiError 
            ? error.message 
            : 'Failed to load project data';
          
          setActionMessage({
            type: 'error',
            text: errorMessage
          });
        } finally {
          setIsLoading(false);
        }
      }
    };
    
    loadProject();
  }, [isEditMode, projectId]);

  // Load all projects for module management tab
  useEffect(() => {
    const loadProjects = async () => {
      if (activeTab === 'modules') {
        setIsLoadingProjects(true);
        console.log('[Settings] Loading all projects for module management');
        
        try {
          const projectsList = await apiService.projects.getAll();
          console.log('[Settings] Projects loaded:', projectsList);
          setProjects(projectsList || []);
        } catch (error) {
          console.error('[Settings] Error loading projects:', error);
        } finally {
          setIsLoadingProjects(false);
        }
      }
    };
    
    loadProjects();
  }, [activeTab]);

  // Load modules when project is selected in module management tab
  useEffect(() => {
    const loadModules = async () => {
      if (activeTab === 'modules' && selectedProjectId) {
        setIsLoadingModules(true);
        setModuleError(null);
        console.log('[Settings] Loading modules for project ID:', selectedProjectId);
        
        try {
          const modulesList = await apiService.modules.getByProject(selectedProjectId);
          console.log('[Settings] Modules loaded successfully:', modulesList);
          setModules(modulesList);
        } catch (error) {
          console.error('[Settings] Error loading modules:', error);
          const errorMessage = error instanceof ApiError 
            ? error.message 
            : 'Failed to load modules';
          setModuleError(errorMessage);
        } finally {
          setIsLoadingModules(false);
        }
      } else if (activeTab === 'modules' && !selectedProjectId) {
        setModules([]);
      }
    };
    
    loadModules();
  }, [activeTab, selectedProjectId]);

  // Form validation
  const validateForm = (): boolean => {
    const newErrors: { [key: string]: string } = {};

    // Required field validation
    if (!formData.name.trim()) {
      newErrors.name = 'Project name is required';
    }

    if (!formData.owner.trim()) {
      newErrors.owner = 'Owner is required';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    }

    if (!formData.repositoryUrl.trim()) {
      newErrors.repositoryUrl = 'Repository URL is required';
    } else {
      // URL validation
      try {
        new URL(formData.repositoryUrl);
      } catch (e) {
        newErrors.repositoryUrl = 'Please enter a valid URL';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error for this field when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Clear previous messages
    setActionMessage(null);

    // Validate form
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    console.log('[Settings] Submitting form, isEditMode:', isEditMode, 'projectId:', projectId);

    try {
      // Prepare data with backend field names (snake_case)
      const projectData = {
        name: formData.name,
        owner: formData.owner,
        description: formData.description,
        repository_url: formData.repositoryUrl,
        is_active: true // Default to active
      };

      console.log('[Settings] Sending data to API:', projectData);

      let savedProject: Project;
      
      if (isEditMode && projectId) {
        // Update existing project
        savedProject = await apiService.projects.update(projectId as any, projectData);
        console.log('[Settings] Project updated successfully:', savedProject);
      } else {
        // Create new project
        savedProject = await apiService.projects.create(projectData);
        console.log('[Settings] Project created successfully:', savedProject);
      }

      // Show success message
      setActionMessage({
        type: 'success',
        text: isEditMode 
          ? 'Project updated successfully!' 
          : 'Project created successfully!'
      });

      // Reset form in create mode
      if (!isEditMode) {
        setFormData({
          name: '',
          owner: '',
          description: '',
          repositoryUrl: ''
        });
      }

      // Redirect to projects page after 2 seconds
      setTimeout(() => {
        router.push('/projects');
      }, 2000);
    } catch (error) {
      console.error('[Settings] Error submitting form:', error);
      
      const errorMessage = error instanceof ApiError 
        ? error.message 
        : 'An error occurred. Please try again.';
      
      setActionMessage({
        type: 'error',
        text: errorMessage
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle back button
  const handleBack = () => {
    router.push('/projects');
  };

  // Module management handlers
  const handleAddModule = async () => {
    if (!newModule.name.trim()) {
      setModuleActionMessage({
        type: 'error',
        text: 'Module name is required'
      });
      return;
    }

    if (!selectedProjectId) {
      setModuleActionMessage({
        type: 'error',
        text: 'Please select a project first'
      });
      return;
    }

    try {
      const createdModule = await apiService.modules.create(selectedProjectId, {
        name: newModule.name.trim(),
        description: newModule.description.trim() || undefined
      });
      
      setModules(prev => [...prev, createdModule]);
      setNewModule({ name: '', description: '' });
      setShowAddModule(false);
      setModuleActionMessage({
        type: 'success',
        text: 'Module added successfully!'
      });
      setTimeout(() => setModuleActionMessage(null), 3000);
    } catch (error) {
      console.error('[Settings] Error adding module:', error);
      const errorMessage = error instanceof ApiError 
        ? error.message 
        : 'Failed to add module';
      setModuleActionMessage({
        type: 'error',
        text: errorMessage
      });
    }
  };

  const handleEditModule = async (moduleId: string) => {
    if (!editingModule || !selectedProjectId) return;

    if (!editingModule.name.trim()) {
      setModuleActionMessage({
        type: 'error',
        text: 'Module name is required'
      });
      return;
    }

    try {
      const updatedModule = await apiService.modules.update(selectedProjectId, moduleId, {
        name: editingModule.name.trim(),
        description: editingModule.description.trim() || undefined
      });
      
      setModules(prev => prev.map(m => m.id === moduleId ? updatedModule : m));
      setEditingModule(null);
      setModuleActionMessage({
        type: 'success',
        text: 'Module updated successfully!'
      });
      setTimeout(() => setModuleActionMessage(null), 3000);
    } catch (error) {
      console.error('[Settings] Error updating module:', error);
      const errorMessage = error instanceof ApiError 
        ? error.message 
        : 'Failed to update module';
      setModuleActionMessage({
        type: 'error',
        text: errorMessage
      });
    }
  };

  const handleDeleteModule = async (moduleId: string) => {
    if (!selectedProjectId) return;
    
    if (!confirm('Are you sure you want to delete this module?')) {
      return;
    }

    try {
      await apiService.modules.delete(selectedProjectId, moduleId);
      setModules(prev => prev.filter(m => m.id !== moduleId));
      setModuleActionMessage({
        type: 'success',
        text: 'Module deleted successfully!'
      });
      setTimeout(() => setModuleActionMessage(null), 3000);
    } catch (error) {
      console.error('[Settings] Error deleting module:', error);
      const errorMessage = error instanceof ApiError 
        ? error.message 
        : 'Failed to delete module';
      setModuleActionMessage({
        type: 'error',
        text: errorMessage
      });
    }
  };

  return (
    <div className="min-h-screen" style={{
      backgroundColor: '#f8fafc',
      padding: '18px'
    }}>
      {/* Page Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '15px'
      }}>
        <h1 style={{
          color: '#1e293b',
          fontWeight: 600,
          fontSize: '20px',
          marginBottom: 0
        }}>
          Settings
        </h1>
        <button
          onClick={handleBack}
          style={{
            backgroundColor: '#374151',
            color: '#ffffff',
            fontWeight: 500,
            padding: '5px 10px',
            fontSize: '12px',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            transition: 'background 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#111827';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#374151';
          }}
        >
          ← Back to Projects
        </button>
      </div>

      {/* Tab Navigation */}
      <div style={{
        display: 'flex',
        gap: '4px',
        marginBottom: '15px',
        borderBottom: '2px solid #e2e8f0'
      }}>
        <button
          onClick={() => setActiveTab('projects')}
          style={{
            backgroundColor: activeTab === 'projects' ? '#ffffff' : 'transparent',
            color: activeTab === 'projects' ? '#6366f1' : '#64748b',
            fontWeight: 600,
            padding: '8px 16px',
            fontSize: '12px',
            border: 'none',
            borderBottom: activeTab === 'projects' ? '2px solid #6366f1' : '2px solid transparent',
            borderRadius: '6px 6px 0 0',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            marginBottom: '-2px'
          }}
          onMouseEnter={(e) => {
            if (activeTab !== 'projects') {
              e.currentTarget.style.color = '#475569';
              e.currentTarget.style.backgroundColor = '#f8fafc';
            }
          }}
          onMouseLeave={(e) => {
            if (activeTab !== 'projects') {
              e.currentTarget.style.color = '#64748b';
              e.currentTarget.style.backgroundColor = 'transparent';
            }
          }}
        >
          <i className="fas fa-folder" style={{ marginRight: '6px' }} />
          Project Management
        </button>
        <button
          onClick={() => setActiveTab('modules')}
          style={{
            backgroundColor: activeTab === 'modules' ? '#ffffff' : 'transparent',
            color: activeTab === 'modules' ? '#6366f1' : '#64748b',
            fontWeight: 600,
            padding: '8px 16px',
            fontSize: '12px',
            border: 'none',
            borderBottom: activeTab === 'modules' ? '2px solid #6366f1' : '2px solid transparent',
            borderRadius: '6px 6px 0 0',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            marginBottom: '-2px'
          }}
          onMouseEnter={(e) => {
            if (activeTab !== 'modules') {
              e.currentTarget.style.color = '#475569';
              e.currentTarget.style.backgroundColor = '#f8fafc';
            }
          }}
          onMouseLeave={(e) => {
            if (activeTab !== 'modules') {
              e.currentTarget.style.color = '#64748b';
              e.currentTarget.style.backgroundColor = 'transparent';
            }
          }}
        >
          <i className="fas fa-cubes" style={{ marginRight: '6px' }} />
          Module Management
        </button>
      </div>

      {/* PROJECT MANAGEMENT TAB */}
      {activeTab === 'projects' && (
        <>
          {/* Subtitle */}
          <p style={{
            fontSize: '11px',
            color: '#64748b',
            marginBottom: '18px'
          }}>
            {isEditMode 
              ? 'Edit the details below for the selected project.'
              : 'Fill in the details below to add a new project to TAP.'}
          </p>

          {/* Loading State */}
          {isLoading && (
            <div
              style={{
                backgroundColor: '#f0f9ff',
                borderColor: '#bae6fd',
                color: '#0369a1',
                border: '1px solid',
                borderRadius: '4px',
                padding: '8px 12px',
                marginBottom: '12px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <i
                className="fas fa-spinner fa-spin"
                style={{
                  fontSize: '13px',
                  color: '#0284c7'
                }}
              />
              <span style={{ fontWeight: 500, fontSize: '11px' }}>Loading project data...</span>
            </div>
          )}

          {/* Action Message */}
          {actionMessage && (
            <div
              style={{
                backgroundColor: actionMessage.type === 'success' ? '#f0fdf4' : '#fef2f2',
                borderColor: actionMessage.type === 'success' ? '#bbf7d0' : '#fecaca',
                color: actionMessage.type === 'success' ? '#166534' : '#dc2626',
                border: '1px solid',
                borderRadius: '4px',
                padding: '8px 12px',
                marginBottom: '12px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <i
                className={actionMessage.type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'}
                style={{
                  fontSize: '13px',
                  color: actionMessage.type === 'success' ? '#10b981' : '#ef4444'
                }}
              />
              <span style={{ fontWeight: 500, fontSize: '11px' }}>{actionMessage.text}</span>
            </div>
          )}

          {/* Project Form Card */}
          <div
            style={{
              border: '1px solid #e2e8f0',
              borderRadius: '6px',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
              background: '#ffffff',
              animation: 'fadeInUp 0.6s ease-out'
            }}
          >
            {/* Card Header */}
            <div style={{
              backgroundColor: '#f8fafc',
              borderBottom: '1px solid #e2e8f0',
              padding: '10px 14px',
              borderRadius: '6px 6px 0 0'
            }}>
              <h4 style={{
                color: '#374151',
                fontWeight: 600,
                fontSize: '13px',
                marginBottom: 0
              }}>
                {isEditMode ? 'Edit Project' : 'Create New Project'}
              </h4>
            </div>

            {/* Card Body */}
            <div style={{
              padding: '14px',
              opacity: isLoading ? 0.5 : 1,
              pointerEvents: isLoading ? 'none' : 'auto'
            }}>
              <form onSubmit={handleSubmit}>
                {/* Row 1: Project Name and Owner */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(12, 1fr)',
                  gap: '12px',
                  marginBottom: '12px'
                }}>
                  {/* Project Name (6 cols) */}
                  <div style={{ gridColumn: 'span 6' }}>
                    <label
                      htmlFor="name"
                      style={{
                        display: 'block',
                        fontWeight: 500,
                        color: '#64748b',
                        marginBottom: '6px',
                        fontSize: '11px'
                      }}
                    >
                      Project Name *
                    </label>
                    <input
                      type="text"
                      id="name"
                      name="name"
                      value={formData.name}
                      onChange={handleInputChange}
                      style={{
                        width: '100%',
                        border: `2px solid ${errors.name ? '#ef4444' : '#e5e7eb'}`,
                        borderRadius: '6px',
                        padding: '8px',
                        fontSize: '11px',
                        transition: 'all 0.2s ease',
                        backgroundColor: '#ffffff',
                        outline: 'none',
                        height: '36px'
                      }}
                      onFocus={(e) => {
                        if (!errors.name) {
                          e.currentTarget.style.borderColor = '#6366f1';
                          e.currentTarget.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.1)';
                        }
                      }}
                      onBlur={(e) => {
                        if (!errors.name) {
                          e.currentTarget.style.borderColor = '#e5e7eb';
                          e.currentTarget.style.boxShadow = 'none';
                        }
                      }}
                      placeholder="Enter project name"
                    />
                    {errors.name && (
                      <div style={{
                        color: '#ef4444',
                        fontSize: '9px',
                        marginTop: '3px'
                      }}>
                        {errors.name}
                      </div>
                    )}
                  </div>

                  {/* Owner (6 cols) */}
                  <div style={{ gridColumn: 'span 6' }}>
                    <label
                      htmlFor="owner"
                      style={{
                        display: 'block',
                        fontWeight: 500,
                        color: '#64748b',
                        marginBottom: '6px',
                        fontSize: '11px'
                      }}
                    >
                      Owner *
                    </label>
                    <input
                      type="text"
                      id="owner"
                      name="owner"
                      value={formData.owner}
                      onChange={handleInputChange}
                      style={{
                        width: '100%',
                        border: `2px solid ${errors.owner ? '#ef4444' : '#e5e7eb'}`,
                        borderRadius: '6px',
                        padding: '8px',
                        fontSize: '11px',
                        transition: 'all 0.2s ease',
                        backgroundColor: '#ffffff',
                        outline: 'none',
                        height: '36px'
                      }}
                      onFocus={(e) => {
                        if (!errors.owner) {
                          e.currentTarget.style.borderColor = '#6366f1';
                          e.currentTarget.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.1)';
                        }
                      }}
                      onBlur={(e) => {
                        if (!errors.owner) {
                          e.currentTarget.style.borderColor = '#e5e7eb';
                          e.currentTarget.style.boxShadow = 'none';
                        }
                      }}
                      placeholder="Enter owner name"
                    />
                    {errors.owner && (
                      <div style={{
                        color: '#ef4444',
                        fontSize: '9px',
                        marginTop: '3px'
                      }}>
                        {errors.owner}
                      </div>
                    )}
                  </div>
                </div>

                {/* Row 2: Description (12 cols) */}
                <div style={{
                  marginBottom: '12px'
                }}>
                  <label
                    htmlFor="description"
                    style={{
                      display: 'block',
                      fontWeight: 500,
                      color: '#64748b',
                      marginBottom: '6px',
                      fontSize: '11px'
                    }}
                  >
                    Description *
                  </label>
                  <textarea
                    id="description"
                    name="description"
                    value={formData.description}
                    onChange={handleInputChange}
                    rows={3}
                    style={{
                      width: '100%',
                      border: `2px solid ${errors.description ? '#ef4444' : '#e5e7eb'}`,
                      borderRadius: '6px',
                      padding: '8px',
                      fontSize: '11px',
                      transition: 'all 0.2s ease',
                      backgroundColor: '#ffffff',
                      outline: 'none',
                      resize: 'vertical',
                      minHeight: '60px'
                    }}
                    onFocus={(e) => {
                      if (!errors.description) {
                        e.currentTarget.style.borderColor = '#6366f1';
                        e.currentTarget.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.1)';
                      }
                    }}
                    onBlur={(e) => {
                      if (!errors.description) {
                        e.currentTarget.style.borderColor = '#e5e7eb';
                        e.currentTarget.style.boxShadow = 'none';
                      }
                    }}
                    placeholder="Enter project description"
                  />
                  {errors.description && (
                    <div style={{
                      color: '#ef4444',
                      fontSize: '9px',
                      marginTop: '3px'
                    }}>
                      {errors.description}
                    </div>
                  )}
                </div>

                {/* Row 3: Repository URL (12 cols) */}
                <div style={{
                  marginBottom: '12px'
                }}>
                  <label
                    htmlFor="repositoryUrl"
                    style={{
                      display: 'block',
                      fontWeight: 500,
                      color: '#64748b',
                      marginBottom: '6px',
                      fontSize: '11px'
                    }}
                  >
                    Repository URL *
                  </label>
                  <input
                    type="url"
                    id="repositoryUrl"
                    name="repositoryUrl"
                    value={formData.repositoryUrl}
                    onChange={handleInputChange}
                    style={{
                      width: '100%',
                      border: `2px solid ${errors.repositoryUrl ? '#ef4444' : '#e5e7eb'}`,
                      borderRadius: '6px',
                      padding: '8px',
                      fontSize: '11px',
                      transition: 'all 0.2s ease',
                      backgroundColor: '#ffffff',
                      outline: 'none',
                      height: '36px'
                    }}
                    onFocus={(e) => {
                      if (!errors.repositoryUrl) {
                        e.currentTarget.style.borderColor = '#6366f1';
                        e.currentTarget.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.1)';
                      }
                    }}
                    onBlur={(e) => {
                      if (!errors.repositoryUrl) {
                        e.currentTarget.style.borderColor = '#e5e7eb';
                        e.currentTarget.style.boxShadow = 'none';
                      }
                    }}
                    placeholder="https://github.com/username/repository"
                  />
                  {errors.repositoryUrl && (
                    <div style={{
                      color: '#ef4444',
                      fontSize: '9px',
                      marginTop: '3px'
                    }}>
                      {errors.repositoryUrl}
                    </div>
                  )}
                </div>

                {/* Save Button */}
                <button
                  type="submit"
                  disabled={isSubmitting}
                  style={{
                    width: '100%',
                    backgroundColor: isSubmitting ? '#9ca3af' : '#059669',
                    borderColor: isSubmitting ? '#9ca3af' : '#059669',
                    color: '#ffffff',
                    fontWeight: 600,
                    padding: '10px',
                    fontSize: '12px',
                    border: '2px solid',
                    borderRadius: '6px',
                    cursor: isSubmitting ? 'not-allowed' : 'pointer',
                    transition: 'all 0.2s ease',
                    opacity: isSubmitting ? 0.7 : 1,
                    height: '36px'
                  }}
                  onMouseEnter={(e) => {
                    if (!isSubmitting) {
                      e.currentTarget.style.backgroundColor = '#047857';
                      e.currentTarget.style.borderColor = '#047857';
                      e.currentTarget.style.transform = 'translateY(-1px)';
                      e.currentTarget.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isSubmitting) {
                      e.currentTarget.style.backgroundColor = '#059669';
                      e.currentTarget.style.borderColor = '#059669';
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = 'none';
                    }
                  }}
                >
                  {isSubmitting 
                    ? (isEditMode ? 'Saving Project...' : 'Creating Project...')
                    : (isEditMode ? 'Save Project' : 'Create Project')}
                </button>
              </form>
            </div>
          </div>
        </>
      )}

      {/* MODULE MANAGEMENT TAB */}
      {activeTab === 'modules' && (
        <>
          {/* Subtitle */}
          <p style={{
            fontSize: '11px',
            color: '#64748b',
            marginBottom: '18px'
          }}>
            Manage modules for your projects. Select a project to view and edit its modules.
          </p>

          {/* Module Management Card */}
          <div
            style={{
              border: '1px solid #e2e8f0',
              borderRadius: '6px',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
              background: '#ffffff',
              animation: 'fadeInUp 0.6s ease-out'
            }}
          >
            {/* Card Header */}
            <div style={{
              backgroundColor: '#f8fafc',
              borderBottom: '1px solid #e2e8f0',
              padding: '10px 14px',
              borderRadius: '6px 6px 0 0'
            }}>
              <h4 style={{
                color: '#374151',
                fontWeight: 600,
                fontSize: '13px',
                marginBottom: 0
              }}>
                Select Project
              </h4>
            </div>

            {/* Card Body - Project Selection */}
            <div style={{ padding: '14px' }}>
              {isLoadingProjects ? (
                <div style={{
                  textAlign: 'center',
                  padding: '20px',
                  color: '#64748b',
                  fontSize: '11px'
                }}>
                  <i className="fas fa-spinner fa-spin" style={{ marginRight: '6px' }} />
                  Loading projects...
                </div>
              ) : projects.length === 0 ? (
                <div style={{
                  textAlign: 'center',
                  padding: '20px',
                  color: '#94a3b8',
                  fontSize: '11px'
                }}>
                  No projects available. Create a project first in the Project Management tab.
                </div>
              ) : (
                <div style={{ marginBottom: '14px' }}>
                  <label
                    htmlFor="project-select"
                    style={{
                      display: 'block',
                      fontWeight: 500,
                      color: '#64748b',
                      marginBottom: '6px',
                      fontSize: '11px'
                    }}
                  >
                    Choose Project *
                  </label>
                  <select
                    id="project-select"
                    value={selectedProjectId}
                    onChange={(e) => {
                      setSelectedProjectId(e.target.value);
                      setShowAddModule(false);
                      setEditingModule(null);
                      setModuleActionMessage(null);
                    }}
                    style={{
                      width: '100%',
                      border: '2px solid #e5e7eb',
                      borderRadius: '6px',
                      padding: '8px',
                      fontSize: '11px',
                      backgroundColor: '#ffffff',
                      outline: 'none',
                      cursor: 'pointer',
                      height: '36px',
                      transition: 'all 0.2s ease'
                    }}
                    onFocus={(e) => {
                      e.currentTarget.style.borderColor = '#6366f1';
                      e.currentTarget.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.1)';
                    }}
                    onBlur={(e) => {
                      e.currentTarget.style.borderColor = '#e5e7eb';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  >
                    <option value="">-- Select a project --</option>
                    {projects.map((project) => (
                      <option key={project.id} value={project.id}>
                        {project.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>

          {/* Modules Card - Only show when project is selected */}
          {selectedProjectId && (
            <div
              style={{
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
                background: '#ffffff',
                marginTop: '12px',
                animation: 'fadeInUp 0.6s ease-out'
              }}
            >
              {/* Card Header */}
              <div style={{
                backgroundColor: '#f8fafc',
                borderBottom: '1px solid #e2e8f0',
                padding: '10px 14px',
                borderRadius: '6px 6px 0 0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <h4 style={{
                  color: '#374151',
                  fontWeight: 600,
                  fontSize: '13px',
                  marginBottom: 0
                }}>
                  Modules for {projects.find(p => p.id === selectedProjectId)?.name}
                </h4>
                <button
                  onClick={() => {
                    setShowAddModule(!showAddModule);
                    setNewModule({ name: '', description: '' });
                    setModuleActionMessage(null);
                  }}
                  style={{
                    backgroundColor: '#6366f1',
                    borderColor: '#6366f1',
                    color: '#ffffff',
                    fontWeight: 500,
                    padding: '4px 10px',
                    fontSize: '11px',
                    border: '1px solid',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#4f46e5';
                    e.currentTarget.style.borderColor = '#4f46e5';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#6366f1';
                    e.currentTarget.style.borderColor = '#6366f1';
                  }}
                >
                  {showAddModule ? '✕ Cancel' : '+ Add New Module'}
                </button>
              </div>

              {/* Card Body */}
              <div style={{ padding: '14px' }}>
                {/* Module Action Message */}
                {moduleActionMessage && (
                  <div
                    style={{
                      backgroundColor: moduleActionMessage.type === 'success' ? '#f0fdf4' : '#fef2f2',
                      borderColor: moduleActionMessage.type === 'success' ? '#bbf7d0' : '#fecaca',
                      color: moduleActionMessage.type === 'success' ? '#166534' : '#dc2626',
                      border: '1px solid',
                      borderRadius: '4px',
                      padding: '8px 12px',
                      marginBottom: '12px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      fontSize: '11px'
                    }}
                  >
                    <i
                      className={moduleActionMessage.type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'}
                      style={{ fontSize: '13px' }}
                    />
                    <span style={{ fontWeight: 500 }}>{moduleActionMessage.text}</span>
                  </div>
                )}

                {/* Add Module Form */}
                {showAddModule && (
                  <div style={{
                    backgroundColor: '#f8fafc',
                    border: '1px solid #e2e8f0',
                    borderRadius: '4px',
                    padding: '12px',
                    marginBottom: '12px'
                  }}>
                    <div style={{ marginBottom: '10px' }}>
                      <label style={{
                        display: 'block',
                        fontWeight: 500,
                        color: '#64748b',
                        marginBottom: '4px',
                        fontSize: '11px'
                      }}>
                        Module Name *
                      </label>
                      <input
                        type="text"
                        value={newModule.name}
                        onChange={(e) => setNewModule(prev => ({ ...prev, name: e.target.value }))}
                        placeholder="Enter module name"
                        style={{
                          width: '100%',
                          border: '2px solid #e5e7eb',
                          borderRadius: '4px',
                          padding: '6px 8px',
                          fontSize: '11px',
                          outline: 'none',
                          height: '32px'
                        }}
                        onFocus={(e) => {
                          e.currentTarget.style.borderColor = '#6366f1';
                          e.currentTarget.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.1)';
                        }}
                        onBlur={(e) => {
                          e.currentTarget.style.borderColor = '#e5e7eb';
                          e.currentTarget.style.boxShadow = 'none';
                        }}
                      />
                    </div>
                    <div style={{ marginBottom: '10px' }}>
                      <label style={{
                        display: 'block',
                        fontWeight: 500,
                        color: '#64748b',
                        marginBottom: '4px',
                        fontSize: '11px'
                      }}>
                        Description
                      </label>
                      <textarea
                        value={newModule.description}
                        onChange={(e) => setNewModule(prev => ({ ...prev, description: e.target.value }))}
                        placeholder="Enter module description (optional)"
                        rows={2}
                        style={{
                          width: '100%',
                          border: '2px solid #e5e7eb',
                          borderRadius: '4px',
                          padding: '6px 8px',
                          fontSize: '11px',
                          outline: 'none',
                          resize: 'vertical',
                          minHeight: '48px'
                        }}
                        onFocus={(e) => {
                          e.currentTarget.style.borderColor = '#6366f1';
                          e.currentTarget.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.1)';
                        }}
                        onBlur={(e) => {
                          e.currentTarget.style.borderColor = '#e5e7eb';
                          e.currentTarget.style.boxShadow = 'none';
                        }}
                      />
                    </div>
                    <button
                      onClick={handleAddModule}
                      style={{
                        backgroundColor: '#059669',
                        borderColor: '#059669',
                        color: '#ffffff',
                        fontWeight: 500,
                        padding: '6px 12px',
                        fontSize: '11px',
                        border: '1px solid',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = '#047857';
                        e.currentTarget.style.borderColor = '#047857';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = '#059669';
                        e.currentTarget.style.borderColor = '#059669';
                      }}
                    >
                      Add Module
                    </button>
                  </div>
                )}

                {/* Loading State */}
                {isLoadingModules && (
                  <div style={{
                    textAlign: 'center',
                    padding: '20px',
                    color: '#64748b',
                    fontSize: '11px'
                  }}>
                    <i className="fas fa-spinner fa-spin" style={{ marginRight: '6px' }} />
                    Loading modules...
                  </div>
                )}

                {/* Error State */}
                {moduleError && !isLoadingModules && (
                  <div style={{
                    backgroundColor: '#fef2f2',
                    borderColor: '#fecaca',
                    color: '#dc2626',
                    border: '1px solid',
                    borderRadius: '4px',
                    padding: '8px 12px',
                    fontSize: '11px'
                  }}>
                    <i className="fas fa-exclamation-circle" style={{ marginRight: '6px' }} />
                    {moduleError}
                  </div>
                )}

                {/* Module List */}
                {!isLoadingModules && !moduleError && (
                  <>
                    {modules.length === 0 ? (
                      <div style={{
                        textAlign: 'center',
                        padding: '20px',
                        color: '#94a3b8',
                        fontSize: '11px'
                      }}>
                        No modules added yet. Click "+ Add New Module" to get started.
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {modules.map((module) => (
                          <div
                            key={module.id}
                            style={{
                              border: '1px solid #e2e8f0',
                              borderRadius: '4px',
                              padding: '10px',
                              backgroundColor: editingModule?.id === module.id ? '#f0f9ff' : '#ffffff',
                              transition: 'all 0.2s'
                            }}
                          >
                            {editingModule?.id === module.id ? (
                              // Edit Mode
                              <>
                                <div style={{ marginBottom: '8px' }}>
                                  <label style={{
                                    display: 'block',
                                    fontWeight: 500,
                                    color: '#64748b',
                                    marginBottom: '4px',
                                    fontSize: '10px'
                                  }}>
                                    Module Name *
                                  </label>
                                  <input
                                    type="text"
                                    value={editingModule.name}
                                    onChange={(e) => setEditingModule(prev => prev ? { ...prev, name: e.target.value } : null)}
                                    style={{
                                      width: '100%',
                                      border: '2px solid #e5e7eb',
                                      borderRadius: '4px',
                                      padding: '6px 8px',
                                      fontSize: '11px',
                                      outline: 'none',
                                      height: '32px'
                                    }}
                                    onFocus={(e) => {
                                      e.currentTarget.style.borderColor = '#6366f1';
                                      e.currentTarget.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.1)';
                                    }}
                                    onBlur={(e) => {
                                      e.currentTarget.style.borderColor = '#e5e7eb';
                                      e.currentTarget.style.boxShadow = 'none';
                                    }}
                                  />
                                </div>
                                <div style={{ marginBottom: '8px' }}>
                                  <label style={{
                                    display: 'block',
                                    fontWeight: 500,
                                    color: '#64748b',
                                    marginBottom: '4px',
                                    fontSize: '10px'
                                  }}>
                                    Description
                                  </label>
                                  <textarea
                                    value={editingModule.description}
                                    onChange={(e) => setEditingModule(prev => prev ? { ...prev, description: e.target.value } : null)}
                                    rows={2}
                                    style={{
                                      width: '100%',
                                      border: '2px solid #e5e7eb',
                                      borderRadius: '4px',
                                      padding: '6px 8px',
                                      fontSize: '11px',
                                      outline: 'none',
                                      resize: 'vertical',
                                      minHeight: '48px'
                                    }}
                                    onFocus={(e) => {
                                      e.currentTarget.style.borderColor = '#6366f1';
                                      e.currentTarget.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.1)';
                                    }}
                                    onBlur={(e) => {
                                      e.currentTarget.style.borderColor = '#e5e7eb';
                                      e.currentTarget.style.boxShadow = 'none';
                                    }}
                                  />
                                </div>
                                <div style={{ display: 'flex', gap: '6px' }}>
                                  <button
                                    onClick={() => handleEditModule(module.id)}
                                    style={{
                                      backgroundColor: '#059669',
                                      borderColor: '#059669',
                                      color: '#ffffff',
                                      fontWeight: 500,
                                      padding: '4px 10px',
                                      fontSize: '10px',
                                      border: '1px solid',
                                      borderRadius: '4px',
                                      cursor: 'pointer',
                                      transition: 'all 0.2s'
                                    }}
                                    onMouseEnter={(e) => {
                                      e.currentTarget.style.backgroundColor = '#047857';
                                    }}
                                    onMouseLeave={(e) => {
                                      e.currentTarget.style.backgroundColor = '#059669';
                                    }}
                                  >
                                    Save
                                  </button>
                                  <button
                                    onClick={() => setEditingModule(null)}
                                    style={{
                                      backgroundColor: '#6b7280',
                                      borderColor: '#6b7280',
                                      color: '#ffffff',
                                      fontWeight: 500,
                                      padding: '4px 10px',
                                      fontSize: '10px',
                                      border: '1px solid',
                                      borderRadius: '4px',
                                      cursor: 'pointer',
                                      transition: 'all 0.2s'
                                    }}
                                    onMouseEnter={(e) => {
                                      e.currentTarget.style.backgroundColor = '#4b5563';
                                    }}
                                    onMouseLeave={(e) => {
                                      e.currentTarget.style.backgroundColor = '#6b7280';
                                    }}
                                  >
                                    Cancel
                                  </button>
                                </div>
                              </>
                            ) : (
                              // View Mode
                              <>
                                <div style={{
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'flex-start',
                                  marginBottom: '6px'
                                }}>
                                  <div style={{ flex: 1 }}>
                                    <h5 style={{
                                      color: '#1e293b',
                                      fontWeight: 600,
                                      fontSize: '12px',
                                      marginBottom: '4px'
                                    }}>
                                      {module.name}
                                    </h5>
                                    {module.description && (
                                      <p style={{
                                        color: '#64748b',
                                        fontSize: '10px',
                                        marginBottom: 0,
                                        lineHeight: '1.4'
                                      }}>
                                        {module.description}
                                      </p>
                                    )}
                                  </div>
                                  <div style={{ display: 'flex', gap: '6px', marginLeft: '12px' }}>
                                    <button
                                      onClick={() => setEditingModule({
                                        id: module.id,
                                        name: module.name,
                                        description: module.description || ''
                                      })}
                                      style={{
                                        backgroundColor: '#3b82f6',
                                        borderColor: '#3b82f6',
                                        color: '#ffffff',
                                        fontWeight: 500,
                                        padding: '4px 8px',
                                        fontSize: '10px',
                                        border: '1px solid',
                                        borderRadius: '4px',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s'
                                      }}
                                      onMouseEnter={(e) => {
                                        e.currentTarget.style.backgroundColor = '#2563eb';
                                      }}
                                      onMouseLeave={(e) => {
                                        e.currentTarget.style.backgroundColor = '#3b82f6';
                                      }}
                                    >
                                      Edit
                                    </button>
                                    <button
                                      onClick={() => handleDeleteModule(module.id)}
                                      style={{
                                        backgroundColor: '#ef4444',
                                        borderColor: '#ef4444',
                                        color: '#ffffff',
                                        fontWeight: 500,
                                        padding: '4px 8px',
                                        fontSize: '10px',
                                        border: '1px solid',
                                        borderRadius: '4px',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s'
                                      }}
                                      onMouseEnter={(e) => {
                                        e.currentTarget.style.backgroundColor = '#dc2626';
                                      }}
                                      onMouseLeave={(e) => {
                                        e.currentTarget.style.backgroundColor = '#ef4444';
                                      }}
                                    >
                                      Delete
                                    </button>
                                  </div>
                                </div>
                              </>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default SettingsPage;
