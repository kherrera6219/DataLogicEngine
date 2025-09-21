import React, { useState, useEffect } from 'react';
import { makeStyles, shorthands, Spinner } from '@fluentui/react-components';
import Card from './Card';
import Button from './Button';
import Text from './Text';
import Input from './Input';

const useStyles = makeStyles({
  layout: {
    display: 'grid',
    gap: '24px',
  },
  twoColumn: {
    display: 'grid',
    gap: '24px',
    gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
  },
  statusList: {
    margin: 0,
    paddingLeft: '18px',
    lineHeight: 1.6,
  },
  formGrid: {
    display: 'grid',
    gap: '16px',
  },
  coordinateGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(90px, 1fr))',
    gap: '12px',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    backgroundColor: 'var(--colorNeutralBackground2)',
    borderRadius: '16px',
    overflow: 'hidden',
  },
  th: {
    padding: '14px 16px',
    backgroundColor: 'rgba(117,172,242,0.12)',
    textAlign: 'left',
    borderBottom: '1px solid rgba(255,255,255,0.08)',
  },
  td: {
    padding: '12px 16px',
    borderBottom: '1px solid rgba(255,255,255,0.06)',
  },
  badge: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    ...shorthands.padding('4px', '10px'),
    borderRadius: '999px',
    backgroundColor: 'rgba(98,179,113,0.2)',
    color: '#9fe2b0',
    fontSize: '0.8rem',
    fontWeight: 600,
  },
});

const UnifiedMapping = () => {
  const styles = useStyles();
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchType, setSearchType] = useState('nuremberg');
  const [searchValue, setSearchValue] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [coordinates, setCoordinates] = useState(Array(13).fill(0));
  const [distanceThreshold, setDistanceThreshold] = useState(0.2);

  useEffect(() => {
    fetchSystemStatus();
  }, []);

  const fetchSystemStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/unified/status');
      const data = await response.json();
      setSystemStatus(data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch system status');
    } finally {
      setLoading(false);
    }
  };

  const handleCoordinateChange = (index, value) => {
    const next = [...coordinates];
    next[index] = parseFloat(value) || 0;
    setCoordinates(next);
  };

  const handleSearch = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (searchType === 'coordinates') {
        const response = await fetch('/api/unified/coordinates', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ coordinates, distance_threshold: distanceThreshold }),
        });
        const data = await response.json();
        if (data.status === 'success') {
          setSearchResults(data.nearby_nodes || []);
        } else {
          setError(data.message || 'Search failed');
        }
      } else {
        const path = searchType === 'nuremberg' ? 'nuremberg' : 'samgov';
        const response = await fetch(`/api/unified/${path}/${searchValue}`);
        const data = await response.json();
        if (data.status === 'success') {
          setSearchResults(data.nodes || []);
        } else {
          setError(data.message || 'Search failed');
        }
      }
    } catch (err) {
      setError('Search failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.layout}>
      <div>
        <Text fontSize="3xl" fontWeight="bold">
          Unified mapping system
        </Text>
        <Text color="muted">
          Map the 13-axis Universal Knowledge Graph coordinates alongside Nuremberg and SAM.gov identifiers.
        </Text>
      </div>

      {error && <Text color="danger">{error}</Text>}

      <div className={styles.twoColumn}>
        <Card>
          <Card.Body>
            <Text fontWeight="semibold">System status</Text>
            {loading && !systemStatus ? (
              <Spinner size="medium" label="Checking status" />
            ) : systemStatus ? (
              <div className={styles.formGrid}>
                <div>
                  <Text fontSize="sm" color="muted">
                    Status
                  </Text>
                  <span className={styles.badge}>{systemStatus.system_status}</span>
                </div>
                {systemStatus.node_stats && (
                  <div>
                    <Text fontWeight="semibold">Node statistics</Text>
                    <ul className={styles.statusList}>
                      <li>Total nodes: {systemStatus.node_stats.total_nodes}</li>
                      <li>Nuremberg mapped: {systemStatus.node_stats.nuremberg_mapped_nodes}</li>
                      <li>SAM.gov mapped: {systemStatus.node_stats.samgov_mapped_nodes}</li>
                      <li>Coordinate mapped: {systemStatus.node_stats.coordinates_mapped_nodes}</li>
                    </ul>
                  </div>
                )}
                <Text fontSize="sm" color="muted">
                  Last updated {systemStatus.timestamp && new Date(systemStatus.timestamp).toLocaleString()}
                </Text>
              </div>
            ) : (
              <Text color="muted">System status unavailable.</Text>
            )}
          </Card.Body>
        </Card>

        <Card>
          <Card.Body>
            <form className={styles.formGrid} onSubmit={handleSearch}>
              <div>
                <Text fontWeight="semibold">Search type</Text>
                <select
                  value={searchType}
                  onChange={(event) => setSearchType(event.target.value)}
                  style={{
                    marginTop: '8px',
                    padding: '10px 14px',
                    borderRadius: '12px',
                    border: '1px solid rgba(255,255,255,0.12)',
                    backgroundColor: 'var(--colorNeutralBackground3)',
                    color: 'var(--colorNeutralForeground1)',
                  }}
                >
                  <option value="nuremberg">Nuremberg code</option>
                  <option value="samgov">SAM.gov name</option>
                  <option value="coordinates">13-axis coordinates</option>
                </select>
              </div>

              {searchType === 'coordinates' ? (
                <div>
                  <Text fontWeight="semibold">Coordinate vector</Text>
                  <div className={styles.coordinateGrid}>
                    {coordinates.map((value, index) => (
                      <Input
                        key={index}
                        type="number"
                        step="0.01"
                        value={value}
                        onChange={(event, data) => handleCoordinateChange(index, data.value)}
                        placeholder={`Axis ${index + 1}`}
                      />
                    ))}
                  </div>
                  <div>
                    <Text fontSize="sm" color="muted">Distance threshold</Text>
                    <Input
                      type="number"
                      step="0.05"
                      value={distanceThreshold}
                      onChange={(event, data) => setDistanceThreshold(parseFloat(data.value) || 0)}
                    />
                  </div>
                </div>
              ) : (
                <Input
                  placeholder={searchType === 'nuremberg' ? 'Enter Nuremberg code' : 'Enter SAM.gov name'}
                  value={searchValue}
                  onChange={(event, data) => setSearchValue(data.value)}
                />
              )}

              <Button type="submit" variant="primary" disabled={loading}>
                {loading ? 'Searching…' : 'Run search'}
              </Button>
            </form>
          </Card.Body>
        </Card>
      </div>

      <Card>
        <Card.Body>
          <Text fontWeight="semibold">Search results</Text>
          <div style={{ overflowX: 'auto', marginTop: '16px' }}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th className={styles.th}>Node</th>
                  <th className={styles.th}>Type</th>
                  <th className={styles.th}>Coordinates</th>
                  <th className={styles.th}>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {searchResults.map((node, index) => (
                  <tr key={index}>
                    <td className={styles.td}>{node.label || node.name || '—'}</td>
                    <td className={styles.td}>{node.type || '—'}</td>
                    <td className={styles.td}>{Array.isArray(node.coordinates) ? node.coordinates.join(', ') : '—'}</td>
                    <td className={styles.td}>{node.distance ? `${(1 - node.distance).toFixed(2)}` : '—'}</td>
                  </tr>
                ))}
                {searchResults.length === 0 && (
                  <tr>
                    <td className={styles.td} colSpan={4}>
                      <Text color="muted">Run a search to view mapped nodes.</Text>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card.Body>
      </Card>
    </div>
  );
};

export default UnifiedMapping;
