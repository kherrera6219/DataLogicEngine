import React, { useEffect, useMemo, useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import Layout from '../components/Layout';
import { Card, Button, Input, Text, Badge } from '../components/ui';
import HoneycombGraph from '../components/ui/HoneycombGraph';
import {
  Accordion,
  AccordionHeader,
  AccordionItem,
  AccordionPanel,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  MenuPopover,
  MenuTrigger,
  Spinner,
  Tab,
  TabList,
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
  makeStyles,
  shorthands,
} from '@fluentui/react-components';
import {
  bundleIcon,
  DataTrending24Filled,
  DataTrending24Regular,
  Table24Filled,
  Table24Regular,
  HexagonThree24Filled,
  HexagonThree24Regular,
  MoreHorizontal20Filled,
  MoreHorizontal20Regular,
  ArrowTrendingLines20Regular,
  ArrowTrendingLines20Filled,
  BookTemplate24Regular,
  BookTemplate24Filled,
} from '@fluentui/react-icons';

const useStyles = makeStyles({
  page: {
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
    ...shorthands.padding('32px', '24px', '56px'),
  },
  header: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  badge: {
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(117, 172, 242, 0.16)',
    color: '#9cc2f7',
    fontWeight: 600,
    ...shorthands.padding('4px', '12px'),
    borderRadius: '999px',
    letterSpacing: '0.04em',
  },
  heroActions: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '12px',
    marginTop: '4px',
  },
  layout: {
    display: 'grid',
    gap: '24px',
    gridTemplateColumns: '1fr',
    '@media (min-width: 1100px)': {
      gridTemplateColumns: '360px 1fr',
    },
  },
  listCard: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  listHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '12px',
  },
  searchField: {
    width: '100%',
  },
  honeycombList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    maxHeight: '520px',
    overflowY: 'auto',
    paddingRight: '6px',
  },
  honeycombItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    borderRadius: '16px',
    backgroundColor: 'var(--colorNeutralBackground3)',
    border: '1px solid rgba(255,255,255,0.04)',
    transition: 'border-color 0.2s ease, transform 0.2s ease',
    cursor: 'pointer',
    ...shorthands.padding('12px', '14px'),
  },
  honeycombItemActive: {
    borderColor: 'var(--colorBrandStroke1)',
    transform: 'translateY(-2px)',
    boxShadow: '0 12px 30px rgba(28, 90, 163, 0.25)',
  },
  honeycombHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  honeycombMeta: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '12px',
    color: 'var(--colorNeutralForeground3)',
    fontSize: '13px',
  },
  detailCard: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  detailHeader: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  detailActions: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '12px',
    flexWrap: 'wrap',
  },
  graphPanel: {
    minHeight: '420px',
  },
  emptyState: {
    minHeight: '420px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    textAlign: 'center',
    gap: '12px',
    color: 'var(--colorNeutralForeground3)',
  },
});

const GraphIcon = bundleIcon(DataTrending24Filled, DataTrending24Regular);
const TableIcon = bundleIcon(Table24Filled, Table24Regular);
const HoneycombIcon = bundleIcon(HexagonThree24Filled, HexagonThree24Regular);
const MenuIcon = bundleIcon(MoreHorizontal20Filled, MoreHorizontal20Regular);
const PatternIcon = bundleIcon(BookTemplate24Filled, BookTemplate24Regular);
const GrowthIcon = bundleIcon(ArrowTrendingLines20Filled, ArrowTrendingLines20Regular);

const honeycombPatterns = [
  { id: 'hc1', name: 'Federal Acquisition Regulation', count: 53, updated: '2025-03-01' },
  { id: 'hc2', name: 'Defense Federal Acquisition Regulation', count: 42, updated: '2025-02-12' },
  { id: 'hc3', name: 'Contract Performance', count: 38, updated: '2025-01-22' },
  { id: 'hc4', name: 'Cost Accounting Standards', count: 27, updated: '2025-02-02' },
  { id: 'hc5', name: 'Procurement Integrity', count: 31, updated: '2025-01-28' },
  { id: 'hc6', name: 'Subcontract Alignment', count: 24, updated: '2025-02-24' },
];

