import React, { useState, useEffect } from 'react';
import {
  makeStyles,
  shorthands,
  Spinner,
  Accordion,
  AccordionItem,
  AccordionHeader,
  AccordionPanel,
} from '@fluentui/react-components';
import Card from './Card';
import Button from './Button';
import Text from './Text';

const useStyles = makeStyles({
  container: {
    display: 'grid',
    gap: '24px',
    gridTemplateColumns: '280px 1fr',
    '@media(max-width: 992px)': {
      gridTemplateColumns: '1fr',
    },
  },
  menu: {
    display: 'grid',
    gap: '8px',
  },
  details: {
    display: 'grid',
    gap: '16px',
  },
  infoSection: {
    display: 'grid',
    gap: '8px',
  },
  hierarchyCard: {
    ...shorthands.padding('16px'),
    borderRadius: '16px',
    backgroundColor: 'rgba(117,172,242,0.12)',
    border: '1px solid rgba(117,172,242,0.25)',
  },
});

const ContextualExpertWeb = () => {
  const styles = useStyles();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [experts, setExperts] = useState([]);
  const [selectedExpert, setSelectedExpert] = useState(null);
  const [expertiseModel, setExpertiseModel] = useState(null);

  useEffect(() => {
    const fetchExperts = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/contextual/experts');
        const data = await response.json();

        if (data.success) {
          setExperts(data.experts);
          if (data.experts.length > 0) {
            setSelectedExpert(data.experts[0]);
            fetchExpertiseModel(data.experts[0].id);
          }
        } else {
          setError(data.error || 'Failed to fetch contextual experts');
        }
      } catch (err) {
        setError('Error fetching contextual experts: ' + err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchExperts();
  }, []);

  const fetchExpertiseModel = async (expertId) => {
    try {
      const response = await fetch(`/api/contextual/expertise-model/${expertId}`);
      const data = await response.json();

      if (data.success) {
        setExpertiseModel(data.expertise_model);
      } else {
        setError(data.error || 'Failed to fetch expertise model');
      }
    } catch (err) {
      setError('Error fetching expertise model: ' + err.message);
    }
  };

  if (loading) {
    return <Spinner size="large" label="Loading contextual experts" />;
  }

  if (error) {
    return (
      <div className={styles.hierarchyCard}>
        <Text color="danger">{error}</Text>
      </div>
    );
  }

  const renderExpertiseAccordion = () => {
    if (!expertiseModel) return null;

    const sections = [
      { key: 'role', label: 'Role', content: expertiseModel.role },
      { key: 'formal_education', label: 'Formal education', content: expertiseModel.formal_education },
      { key: 'certifications', label: 'Certifications', content: expertiseModel.certifications },
      { key: 'job_training', label: 'Job training', content: expertiseModel.job_training },
      { key: 'skills', label: 'Skills', content: expertiseModel.skills },
      { key: 'related_tasks', label: 'Related tasks', content: expertiseModel.related_tasks },
      { key: 'related_roles', label: 'Related roles', content: expertiseModel.related_roles },
    ];

    return (
      <Accordion collapsible>
        {sections.map((section) => (
          <AccordionItem key={section.key} value={section.key}>
            <AccordionHeader>{section.label}</AccordionHeader>
            <AccordionPanel>
              {Array.isArray(section.content) ? (
                <ul>
                  {section.content.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              ) : (
                <Text>{section.content}</Text>
              )}
            </AccordionPanel>
          </AccordionItem>
        ))}
      </Accordion>
    );
  };

  return (
    <div className={styles.container}>
      <Card>
        <Card.Body className={styles.menu}>
          <Text fontWeight="semibold">Contextual experts</Text>
          {experts.map((expert) => (
            <Button
              key={expert.id}
              variant={selectedExpert?.id === expert.id ? 'primary' : 'subtle'}
              onClick={() => {
                setSelectedExpert(expert);
                fetchExpertiseModel(expert.id);
              }}
            >
              {expert.label}
            </Button>
          ))}
        </Card.Body>
      </Card>

      <div className={styles.details}>
        {selectedExpert && (
          <Card>
            <Card.Body className={styles.infoSection}>
              <Text fontSize="lg" fontWeight="semibold">
                {selectedExpert.label}
              </Text>
              <Text color="muted">{selectedExpert.description}</Text>
              {renderExpertiseAccordion()}
            </Card.Body>
          </Card>
        )}

        <div className={styles.hierarchyCard}>
          <Text fontWeight="semibold">Branch structure</Text>
          <Text fontSize="sm" color="muted">
            Context experts follow the UKG branch pattern:
          </Text>
          <ul>
            <li>Mega branches (4)</li>
            <li>Large branches (4 per mega)</li>
            <li>Medium branches (4 per large)</li>
            <li>Small branches (4 per medium)</li>
            <li>Granular branches (as needed)</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ContextualExpertWeb;
