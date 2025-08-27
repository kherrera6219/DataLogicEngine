import React, { useState, useEffect, useCallback } from 'react';
import { Card, Button, Textarea, Badge } from './';
import Text from './Text';
import Dropdown from './Dropdown';
import Label from './Label';
import { useToast } from '@chakra-ui/react';

export default function PillarMapping({ initialPillarId }) {
  const [pillars, setPillars] = useState([]);
  const [selectedPillar, setSelectedPillar] = useState(initialPillarId || '');
  const [expansion, setExpansion] = useState(null);
  const [contextText, setContextText] = useState('');
  const [loading, setLoading] = useState(false);
  const [mappings, setMappings] = useState([]);
  const toast = useToast();

  // Load all pillars on component mount
  useEffect(() => {
    const fetchPillars = async () => {
      try {
        const response = await fetch('/api/pillars/');
        if (response.ok) {
          const data = await response.json();
          setPillars(data);
        } else {
          console.error('Failed to fetch pillars');
        }
      } catch (error) {
        console.error('Error fetching pillars:', error);
      }
    };

    fetchPillars();
  }, []);

  const fetchMappings = useCallback(async (pillarId) => {
    try {
      const response = await fetch(`/api/pillars/mappings?pillar_id=${pillarId}`);
      if (response.ok) {
        const data = await response.json();
        setMappings(data);
      }
    } catch (error) {
      console.error('Error fetching mappings:', error);
    }
  }, []);

  const fetchPillarExpansion = useCallback(async (pillarId, text = null) => {
    if (!pillarId) return;

    setLoading(true);
    try {
      const response = await fetch(`/api/pillars/${pillarId}/expand`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ context_text: text }),
      });

      if (response.ok) {
        const data = await response.json();
        setExpansion(data);

        // Also fetch existing mappings
        fetchMappings(pillarId);
      } else {
        const errorData = await response.json();
        showToast({
          title: 'Error',
          description: errorData.error || 'Failed to expand pillar',
          status: 'error',
          duration: 5000,
        });
      }
    } catch (error) {
      console.error('Error expanding pillar:', error);
      showToast({
        title: 'Error',
        description: 'An unexpected error occurred',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  }, [fetchMappings]);

  // Load selected pillar if provided
  useEffect(() => {
    if (initialPillarId) {
      setSelectedPillar(initialPillarId);
      fetchPillarExpansion(initialPillarId);
    }
  }, [initialPillarId, fetchPillarExpansion]);

  const handlePillarSelect = (pillarId) => {
    setSelectedPillar(pillarId);
    setContextText('');
    setExpansion(null);
    if (pillarId) {
      fetchPillarExpansion(pillarId);
    }
  };

  const handleExpandWithContext = () => {
    if (selectedPillar) {
      fetchPillarExpansion(selectedPillar, contextText);
    } else {
      showToast({
        title: 'Warning',
        description: 'Please select a pillar first',
        status: 'warning',
        duration: 3000,
      });
    }
  };

  const createMapping = async (sourceSublevelId, targetPillarId, targetSublevelId) => {
    try {
      const response = await fetch('/api/pillars/mappings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          source_pillar_id: selectedPillar,
          source_sublevel_id: sourceSublevelId,
          target_pillar_id: targetPillarId,
          target_sublevel_id: targetSublevelId,
          mapping_type: 'related_to',
          strength: 0.7,
          bidirectional: true
        }),
      });

      if (response.ok) {
        showToast({
          title: 'Success',
          description: 'Mapping created successfully',
          status: 'success',
          duration: 3000,
        });

        // Refresh mappings
        fetchMappings(selectedPillar);
      } else {
        const errorData = await response.json();
        showToast({
          title: 'Error',
          description: errorData.error || 'Failed to create mapping',
          status: 'error',
          duration: 5000,
        });
      }
    } catch (error) {
      console.error('Error creating mapping:', error);
      showToast({
        title: 'Error',
        description: 'An unexpected error occurred',
        status: 'error',
        duration: 5000,
      });
    }
  };

  // Render sublevel tree with optional nesting
  const renderSublevels = (sublevels, indent = 0) => {
    if (!sublevels || !Array.isArray(sublevels) || sublevels.length === 0) {
      return <Text color="gray.500" ml={indent * 4}>No sublevels defined</Text>;
    }

    return (
      <div>
        {sublevels.map((sublevel) => (
          <div key={sublevel.id} style={{ marginLeft: `${indent * 20}px`, marginBottom: '8px' }}>
            <div className="d-flex align-items-center">
              <Badge color={indent === 0 ? 'primary' : indent === 1 ? 'info' : 'secondary'}>
                {sublevel.id}
              </Badge>
              <Text ml={2} fontWeight={indent === 0 ? 'bold' : 'normal'}>
                {sublevel.label || sublevel.name}
              </Text>

              {/* Add mapping dropdown for each sublevel */}
              {expansion && expansion.related_pillars && expansion.related_pillars.length > 0 && (
                <Dropdown 
                  className="ms-auto" 
                  title="Map to..." 
                  variant="outline-secondary" 
                  size="sm"
                >
                  {expansion.related_pillars.map(relatedPillar => (
                    <div key={relatedPillar.pillar_id} className="dropdown-item">
                      <strong>{relatedPillar.pillar_id}</strong>
                      {relatedPillar.mappings && relatedPillar.mappings.map(mapping => (
                        <Button
                          key={`${mapping.target_sublevel}`}
                          size="sm"
                          variant="link"
                          className="d-block text-start"
                          onClick={() => createMapping(
                            sublevel.id, 
                            relatedPillar.pillar_id, 
                            mapping.target_sublevel
                          )}
                        >
                          Map to {mapping.target_sublevel}
                        </Button>
                      ))}
                    </div>
                  ))}
                </Dropdown>
              )}
            </div>

            {sublevel.description && (
              <Text fontSize="sm" color="gray.600" ml={3}>
                {sublevel.description}
              </Text>
            )}

            {/* Recursively render nested sublevels */}
            {sublevel.sublevels && renderSublevels(sublevel.sublevels, indent + 1)}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div>
      <Card className="mb-4">
        <Card.Header>
          <Card.Title>Knowledge Pillar Dynamic Mapping</Card.Title>
        </Card.Header>
        <Card.Body>
          <div className="mb-4">
            <Label htmlFor="pillarSelect">Select Pillar Level:</Label>
            <Dropdown title={selectedPillar || "Select a Pillar"} id="pillarSelect">
              {pillars.map(pillar => (
                <Dropdown.Item 
                  key={pillar.id} 
                  onClick={() => handlePillarSelect(pillar.id)}
                >
                  {pillar.id}: {pillar.label || pillar.name}
                </Dropdown.Item>
              ))}
            </Dropdown>
          </div>

          <div className="mb-4">
            <Label htmlFor="contextText">Context for Expansion:</Label>
            <Textarea
              id="contextText"
              value={contextText}
              onChange={(e) => setContextText(e.target.value)}
              placeholder="Enter text to provide context for dynamic mapping expansion..."
              rows={4}
            />
            <div className="mt-2">
              <Button 
                onClick={handleExpandWithContext} 
                disabled={!selectedPillar || loading}
                isLoading={loading}
              >
                {expansion ? 'Re-expand with Context' : 'Expand with Context'}
              </Button>
            </div>
          </div>

          {expansion && (
            <>
              <h4 className="mb-3">Pillar Structure: {expansion.pillar_name} ({expansion.pillar_id})</h4>
              <div className="mb-4">
                <h5>Base Sublevels</h5>
                {renderSublevels(expansion.base_sublevels)}
              </div>

              {expansion.expanded_sublevels && expansion.expanded_sublevels.length > 0 && (
                <div className="mb-4">
                  <h5>Expanded Sublevels</h5>
                  {renderSublevels(expansion.expanded_sublevels)}
                </div>
              )}

              {expansion.related_pillars && expansion.related_pillars.length > 0 && (
                <div className="mb-4">
                  <h5>Related Pillars</h5>
                  <div className="row">
                    {expansion.related_pillars.map(relatedPillar => (
                      <div key={relatedPillar.pillar_id} className="col-md-6 mb-3">
                        <Card>
                          <Card.Body>
                            <div className="d-flex align-items-center mb-2">
                              <h6 className="mb-0">{relatedPillar.pillar_id}</h6>
                              <Badge 
                                className="ms-2" 
                                color={relatedPillar.suggested ? 'warning' : 'success'}
                              >
                                {relatedPillar.suggested ? 'Suggested' : 'Mapped'}
                              </Badge>
                              <Text className="ms-auto">
                                Strength: {relatedPillar.strength.toFixed(2)}
                              </Text>
                            </div>

                            {relatedPillar.mappings && relatedPillar.mappings.length > 0 && (
                              <div>
                                <Text fontSize="sm" fontWeight="bold">Existing Mappings:</Text>
                                <ul className="list-unstyled ms-3">
                                  {relatedPillar.mappings.map((mapping, idx) => (
                                    <li key={idx}>
                                      <Text fontSize="sm">
                                        {mapping.source_sublevel || 'source'} → {mapping.target_sublevel || 'target'}
                                        {mapping.mapping_type && ` (${mapping.mapping_type})`}
                                      </Text>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {relatedPillar.reason && (
                              <Text fontSize="sm" fontStyle="italic" color="gray.500" mt={1}>
                                {relatedPillar.reason}
                              </Text>
                            )}
                          </Card.Body>
                        </Card>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {mappings && mappings.length > 0 && (
                <div className="mb-4">
                  <h5>All Dynamic Mappings</h5>
                  <div className="table-responsive">
                    <table className="table table-sm">
                      <thead>
                        <tr>
                          <th>Source</th>
                          <th>Target</th>
                          <th>Type</th>
                          <th>Strength</th>
                        </tr>
                      </thead>
                      <tbody>
                        {mappings.map((mapping, idx) => (
                          <tr key={idx}>
                            <td>
                              {mapping.source.pillar_id}.{mapping.source.sublevel_id}
                            </td>
                            <td>
                              {mapping.target.pillar_id}.{mapping.target.sublevel_id}
                            </td>
                            <td>{mapping.mapping_type}</td>
                            <td>{mapping.strength.toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </Card.Body>
      </Card>
    </div>
  );
}