export default function HoneycombPage() {
  const styles = useStyles();
  const [activeView, setActiveView] = useState('honeycomb');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedHoneycomb, setSelectedHoneycomb] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!selectedHoneycomb) {
      setGraphData(null);
      return;
    }

    setLoading(true);
    const timeout = setTimeout(() => {
      const nodes = Array.from({ length: 20 }, (_, i) => ({
        id: `node-${i}`,
        name: `${selectedHoneycomb.name} Node ${i + 1}`,
        group: Math.floor(i / 4) + 1,
        axis: (i % 5) + 1,
        value: 6 + Math.random() * 16,
      }));
      const links = Array.from({ length: 30 }, () => ({
        source: `node-${Math.floor(Math.random() * 20)}`,
        target: `node-${Math.floor(Math.random() * 20)}`,
        value: 1 + Math.random() * 3,
      }));

      setGraphData({ nodes, links });
      setLoading(false);
    }, 650);

    return () => clearTimeout(timeout);
  }, [selectedHoneycomb]);

  const filteredHoneycombs = useMemo(() => {
    const query = searchQuery.toLowerCase();
    if (!query) {
      return honeycombPatterns;
    }
    return honeycombPatterns.filter(
      (pattern) =>
        pattern.name.toLowerCase().includes(query) || pattern.id.toLowerCase().includes(query)
    );
  }, [searchQuery]);

  const viewTabs = (
    <TabList
      selectedValue={activeView}
      onTabSelect={(_, data) => setActiveView(data.value)}
      appearance="subtle"
    >
      <Tab value="honeycomb" icon={<GraphIcon />}>Graph view</Tab>
      <Tab value="table" icon={<TableIcon />}>Tabular view</Tab>
    </TabList>
  );

  return (
    <Layout>
      <Head>
        <title>Honeycomb Analysis - UKG</title>
      </Head>

      <div className={styles.page}>
        <header className={styles.header}>
          <span className={styles.badge}>Axis 3 &bull; Honeycomb knowledge patterns</span>
          <Text as="h1" fontSize="3xl" fontWeight="semibold">
            Honeycomb relationship intelligence
          </Text>
          <Text color="muted">
            Investigate cross-domain controls, dependencies, and compliance coverage through the Universal
            Knowledge Graph honeycomb fabric. Compare structures side-by-side and export curated insights
            for enterprise governance.
          </Text>
          <div className={styles.heroActions}>
            <Button as={Link} href="/knowledge-graph" variant="primary" icon={<PatternIcon />}>
              Open knowledge graph explorer
            </Button>
            <Button
              variant="outline"
              icon={<GrowthIcon />}
              onClick={() => selectedHoneycomb && setActiveView('table')}
              disabled={!selectedHoneycomb}
            >
              Review relational metrics
            </Button>
          </div>
        </header>

        <section className={styles.layout}>
          <Card className={styles.listCard} appearance="subtle">
            <Card.Header
              header={
                <div className={styles.listHeader}>
                  <Text fontWeight="semibold">Honeycomb library</Text>
                  <Badge appearance="tint" color="brand">
                    {filteredHoneycombs.length} active
                  </Badge>
                </div>
              }
              description="Select a Microsoft-aligned pattern to load its contextual network."
            />
            <div className={styles.searchField}>
              <Input
                placeholder="Search by pattern, identifier, or focus area"
                value={searchQuery}
                onChange={(_, data) => setSearchQuery(data.value)}
              />
            </div>
            <div className={styles.honeycombList}>
              {filteredHoneycombs.map((pattern) => {
                const isActive = selectedHoneycomb?.id === pattern.id;
                return (
                  <div
                    key={pattern.id}
                    role="button"
                    tabIndex={0}
                    onClick={() => setSelectedHoneycomb(pattern)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        setSelectedHoneycomb(pattern);
                      }
                    }}
                    className={`${styles.honeycombItem} ${isActive ? styles.honeycombItemActive : ''}`}
                  >
                    <div className={styles.honeycombHeader}>
                      <HoneycombIcon />
                      <div>
                        <Text fontWeight="semibold">{pattern.name}</Text>
                        <Text fontSize="sm" color="muted">
                          Identifier: {pattern.id.toUpperCase()}
                        </Text>
                      </div>
                    </div>
                    <div className={styles.honeycombMeta}>
                      <span>{pattern.count} nodes</span>
                      <span>Refreshed {pattern.updated}</span>
                    </div>
                  </div>
                );
              })}

              {filteredHoneycombs.length === 0 && (
                <div className={styles.emptyState}>
                  <Text fontWeight="semibold">No patterns matched your search</Text>
                  <Text color="muted">
                    Adjust your filters or request a new honeycomb synthesis from the orchestration workspace.
                  </Text>
                </div>
              )}
            </div>
          </Card>

          <Card className={styles.detailCard} appearance="subtle">
            <Card.Header
              header={
                <div className={styles.detailHeader}>
                  <div className={styles.detailActions}>
                    <div>
                      <Text fontWeight="semibold" fontSize="lg">
                        {selectedHoneycomb ? selectedHoneycomb.name : 'Select a honeycomb pattern'}
                      </Text>
                      <Text fontSize="sm" color="muted">
                        {selectedHoneycomb
                          ? 'Explore the underlying network, export intelligence, or pivot to alternate visualizations.'
                          : 'Choose a pattern from the library to analyse its relationships and dependencies.'}
                      </Text>
                    </div>
                    <Menu positioning="below-end">
                      <MenuTrigger>
                        <MenuButton
                          appearance="transparent"
                          icon={<MenuIcon />}
                          disabled={!selectedHoneycomb}
                        >
                          Actions
                        </MenuButton>
                      </MenuTrigger>
                      <MenuPopover>
                        <MenuList>
                          <MenuItem disabled={!selectedHoneycomb}>Export as interactive report</MenuItem>
                          <MenuItem disabled={!selectedHoneycomb}>Share with compliance workspace</MenuItem>
                          <MenuItem disabled={!selectedHoneycomb}>Launch cross-pillar mapping</MenuItem>
                        </MenuList>
                      </MenuPopover>
                    </Menu>
                  </div>
                  {viewTabs}
                </div>
              }
            />

            {selectedHoneycomb ? (
              activeView === 'honeycomb' ? (
                <div className={styles.graphPanel}>
                  <HoneycombGraph
                    graphData={graphData}
                    loading={loading}
                    width="100%"
                    height={420}
                    emptyMessage="Select a honeycomb pattern to render its network."
                  />
                </div>
              ) : (
                <HoneycombTable graphData={graphData} loading={loading} />
              )
            ) : (
              <div className={styles.emptyState}>
                <HoneycombIcon />
                <Text fontWeight="semibold">No pattern selected</Text>
                <Text color="muted">
                  Choose a honeycomb pattern to visualise collaborative intelligence, relational overlap, and
                  compliance dependencies across the Universal Knowledge Graph.
                </Text>
              </div>
            )}

            <Accordion collapsible defaultOpenItems={["insights"]}>
              <AccordionItem value="insights">
                <AccordionHeader icon={<GraphIcon />}>Insight highlights</AccordionHeader>
                <AccordionPanel>
                  <Text fontSize="sm" color="muted">
                    Use honeycomb expansions to monitor control saturation, surface orphaned nodes, and align
                    remediation plans with Microsoft cloud governance blueprints.
                  </Text>
                </AccordionPanel>
              </AccordionItem>
            </Accordion>
          </Card>
        </section>
      </div>
    </Layout>
  );
}

