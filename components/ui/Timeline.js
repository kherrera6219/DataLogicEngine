
import React, { useState, useEffect } from 'react';
import { Card, Button, Badge, ProgressBar } from 'react-bootstrap';

const Timeline = ({ initialData, timelineType }) => {
  const [timelineData, setTimelineData] = useState(initialData || []);
  const [loading, setLoading] = useState(!initialData);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('timeline'); // 'timeline' or 'calendar' or 'gantt'
  const [filterType, setFilterType] = useState('all');
  
  // Fetch timeline data if not provided initially
  useEffect(() => {
    if (!initialData) {
      fetchTimelineData();
    }
  }, [initialData, timelineType]);
  
  const fetchTimelineData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Determine endpoint based on timelineType
      let endpoint = '/api/time';
      
      if (timelineType === 'historical') {
        endpoint = '/api/time/historical';
      } else if (timelineType === 'career') {
        endpoint = `/api/time/career/${timelineType.split('_')[1]}`;
      } else if (timelineType === 'project') {
        endpoint = `/api/time/project/${timelineType.split('_')[1]}`;
      }
      
      const response = await fetch(endpoint);
      const data = await response.json();
      
      if (data.success) {
        if (timelineType === 'historical') {
          setTimelineData(data.periods || []);
        } else if (timelineType === 'career') {
          setTimelineData(data.career_stages || []);
        } else if (timelineType === 'project') {
          setTimelineData({
            project: data.project,
            tasks: data.tasks || [],
            milestones: data.milestones || [],
            completionPercentage: data.completion_percentage || 0
          });
        } else {
          setTimelineData(data.time_contexts || []);
        }
      } else {
        setError(data.error || 'Error fetching timeline data');
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  const formatDate = (dateString) => {
    if (!dateString) return 'Present';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };
  
  const getStatusBadge = (status) => {
    if (!status) return null;
    
    let variant = 'secondary';
    
    switch(status.toLowerCase()) {
      case 'completed':
        variant = 'success';
        break;
      case 'in_progress':
        variant = 'primary';
        break;
      case 'not_started':
        variant = 'light';
        break;
      case 'delayed':
        variant = 'warning';
        break;
      case 'blocked':
        variant = 'danger';
        break;
    }
    
    return <Badge bg={variant}>{status.replace('_', ' ')}</Badge>;
  };
  
  const getTimelineItem = (item, index) => {
    return (
      <div key={item.uid || index} className="timeline-item">
        <div className="timeline-icon">
          {item.time_type === 'milestone' ? (
            <i className="bi bi-flag-fill text-warning"></i>
          ) : item.time_type === 'career_stage' ? (
            <i className="bi bi-briefcase-fill text-primary"></i>
          ) : item.time_type === 'historical' ? (
            <i className="bi bi-clock-history text-info"></i>
          ) : item.time_type === 'project' ? (
            <i className="bi bi-kanban text-success"></i>
          ) : (
            <i className="bi bi-calendar-event text-secondary"></i>
          )}
        </div>
        <div className="timeline-content">
          <Card>
            <Card.Header className="d-flex justify-content-between align-items-center">
              <span>{item.name}</span>
              {item.attributes && item.attributes.status && 
                getStatusBadge(item.attributes.status)
              }
            </Card.Header>
            <Card.Body>
              <div className="small mb-2">
                <i className="bi bi-calendar me-1"></i>
                {formatDate(item.start_date)} - {formatDate(item.end_date)}
              </div>
              
              {item.attributes && item.attributes.description && (
                <p className="mb-2">{item.attributes.description}</p>
              )}
              
              {item.attributes && item.attributes.assignee && (
                <div className="small mb-2">
                  <i className="bi bi-person me-1"></i>
                  Assignee: {item.attributes.assignee}
                </div>
              )}
              
              {item.attributes && item.attributes.skills_gained && (
                <div className="mt-2">
                  <small className="text-muted">Skills:</small>
                  <div>
                    {item.attributes.skills_gained.map((skill, i) => (
                      <Badge key={i} bg="info" className="me-1 mb-1">{skill}</Badge>
                    ))}
                  </div>
                </div>
              )}
              
              {item.attributes && item.attributes.roles && (
                <div className="mt-2">
                  <small className="text-muted">Roles:</small>
                  <div>
                    {item.attributes.roles.map((role, i) => (
                      <Badge key={i} bg="secondary" className="me-1 mb-1">{role}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </Card.Body>
          </Card>
        </div>
      </div>
    );
  };
  
  const renderHistoricalTimeline = () => {
    return (
      <div className="historical-timeline">
        {timelineData.map((period, index) => getTimelineItem(period, index))}
      </div>
    );
  };
  
  const renderCareerTimeline = () => {
    return (
      <div className="career-timeline">
        {timelineData.map((stage, index) => getTimelineItem(stage, index))}
      </div>
    );
  };
  
  const renderProjectTimeline = () => {
    if (!timelineData.project) return <div>No project data available</div>;
    
    const { project, tasks, milestones, completionPercentage } = timelineData;
    
    return (
      <div className="project-timeline">
        <Card className="mb-4">
          <Card.Header>
            <h5>{project.name}</h5>
          </Card.Header>
          <Card.Body>
            <div className="d-flex justify-content-between mb-2">
              <div>
                <i className="bi bi-calendar me-1"></i>
                {formatDate(project.start_date)} - {formatDate(project.end_date)}
              </div>
              {project.attributes && project.attributes.status && 
                getStatusBadge(project.attributes.status)
              }
            </div>
            
            {project.attributes && project.attributes.description && (
              <p>{project.attributes.description}</p>
            )}
            
            <div className="mt-3">
              <div className="d-flex justify-content-between mb-1">
                <span>Progress:</span>
                <span>{completionPercentage}%</span>
              </div>
              <ProgressBar now={completionPercentage} />
            </div>
          </Card.Body>
        </Card>
        
        <div className="d-flex justify-content-center mb-4">
          <div className="btn-group">
            <Button 
              variant={filterType === 'all' ? 'primary' : 'outline-primary'}
              onClick={() => setFilterType('all')}
            >
              All
            </Button>
            <Button 
              variant={filterType === 'task' ? 'primary' : 'outline-primary'}
              onClick={() => setFilterType('task')}
            >
              Tasks
            </Button>
            <Button 
              variant={filterType === 'milestone' ? 'primary' : 'outline-primary'}
              onClick={() => setFilterType('milestone')}
            >
              Milestones
            </Button>
          </div>
        </div>
        
        <div className="timeline-container">
          {filterType === 'all' && (
            <>
              {[...tasks, ...milestones]
                .sort((a, b) => new Date(a.start_date) - new Date(b.start_date))
                .map((item, index) => getTimelineItem(item, index))
              }
            </>
          )}
          
          {filterType === 'task' && (
            <>
              {tasks.map((task, index) => getTimelineItem(task, index))}
            </>
          )}
          
          {filterType === 'milestone' && (
            <>
              {milestones.map((milestone, index) => getTimelineItem(milestone, index))}
            </>
          )}
        </div>
      </div>
    );
  };
  
  if (loading) {
    return (
      <div className="text-center my-5">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Loading timeline...</span>
        </div>
        <p className="mt-2">Loading timeline data...</p>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="alert alert-danger">
        <i className="bi bi-exclamation-triangle me-2"></i>
        {error}
      </div>
    );
  }
  
  return (
    <div className="timeline-component">
      <div className="d-flex justify-content-between mb-4">
        <h3>
          {timelineType === 'historical' && 'Historical Timeline'}
          {timelineType === 'career' && 'Career Timeline'}
          {timelineType === 'project' && 'Project Timeline'}
          {!timelineType && 'Timeline'}
        </h3>
        
        <div className="btn-group">
          <Button 
            variant={viewMode === 'timeline' ? 'primary' : 'outline-primary'}
            onClick={() => setViewMode('timeline')}
          >
            <i className="bi bi-list me-1"></i> Timeline
          </Button>
          <Button 
            variant={viewMode === 'calendar' ? 'primary' : 'outline-primary'}
            onClick={() => setViewMode('calendar')}
          >
            <i className="bi bi-calendar3 me-1"></i> Calendar
          </Button>
          <Button 
            variant={viewMode === 'gantt' ? 'primary' : 'outline-primary'}
            onClick={() => setViewMode('gantt')}
          >
            <i className="bi bi-bar-chart me-1"></i> Gantt
          </Button>
        </div>
      </div>
      
      {viewMode === 'timeline' && (
        <div className="timeline-container">
          {timelineType === 'historical' && renderHistoricalTimeline()}
          {timelineType === 'career' && renderCareerTimeline()}
          {timelineType === 'project' && renderProjectTimeline()}
          {!timelineType && timelineData.map((item, index) => getTimelineItem(item, index))}
          
          {Array.isArray(timelineData) && timelineData.length === 0 && (
            <div className="text-center my-5">
              <i className="bi bi-calendar-x display-4 text-muted"></i>
              <p className="mt-3">No timeline data available</p>
            </div>
          )}
        </div>
      )}
      
      {viewMode === 'calendar' && (
        <div className="calendar-view">
          <div className="alert alert-info">
            <i className="bi bi-info-circle me-2"></i>
            Calendar view implementation will be added in the next iteration.
          </div>
        </div>
      )}
      
      {viewMode === 'gantt' && (
        <div className="gantt-view">
          <div className="alert alert-info">
            <i className="bi bi-info-circle me-2"></i>
            Gantt chart view implementation will be added in the next iteration.
          </div>
        </div>
      )}
      
      <style jsx>{`
        .timeline-container {
          position: relative;
          padding: 20px 0;
        }
        
        .timeline-container::before {
          content: '';
          position: absolute;
          top: 0;
          bottom: 0;
          left: 20px;
          width: 4px;
          background: #e5e5e5;
        }
        
        .timeline-item {
          position: relative;
          margin-bottom: 30px;
          padding-left: 45px;
        }
        
        .timeline-icon {
          position: absolute;
          left: 0;
          top: 5px;
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background: #fff;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 3px solid #e5e5e5;
          z-index: 1;
        }
        
        .timeline-content {
          padding-bottom: 10px;
        }
      `}</style>
    </div>
  );
};

export default Timeline;
