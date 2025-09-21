import React, { useEffect, useMemo, useState } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import { Card, Button, Text } from '../components/ui';
import dynamic from 'next/dynamic';
import {
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  MenuPopover,
  MenuTrigger,
  Spinner,
  makeStyles,
  mergeClasses,
  shorthands,
} from '@fluentui/react-components';
import {
  bundleIcon,
  AppsList24Filled,
  AppsList24Regular,
  Building24Filled,
  Building24Regular,
  HexagonThree24Filled,
  HexagonThree24Regular,
  Branch24Filled,
  Branch24Regular,
  Circle24Filled,
  Circle24Regular,
  PersonSupport24Filled,
  PersonSupport24Regular,
  ShieldGlobe24Filled,
  ShieldGlobe24Regular,
  ShieldCheckmark24Filled,
  ShieldCheckmark24Regular,
  Beaker24Filled,
  Beaker24Regular,
  BookOpen24Filled,
  BookOpen24Regular,
  Layer24Filled,
  Layer24Regular,
  Location24Filled,
  Location24Regular,
  Clock24Filled,
  Clock24Regular,
  ZoomIn24Filled,
  ZoomIn24Regular,
  ZoomOut24Filled,
  ZoomOut24Regular,
  ArrowCounterclockwise24Filled,
  ArrowCounterclockwise24Regular,
  MoreHorizontal20Filled,
  MoreHorizontal20Regular,
} from '@fluentui/react-icons';

const useStyles = makeStyles({
  page: {
    display: 'flex',
    flexDirection: 'column',
    gap: '28px',
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
  layout: {
    display: 'grid',
    gap: '24px',
    gridTemplateColumns: '1fr',
    '@media (min-width: 1200px)': {
      gridTemplateColumns: '320px 1fr',
    },
  },
  axisPanel: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  axisList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  axisButton: {
    justifyContent: 'flex-start',
    width: '100%',
  },
  axisButtonActive: {
    boxShadow: '0 12px 30px rgba(28, 90, 163, 0.25)',
  },
  mainPanel: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  toolbar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: '12px',
  },
  graphContainer: {
    position: 'relative',
    minHeight: '520px',
  },
  nodePanel: {
    position: 'absolute',
    top: '24px',
    right: '24px',
    width: '320px',
    maxWidth: 'calc(100% - 48px)',
    zIndex: 10,
  },
  emptyState: {
    minHeight: '420px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
    textAlign: 'center',
    color: 'var(--colorNeutralForeground3)',
  },
});