function HoneycombTable({ graphData, loading }) {
  if (loading) {
    return (
      <div style={{ minHeight: 360, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Spinner appearance="primary" size="large" />
      </div>
    );
  }

  if (!graphData || !graphData.nodes?.length) {
    return (
      <div style={{ minHeight: 360, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Text color="muted">No relational data available for this honeycomb.</Text>
      </div>
    );
  }

  const nodeConnections = graphData.nodes.map((node) => ({
    id: node.id,
    name: node.name,
    group: node.group,
    connections: graphData.links.filter(
      (link) => link.source === node.id || link.target === node.id
    ).length,
  }));

  return (
    <Table aria-label="Honeycomb node relationships">
      <TableHeader>
        <TableRow>
          <TableHeaderCell>Node</TableHeaderCell>
          <TableHeaderCell>Label</TableHeaderCell>
          <TableHeaderCell>Connections</TableHeaderCell>
          <TableHeaderCell>Group</TableHeaderCell>
        </TableRow>
      </TableHeader>
      <TableBody>
        {nodeConnections.map((node) => (
          <TableRow key={node.id}>
            <TableCell>{node.id}</TableCell>
            <TableCell>{node.name}</TableCell>
            <TableCell>{node.connections}</TableCell>
            <TableCell>{node.group}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
