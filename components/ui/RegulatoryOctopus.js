import React, { useEffect, useState } from 'react';
import { Card, Button, Badge, Text } from './index';
import {
  MessageBar,
  MessageBarBody,
  MessageBarTitle,
  Spinner,
  makeStyles,
  mergeClasses,
  shorthands,
} from '@fluentui/react-components';
import {
  bundleIcon,
  ChevronDown20Filled,
  ChevronDown20Regular,
  ChevronUp20Filled,
  ChevronUp20Regular,
  Document24Filled,
  Document24Regular,
} from '@fluentui/react-icons';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  meta: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '10px',
  },
  section: {
    display: 'flex',
    flexDirection: 'column',
    gap: '14px',
  },
  collapsible: {
    borderRadius: '16px',
    backgroundColor: 'var(--colorNeutralBackground3)',
    border: '1px solid rgba(255,255,255,0.04)',
  },
  collapsibleHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    cursor: 'pointer',
    gap: '12px',
    ...shorthands.padding('12px', '16px'),
  },
  collapsibleBody: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    ...shorthands.padding('0', '16px', '16px'),
  },
  requirementList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  requirementCard: {
    cursor: 'pointer',
  },
});

const ExpandIcon = bundleIcon(ChevronUp20Filled, ChevronUp20Regular);
const CollapseIcon = bundleIcon(ChevronDown20Filled, ChevronDown20Regular);
const DocumentIcon = bundleIcon(Document24Filled, Document24Regular);

const criticalityColorMap = {
  high: 'danger',
  medium: 'warning',
  low: 'brand',
};