const HoneycombGraph = dynamic(() => import('../components/ui/HoneycombGraph'), {
  ssr: false,
  loading: () => (
    <div style={{ minHeight: 480, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Spinner appearance="primary" size="large" />
    </div>
  ),
});

const axisIcons = {
  pillar: bundleIcon(AppsList24Filled, AppsList24Regular),
  sector: bundleIcon(Building24Filled, Building24Regular),
  honeycomb: bundleIcon(HexagonThree24Filled, HexagonThree24Regular),
  branch: bundleIcon(Branch24Filled, Branch24Regular),
  node: bundleIcon(Circle24Filled, Circle24Regular),
  expert: bundleIcon(PersonSupport24Filled, PersonSupport24Regular),
  regulatory: bundleIcon(ShieldGlobe24Filled, ShieldGlobe24Regular),
  compliance: bundleIcon(ShieldCheckmark24Filled, ShieldCheckmark24Regular),
  method: bundleIcon(Beaker24Filled, Beaker24Regular),
  topic: bundleIcon(BookOpen24Filled, BookOpen24Regular),
  context: bundleIcon(Layer24Filled, Layer24Regular),
  location: bundleIcon(Location24Filled, Location24Regular),
  time: bundleIcon(Clock24Filled, Clock24Regular),
};

const ZoomInIcon = bundleIcon(ZoomIn24Filled, ZoomIn24Regular);
const ZoomOutIcon = bundleIcon(ZoomOut24Filled, ZoomOut24Regular);
const ResetIcon = bundleIcon(ArrowCounterclockwise24Filled, ArrowCounterclockwise24Regular);
const MenuIcon = bundleIcon(MoreHorizontal20Filled, MoreHorizontal20Regular);

const axes = [
  { id: 'pillar', name: 'Pillar Levels (Axis 1)' },
  { id: 'sector', name: 'Sectors of Industry (Axis 2)' },
  { id: 'honeycomb', name: 'Honeycomb (Axis 3)' },
  { id: 'branch', name: 'Branch (Axis 4)' },
  { id: 'node', name: 'Node (Axis 5)' },
  { id: 'expert', name: 'Expert Role (Axis 6)' },
  { id: 'regulatory', name: 'Regulatory (Axis 7)' },
  { id: 'compliance', name: 'Compliance (Axis 8)' },
  { id: 'method', name: 'Method (Axis 9)' },
  { id: 'topic', name: 'Topic (Axis 10)' },
  { id: 'context', name: 'Context (Axis 11)' },
  { id: 'location', name: 'Location (Axis 12)' },
  { id: 'time', name: 'Time (Axis 13)' },
];

export default function KnowledgeGraphExplorer() {
  const styles = useStyles();
  const [activeAxis, setActiveAxis] = useState('pillar');
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);

  useEffect(() => {
    const fetchGraphData = async () => {
      setLoading(true);
      try {
        const response = await fetch(`/api/graph_data?axis=${activeAxis}`);
        if (response.ok) {
          const data = await response.json();
          setGraphData(data);
        } else {
          setGraphData(generateMockGraph());
        }
      } catch (error) {
        setGraphData(generateMockGraph());
      } finally {
        setLoading(false);
        setSelectedNode(null);
      }
    };

    fetchGraphData();
  }, [activeAxis]);

  const axisTitle = useMemo(() => axes.find((axis) => axis.id === activeAxis)?.name, [activeAxis]);
  const AxisIcon = axisIcons[activeAxis] || axisIcons.pillar;

  return (
    <Layout>
      <Head>
        <title>Knowledge Graph Explorer - UKG</title>
      </Head>

      <div className={styles.page}>
        <header className={styles.header}>
          <span className={styles.badge}>Universal Knowledge Graph</span>
          <Text as="h1" fontSize="3xl" fontWeight="semibold">
            Context-rich knowledge navigation
          </Text>
          <Text color="muted">
            Traverse the 13-axis Microsoft-aligned knowledge fabric, surface connected insights, and pivot
            across compliance, operational telemetry, and subject matter expertise.
          </Text>
        </header>

        <section className={styles.layout}>
          <Card className={styles.axisPanel} appearance="subtle">
            <Card.Header
              header={<Text fontWeight="semibold">Axis selector</Text>}
              description="Choose an axis to focus the graph visualisation and contextual analytics."
            />
            <div className={styles.axisList}>
              {axes.map((axis) => {
                const Icon = axisIcons[axis.id] || axisIcons.pillar;
                const isActive = activeAxis === axis.id;
                return (
                  <Button
                    key={axis.id}
                    variant={isActive ? 'primary' : 'subtle'}
                    icon={<Icon />}
                    className={mergeClasses(styles.axisButton, isActive && styles.axisButtonActive)}
                    onClick={() => setActiveAxis(axis.id)}
                  >
                    {axis.name}
                  </Button>
                );
              })}
            </div>
          </Card>

          <div className={styles.mainPanel}>
            <Card appearance="subtle">
              <Card.Header
                header={
                  <div className={styles.toolbar}>
                    <div>
                      <Text fontWeight="semibold">{axisTitle}</Text>
                      <Text fontSize="sm" color="muted">
                        Interactive graph visualisation with contextual analytics and export actions.
                      </Text>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <Button variant="subtle" icon={<ZoomInIcon />} disabled={loading}>
                        Zoom in
                      </Button>
                      <Button variant="subtle" icon={<ZoomOutIcon />} disabled={loading}>
                        Zoom out
                      </Button>
                      <Button variant="subtle" icon={<ResetIcon />} disabled={loading}>
                        Reset view
                      </Button>
                      <Menu positioning="below-end">
                        <MenuTrigger>
                          <MenuButton appearance="transparent" icon={<MenuIcon />} disabled={loading}>
                            Actions
                          </MenuButton>
                        </MenuTrigger>
                        <MenuPopover>
                          <MenuList>
                            <MenuItem disabled={loading}>Export to Power BI</MenuItem>
                            <MenuItem disabled={loading}>Sync with Microsoft Purview</MenuItem>
                            <MenuItem disabled={loading}>Open crosswalk matrix</MenuItem>
                          </MenuList>
                        </MenuPopover>
                      </Menu>
                    </div>
                  </div>
                }
                action={<AxisIcon />}
              />

              <div className={styles.graphContainer}>
                {loading ? (
                  <div className={styles.emptyState}>
                    <Spinner appearance="primary" size="large" />
                    <Text color="muted">Building contextual layout for {axisTitle}</Text>
                  </div>
                ) : (
                  <HoneycombGraph
                    graphData={graphData}
                    width="100%"
                    height={520}
                    emptyMessage="No graph data available for this axis."
                    onNodeClick={(node) => setSelectedNode(node)}
                  />
                )}

                {selectedNode && (
                  <Card className={styles.nodePanel} appearance="subtle">
                    <Card.Header
                      header={<Text fontWeight="semibold">{selectedNode.name || selectedNode.id}</Text>}
                      description={<Text fontSize="sm">ID: {selectedNode.id}</Text>}
                      action={
                        <Button
                          variant="transparent"
                          icon={<ResetIcon />}
                          onClick={() => setSelectedNode(null)}
                        >
                          Close
                        </Button>
                      }
                    />
                    <Card.Body>
                      <Text fontSize="sm" color="muted">
                        Group: {selectedNode.group ?? 'N/A'}
                      </Text>
                      <Text fontSize="sm" color="muted">
                        Value: {selectedNode.value ? selectedNode.value.toFixed(2) : 'N/A'}
                      </Text>
                      <Button variant="primary" style={{ marginTop: '12px' }}>
                        Launch detailed analysis
                      </Button>
                    </Card.Body>
                  </Card>
                )}
              </div>
            </Card>
          </div>
        </section>
      </div>
    </Layout>
  );
}

function generateMockGraph() {
  const nodes = Array.from({ length: 28 }, (_, i) => ({
    id: `node-${i}`,
    name: `Node ${i}`,
    group: Math.floor(i / 4) + 1,
    axis: (i % 5) + 1,
    value: 10 + Math.random() * 15,
  }));
  const links = Array.from({ length: 38 }, () => ({
    source: `node-${Math.floor(Math.random() * nodes.length)}`,
    target: `node-${Math.floor(Math.random() * nodes.length)}`,
    value: 1 + Math.random() * 4,
  }));
  return { nodes, links };
}
