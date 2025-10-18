import React from 'react';
import { makeStyles, ProgressBar } from '@fluentui/react-components';
import Card from './Card';
import Text from './Text';

const useStyles = makeStyles({
  list: {
    display: 'grid',
    gap: '16px',
  },
  item: {
    display: 'grid',
    gap: '8px',
  },
  meta: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    color: 'var(--colorNeutralForeground3)',
    fontSize: '0.85rem',
  },
  section: {
    display: 'grid',
    gap: '12px',
  },
});

const Timeline = ({ initialData = [], timelineType = 'historical', projectData, careerData }) => {
  const styles = useStyles();

  if (timelineType === 'project' && projectData) {
    return (
      <div className={styles.section}>
        <Card>
          <Card.Body className={styles.item}>
            <Text fontSize="lg" fontWeight="semibold">
              {projectData.project?.name || 'Project'}
            </Text>
            <Text color="muted">{projectData.project?.description}</Text>
            <ProgressBar value={projectData.completionPercentage || 0} max={100} />
            <Text fontSize="sm" color="muted">
              {projectData.completionPercentage || 0}% complete
            </Text>
          </Card.Body>
        </Card>

        <Card>
          <Card.Body>
            <Text fontWeight="semibold">Upcoming milestones</Text>
            <div className={styles.list}>
              {(projectData.milestones || []).map((milestone, index) => (
                <div key={index} className={styles.item}>
                  <Text fontWeight="semibold">{milestone.title}</Text>
                  <div className={styles.meta}>
                    <span>{milestone.owner}</span>
                    <span>{milestone.due_date && new Date(milestone.due_date).toLocaleDateString()}</span>
                  </div>
                  <Text fontSize="sm" color="muted">
                    {milestone.description}
                  </Text>
                </div>
              ))}
            </div>
          </Card.Body>
        </Card>
      </div>
    );
  }

  if (timelineType === 'career' && careerData) {
    return (
      <div className={styles.list}>
        {careerData.map((stage, index) => (
          <Card key={index}>
            <Card.Body className={styles.item}>
              <Text fontWeight="semibold">{stage.title}</Text>
              <div className={styles.meta}>
                <span>{stage.role}</span>
                <span>
                  {stage.start_date && new Date(stage.start_date).toLocaleDateString()} –
                  {stage.end_date ? ` ${new Date(stage.end_date).toLocaleDateString()}` : ' Present'}
                </span>
              </div>
              <Text fontSize="sm" color="muted">
                {stage.description}
              </Text>
            </Card.Body>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className={styles.list}>
      {initialData.map((event, index) => (
        <Card key={index}>
          <Card.Body className={styles.item}>
            <Text fontWeight="semibold">{event.title}</Text>
            <div className={styles.meta}>
              <span>{event.period}</span>
              <span>{event.region}</span>
            </div>
            <Text fontSize="sm" color="muted">
              {event.description}
            </Text>
          </Card.Body>
        </Card>
      ))}
    </div>
  );
};

export default Timeline;