const RegulatoryOctopus = ({ frameworkUid, onNodeClick }) => {
  const styles = useStyles();
  const [octopusData, setOctopusData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedNodes, setExpandedNodes] = useState({});

  useEffect(() => {
    if (!frameworkUid) {
      setOctopusData(null);
      return;
    }

    const fetchOctopusData = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/regulatory/octopus/${frameworkUid}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch octopus data: ${response.statusText}`);
        }
        const data = await response.json();
        if (data.status === 'success') {
          setOctopusData(data.octopus);
        } else {
          throw new Error(data.message || 'Failed to load regulatory octopus data');
        }
      } catch (err) {
        setError(err.message || 'An error occurred while fetching the octopus data');
        setOctopusData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchOctopusData();
  }, [frameworkUid]);

  const toggleExpandNode = (nodeId) => {
    setExpandedNodes((prev) => ({
      ...prev,
      [nodeId]: !prev[nodeId],
    }));
  };

  if (loading) {
    return (
      <div style={{ minHeight: 320, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Spinner appearance="primary" size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <MessageBar intent="error">
        <MessageBarBody>
          <MessageBarTitle>Unable to load regulatory framework</MessageBarTitle>
          {error}
        </MessageBarBody>
      </MessageBar>
    );
  }

  if (!octopusData) {
    return (
      <MessageBar intent="info">
        <MessageBarBody>Select a regulatory framework to view its hierarchical structure.</MessageBarBody>
      </MessageBar>
    );
  }

  return (
    <div className={styles.container}>
      <Card appearance="subtle">
        <Card.Header
          header={<Text fontWeight="semibold">{octopusData.mega_framework.label}</Text>}
          description={<Text fontSize="sm">{octopusData.mega_framework.description}</Text>}
          action={<DocumentIcon />}
        />
        <Card.Body>
          <div className={styles.meta}>
            {octopusData.mega_framework.framework_type && (
              <Badge appearance="tint" color="brand">
                {octopusData.mega_framework.framework_type}
              </Badge>
            )}
            {octopusData.mega_framework.issuing_authority && (
              <Badge appearance="tint" color="brand">
                Authority: {octopusData.mega_framework.issuing_authority}
              </Badge>
            )}
            {octopusData.mega_framework.effective_date && (
              <Badge appearance="tint" color="brand">
                Effective: {new Date(octopusData.mega_framework.effective_date).toLocaleDateString()}
              </Badge>
            )}
          </div>
        </Card.Body>
      </Card>

      <div className={styles.section}>
        <Text fontWeight="semibold">Large frameworks</Text>
        {renderLargeFrameworks(octopusData.large_frameworks, {
          expandedNodes,
          toggleExpandNode,
          onNodeClick,
          styles,
        })}
      </div>
    </div>
  );
};

function renderLargeFrameworks(frameworks, helpers) {
  const { expandedNodes, toggleExpandNode, onNodeClick, styles } = helpers;

  if (!frameworks || Object.keys(frameworks).length === 0) {
    return (
      <MessageBar intent="info">
        <MessageBarBody>No large frameworks defined.</MessageBarBody>
      </MessageBar>
    );
  }

  return Object.entries(frameworks).map(([largeId, largeData]) => {
    const isExpanded = expandedNodes[largeId];
    return (
      <div key={largeId} className={styles.collapsible}>
        <div
          className={styles.collapsibleHeader}
          onClick={() => toggleExpandNode(largeId)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              toggleExpandNode(largeId);
            }
          }}
          role="button"
          tabIndex={0}
        >
          <div>
            <Text fontWeight="semibold">{largeData.framework.label}</Text>
            <Text fontSize="sm" color="muted">
              {largeData.framework.description}
            </Text>
          </div>
          <Badge appearance="ghost" color="brand">
            {Object.keys(largeData.medium_frameworks || {}).length} medium frameworks
          </Badge>
          {isExpanded ? <ExpandIcon /> : <CollapseIcon />}
        </div>
        {isExpanded && (
          <div className={styles.collapsibleBody}>
            <Button variant="subtle" onClick={() => onNodeClick?.(largeData.framework)}>
              View framework details
            </Button>
            {renderMediumFrameworks(largeData.medium_frameworks, helpers)}
          </div>
        )}
      </div>
    );
  });
}

function renderMediumFrameworks(frameworks, helpers) {
  const { expandedNodes, toggleExpandNode, onNodeClick, styles } = helpers;

  if (!frameworks || Object.keys(frameworks).length === 0) {
    return (
      <MessageBar intent="warning">
        <MessageBarBody>No medium frameworks defined.</MessageBarBody>
      </MessageBar>
    );
  }

  return Object.entries(frameworks).map(([mediumId, mediumData]) => {
    const isExpanded = expandedNodes[mediumId];
    return (
      <div key={mediumId} className={styles.collapsible}>
        <div
          className={styles.collapsibleHeader}
          onClick={() => toggleExpandNode(mediumId)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              toggleExpandNode(mediumId);
            }
          }}
          role="button"
          tabIndex={0}
        >
          <div>
            <Text fontWeight="semibold">{mediumData.framework.label}</Text>
            <Text fontSize="sm" color="muted">
              {mediumData.framework.description}
            </Text>
          </div>
          <Badge appearance="ghost" color="brand">
            {Object.keys(mediumData.small_frameworks || {}).length} small frameworks
          </Badge>
          {isExpanded ? <ExpandIcon /> : <CollapseIcon />}
        </div>
        {isExpanded && (
          <div className={styles.collapsibleBody}>
            {renderSmallFrameworks(mediumData.small_frameworks, helpers)}
          </div>
        )}
      </div>
    );
  });
}

function renderSmallFrameworks(frameworks, helpers) {
  const { expandedNodes, toggleExpandNode, onNodeClick, styles } = helpers;

  if (!frameworks || Object.keys(frameworks).length === 0) {
    return (
      <MessageBar intent="info">
        <MessageBarBody>No small frameworks defined.</MessageBarBody>
      </MessageBar>
    );
  }

  return Object.entries(frameworks).map(([smallId, smallData]) => {
    const isExpanded = expandedNodes[smallId];
    return (
      <div key={smallId} className={styles.collapsible}>
        <div
          className={styles.collapsibleHeader}
          onClick={() => toggleExpandNode(smallId)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              toggleExpandNode(smallId);
            }
          }}
          role="button"
          tabIndex={0}
        >
          <div>
            <Text fontWeight="semibold">{smallData.framework.label}</Text>
            <Text fontSize="sm" color="muted">
              {smallData.framework.description}
            </Text>
          </div>
          <Badge appearance="ghost" color="brand">
            {Object.keys(smallData.granular_requirements || {}).length} requirements
          </Badge>
          {isExpanded ? <ExpandIcon /> : <CollapseIcon />}
        </div>
        {isExpanded && (
          <div className={styles.collapsibleBody}>
            {renderRequirements(smallData.granular_requirements, onNodeClick, styles)}
          </div>
        )}
      </div>
    );
  });
}

function renderRequirements(requirements, onNodeClick, styles) {
  if (!requirements || Object.keys(requirements).length === 0) {
    return (
      <MessageBar intent="info">
        <MessageBarBody>No requirements defined.</MessageBarBody>
      </MessageBar>
    );
  }

  return (
    <div className={styles.requirementList}>
      {Object.entries(requirements).map(([reqId, reqData]) => (
        <Card
          key={reqId}
          appearance="subtle"
          className={mergeClasses(styles.requirementCard)}
          onClick={() => onNodeClick?.(reqData.requirement)}
        >
          <Card.Body>
            <Text fontWeight="semibold">{reqData.requirement.label}</Text>
            <Text fontSize="sm" color="muted">
              {reqData.requirement.description}
            </Text>
            {reqData.requirement.criticality && (
              <Badge
                appearance="tint"
                color={criticalityColorMap[reqData.requirement.criticality] || 'brand'}
              >
                {reqData.requirement.criticality}
              </Badge>
            )}
          </Card.Body>
        </Card>
      ))}
    </div>
  );
}

export default RegulatoryOctopus;
