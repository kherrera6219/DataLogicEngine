import React, { useState, useMemo } from 'react';
import { makeStyles, shorthands } from '@fluentui/react-components';
import Card from './Card';
import Button from './Button';
import Text from './Text';
import Input from './Input';

const useStyles = makeStyles({
  layout: {
    display: 'grid',
    gap: '24px',
  },
  header: {
    display: 'grid',
    gap: '12px',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
  },
  summaryCard: {
    display: 'grid',
    gap: '8px',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    borderRadius: '18px',
    overflow: 'hidden',
    backgroundColor: 'var(--colorNeutralBackground2)',
    boxShadow: '0 18px 45px rgba(9, 17, 32, 0.35)',
  },
  tableHeader: {
    backgroundColor: 'rgba(117,172,242,0.16)',
    textAlign: 'left',
  },
  th: {
    padding: '16px 20px',
    fontSize: '0.85rem',
    fontWeight: 600,
    color: '#dce9ff',
    borderBottom: '1px solid rgba(255,255,255,0.08)',
  },
  td: {
    padding: '14px 20px',
    borderBottom: '1px solid rgba(255,255,255,0.06)',
  },
  filterRow: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '12px',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  searchGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
});

const LocationMap = ({ initialLocations }) => {
  const styles = useStyles();
  const [search, setSearch] = useState('');
  const [selectedType, setSelectedType] = useState('');

  const locations = useMemo(() => initialLocations || [], [initialLocations]);

  const filteredLocations = useMemo(() => {
    return locations.filter((location) => {
      const matchesSearch = search
        ? (location.name || '').toLowerCase().includes(search.toLowerCase()) ||
          (location.region || '').toLowerCase().includes(search.toLowerCase())
        : true;
      const matchesType = selectedType ? location.type === selectedType : true;
      return matchesSearch && matchesType;
    });
  }, [locations, search, selectedType]);

  const uniqueTypes = Array.from(new Set(locations.map((location) => location.type).filter(Boolean)));

  return (
    <div className={styles.layout}>
      <div className={styles.header}>
        <Card>
          <Card.Body className={styles.summaryCard}>
            <Text fontSize="sm" color="muted">
              Total locations
            </Text>
            <Text fontSize="2xl" fontWeight="bold">
              {locations.length}
            </Text>
            <Text fontSize="sm" color="muted">
              Across all operational regions registered in the UKG.
            </Text>
          </Card.Body>
        </Card>

        <Card>
          <Card.Body className={styles.summaryCard}>
            <Text fontSize="sm" color="muted">
              Active types
            </Text>
            <Text fontSize="2xl" fontWeight="bold">
              {uniqueTypes.length}
            </Text>
            <Text fontSize="sm" color="muted">
              Location categories such as campuses, data centres, and field offices.
            </Text>
          </Card.Body>
        </Card>
      </div>

      <Card>
        <Card.Body>
          <div className={styles.filterRow}>
            <div className={styles.searchGroup}>
              <Input
                placeholder="Search by name or region"
                value={search}
                onChange={(event, data) => setSearch(data.value)}
                style={{ minWidth: '260px' }}
              />
              <Button
                variant="secondary"
                onClick={() => {
                  setSearch('');
                  setSelectedType('');
                }}
              >
                Reset
              </Button>
            </div>
            <div>
              <label htmlFor="location-type-filter">
                <Text fontSize="sm" color="muted">
                  Filter by type
                </Text>
              </label>
              <select
                id="location-type-filter"
                value={selectedType}
                onChange={(event) => setSelectedType(event.target.value)}
                style={{
                  marginTop: '6px',
                  padding: '10px 14px',
                  borderRadius: '12px',
                  border: '1px solid rgba(255,255,255,0.12)',
                  backgroundColor: 'var(--colorNeutralBackground3)',
                  color: 'var(--colorNeutralForeground1)',
                }}
              >
                <option value="">All types</option>
                {uniqueTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div style={{ overflowX: 'auto', marginTop: '20px' }}>
            <table className={styles.table}>
              <thead className={styles.tableHeader}>
                <tr>
                  <th className={styles.th}>Name</th>
                  <th className={styles.th}>Region</th>
                  <th className={styles.th}>Type</th>
                  <th className={styles.th}>Latitude</th>
                  <th className={styles.th}>Longitude</th>
                </tr>
              </thead>
              <tbody>
                {filteredLocations.map((location) => (
                  <tr key={location.id}>
                    <td className={styles.td}>{location.name || '—'}</td>
                    <td className={styles.td}>{location.region || '—'}</td>
                    <td className={styles.td}>{location.type || '—'}</td>
                    <td className={styles.td}>{location.latitude || '—'}</td>
                    <td className={styles.td}>{location.longitude || '—'}</td>
                  </tr>
                ))}
                {filteredLocations.length === 0 && (
                  <tr>
                    <td className={styles.td} colSpan={5}>
                      <Text color="muted">No locations match the current filters.</Text>
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

export default LocationMap;
