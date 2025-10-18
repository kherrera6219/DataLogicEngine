import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Card, Button, Text, Dropdown, Textarea, Badge } from './';
import {
  MessageBar,
  MessageBarBody,
  MessageBarTitle,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  MenuPopover,
  MenuTrigger,
  Spinner,
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
  makeStyles,
  shorthands,
} from '@fluentui/react-components';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  controls: {
    display: 'grid',
    gap: '16px',
    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
  },
  notification: {
    marginTop: '4px',
  },
  sublevelList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    marginTop: '12px',
  },
  sublevelCard: {
    borderRadius: '16px',
    backgroundColor: 'var(--colorNeutralBackground3)',
    border: '1px solid rgba(255,255,255,0.04)',
    ...shorthands.padding('12px', '16px'),
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  sublevelHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '12px',
  },
  sublevelMeta: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  relatedGrid: {
    display: 'grid',
    gap: '16px',
    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
  },
  loadingPanel: {
    minHeight: '200px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
    flexDirection: 'column',
  },
});

export default function PillarMapping({ initialPillarId }) {
  const styles = useStyles();
  const [pillars, setPillars] = useState([]);
  const [selectedPillar, setSelectedPillar] = useState(initialPillarId || '');
  const [expansion, setExpansion] = useState(null);
  const [contextText, setContextText] = useState('');
  const [loading, setLoading] = useState(false);
  const [mappings, setMappings] = useState([]);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    const fetchPillars = async () => {
      try {
        const response = await fetch('/api/pillars/');
        if (response.ok) {
          const data = await response.json();
          setPillars(data);
        } else {
          setNotification({ intent: 'error', title: 'Unable to load pillars', description: 'Failed to fetch pillars.' });
        }
      } catch (error) {
        setNotification({ intent: 'error', title: 'Unable to load pillars', description: error.message });
      }
    };

    fetchPillars();
  }, []);

  useEffect(() => {
    if (!initialPillarId) return;
    setSelectedPillar(initialPillarId);
    fetchPillarExpansion(initialPillarId);
  }, [initialPillarId, fetchPillarExpansion]);

  useEffect(() => {
    if (!notification) return;
    const timer = setTimeout(() => setNotification(null), 5000);
    return () => clearTimeout(timer);
  }, [notification]);

  const showNotification = useCallback((intent, title, description) => {
    setNotification({ intent, title, description });
  }, []);

  const fetchMappings = useCallback(async (pillarId) => {
    try {
      const response = await fetch(`/api/pillars/mappings?pillar_id=${pillarId}`);
      if (response.ok) {
        const data = await response.json();
        setMappings(data);
      }
    } catch (error) {
      showNotification('error', 'Mapping retrieval failed', error.message);
    }
  }, [showNotification]);

  const fetchPillarExpansion = useCallback(async (pillarId, text = null) => {
    if (!pillarId) return;
    setLoading(true);
    try {
      const response = await fetch(`/api/pillars/${pillarId}/expand`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ context_text: text }),
      });
      if (response.ok) {
        const data = await response.json();
        setExpansion(data);
        fetchMappings(pillarId);
      } else {
        const errorData = await response.json();
        showNotification('error', 'Expansion failed', errorData.error || 'Unable to expand pillar');
      }
    } catch (error) {
      showNotification('error', 'Expansion failed', error.message);
    } finally {
      setLoading(false);
    }
  }, [fetchMappings, showNotification]);

  const handlePillarSelect = (pillarId) => {
    setSelectedPillar(pillarId);
    setContextText('');
    setExpansion(null);
    setMappings([]);
    if (pillarId) {
      fetchPillarExpansion(pillarId);
    }
  };

  const handleExpandWithContext = () => {
    if (!selectedPillar) {
      showNotification('warning', 'Select a pillar', 'Choose a pillar before running a contextual expansion.');
      return;
    }
    fetchPillarExpansion(selectedPillar, contextText);
  };

  const createMapping = async (sourceSublevelId, targetPillarId, targetSublevelId) => {
    try {
      const response = await fetch('/api/pillars/mappings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_pillar_id: selectedPillar,
          source_sublevel_id: sourceSublevelId,
          target_pillar_id: targetPillarId,
          target_sublevel_id: targetSublevelId,
          mapping_type: 'related_to',
          strength: 0.7,
          bidirectional: true,
        }),
      });
      if (response.ok) {
        showNotification('success', 'Mapping created', 'The dynamic mapping was created successfully.');
        fetchMappings(selectedPillar);
      } else {
        const errorData = await response.json();
        showNotification('error', 'Mapping failed', errorData.error || 'Unable to create mapping');
      }
    } catch (error) {
      showNotification('error', 'Mapping failed', error.message);
    }
  };

  const pillarOptions = useMemo(
    () =>
      pillars.map((pillar) => ({
        value: pillar.id,
        label: `${pillar.id} — ${pillar.label || pillar.name}`,
      })),
    [pillars]
  );

  return (
    <div className={styles.container}>
      {notification && (
        <MessageBar intent={notification.intent} className={styles.notification}>
          <MessageBarBody>
            {notification.title && <MessageBarTitle>{notification.title}</MessageBarTitle>}
            {notification.description}
          </MessageBarBody>
        </MessageBar>
      )}

      <div className={styles.controls}>
        <div>
          <Text fontWeight="semibold">Select pillar level</Text>
          <Dropdown
            placeholder="Choose a pillar"
            options={pillarOptions}
            value={selectedPillar}
            onChange={(value) => handlePillarSelect(value)}
          />
        </div>
        <div>
          <Text fontWeight="semibold">Context for expansion</Text>
          <Textarea
            value={contextText}
            onChange={(_, data) => setContextText(data.value)}
            placeholder="Provide contextual details to refine the expansion"
            rows={4}
          />
          <Button
            style={{ marginTop: '8px' }}
            variant="primary"
            onClick={handleExpandWithContext}
            disabled={!selectedPillar || loading}
          >
            {expansion ? 'Re-expand with context' : 'Expand with context'}
          </Button>
        </div>
      </div>

      {loading ? (
        <Card appearance="subtle">
          <div className={styles.loadingPanel}>
            <Spinner appearance="primary" size="large" />
            <Text color="muted">Generating dynamic mapping suggestions…</Text>
          </div>
        </Card>
      ) : (
        expansion && (
          <>
            <Card appearance="subtle">
              <Card.Header
                header={<Text fontWeight="semibold">Pillar structure: {expansion.pillar_name} ({expansion.pillar_id})</Text>}
                description={<Text fontSize="sm">Explore the base and expanded sublevels for this pillar.</Text>}
              />
              <Card.Body>
                <Text fontWeight="semibold">Base sublevels</Text>
                {renderSublevels(expansion.base_sublevels, 0, expansion, createMapping, styles)}

                {expansion.expanded_sublevels && expansion.expanded_sublevels.length > 0 && (
                  <>
                    <Text fontWeight="semibold" style={{ marginTop: '16px' }}>
                      Expanded sublevels
                    </Text>
                    {renderSublevels(expansion.expanded_sublevels, 0, expansion, createMapping, styles)}
                  </>
                )}
              </Card.Body>
            </Card>

            {expansion.related_pillars && expansion.related_pillars.length > 0 && (
              <Card appearance="subtle">
                <Card.Header
                  header={<Text fontWeight="semibold">Related pillars</Text>}
                  description={<Text fontSize="sm">Suggested crosswalk opportunities based on semantic similarity.</Text>}
                />
                <Card.Body>
                  <div className={styles.relatedGrid}>
                    {expansion.related_pillars.map((related) => (
                      <Card key={related.pillar_id} appearance="subtle">
                        <Card.Body>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'space-between' }}>
                            <Text fontWeight="semibold">{related.pillar_id}</Text>
                            <Badge appearance="tint" color={related.suggested ? 'warning' : 'brand'}>
                              {related.suggested ? 'Suggested' : 'Mapped'}
                            </Badge>
                          </div>
                          <Text fontSize="sm" color="muted">
                            Strength: {related.strength?.toFixed(2) || 'N/A'}
                          </Text>
                          {related.reason && (
                            <Text fontSize="sm" color="muted" style={{ marginTop: '8px' }}>
                              {related.reason}
                            </Text>
                          )}
                        </Card.Body>
                      </Card>
                    ))}
                  </div>
                </Card.Body>
              </Card>
            )}

            {mappings && mappings.length > 0 && (
              <Card appearance="subtle">
                <Card.Header
                  header={<Text fontWeight="semibold">Dynamic mappings</Text>}
                  description={<Text fontSize="sm">Existing relationships generated from prior expansions.</Text>}
                />
                <Card.Body>
                  <Table aria-label="Pillar mappings">
                    <TableHeader>
                      <TableRow>
                        <TableHeaderCell>Source</TableHeaderCell>
                        <TableHeaderCell>Target</TableHeaderCell>
                        <TableHeaderCell>Type</TableHeaderCell>
                        <TableHeaderCell>Strength</TableHeaderCell>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {mappings.map((mapping, index) => (
                        <TableRow key={`${mapping.source?.pillar_id}-${mapping.target?.pillar_id}-${index}`}>
                          <TableCell>
                            {mapping.source?.pillar_id}.{mapping.source?.sublevel_id}
                          </TableCell>
                          <TableCell>
                            {mapping.target?.pillar_id}.{mapping.target?.sublevel_id}
                          </TableCell>
                          <TableCell>{mapping.mapping_type}</TableCell>
                          <TableCell>{mapping.strength?.toFixed(2)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Card.Body>
              </Card>
            )}
          </>
        )
      )}
    </div>
  );
}

function renderSublevels(sublevels, depth, expansion, createMapping, styles) {
  if (!sublevels || !Array.isArray(sublevels) || sublevels.length === 0) {
    return <Text color="muted">No sublevels defined.</Text>;
  }

  return (
    <div className={styles.sublevelList} style={{ marginLeft: depth * 16 }}>
      {sublevels.map((sublevel) => (
        <div key={sublevel.id} className={styles.sublevelCard}>
          <div className={styles.sublevelHeader}>
            <div className={styles.sublevelMeta}>
              <Badge appearance="tint" color={depth === 0 ? 'brand' : 'neutral'}>
                {sublevel.id}
              </Badge>
              <Text fontWeight={depth === 0 ? 'semibold' : 'medium'}>{sublevel.label || sublevel.name}</Text>
            </div>
            {hasMappingOptions(expansion) && (
              <Menu positioning="below-end">
                <MenuTrigger>
                  <MenuButton appearance="transparent" size="small">
                    Map to…
                  </MenuButton>
                </MenuTrigger>
                <MenuPopover>
                  <MenuList>
                    {renderMappingOptions(expansion, sublevel, createMapping)}
                  </MenuList>
                </MenuPopover>
              </Menu>
            )}
          </div>
          {sublevel.description && (
            <Text fontSize="sm" color="muted">
              {sublevel.description}
            </Text>
          )}
          {sublevel.sublevels &&
            sublevel.sublevels.length > 0 &&
            renderSublevels(sublevel.sublevels, depth + 1, expansion, createMapping, styles)}
        </div>
      ))}
    </div>
  );
}

function hasMappingOptions(expansion) {
  return Boolean(
    expansion &&
      expansion.related_pillars &&
      expansion.related_pillars.some((related) => Array.isArray(related.mappings) && related.mappings.length > 0)
  );
}

function renderMappingOptions(expansion, sublevel, createMapping) {
  if (!expansion?.related_pillars) {
    return <MenuItem disabled>No mapping options available</MenuItem>;
  }

  const options = [];
  expansion.related_pillars.forEach((related) => {
    if (Array.isArray(related.mappings) && related.mappings.length > 0) {
      related.mappings.forEach((mapping) => {
        options.push({
          key: `${related.pillar_id}-${mapping.target_sublevel}`,
          label: `${related.pillar_id} → ${mapping.target_sublevel}`,
          action: () => createMapping(sublevel.id, related.pillar_id, mapping.target_sublevel),
        });
      });
    }
  });

  if (options.length === 0) {
    return <MenuItem disabled>No mapping options available</MenuItem>;
  }

  return options.map((option) => (
    <MenuItem key={option.key} onClick={option.action}>
      {option.label}
    </MenuItem>
  ));
}
