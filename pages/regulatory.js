import React, { useMemo, useState } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import { Card, Button, Input, Text, Badge, Textarea, Dropdown } from '../components/ui';
import dynamic from 'next/dynamic';
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
  ShieldGlobe24Filled,
  ShieldGlobe24Regular,
  TextBulletListSquare24Filled,
  TextBulletListSquare24Regular,
  Branch24Filled,
  Branch24Regular,
  MoreHorizontal20Filled,
  MoreHorizontal20Regular,
  ArrowTrendingLines20Filled,
  ArrowTrendingLines20Regular,
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
  heroBadge: {
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
  },
  layout: {
    display: 'grid',
    gap: '24px',
    gridTemplateColumns: '1fr',
    '@media (min-width: 1200px)': {
      gridTemplateColumns: '360px 1fr',
    },
  },
  listCard: {
    display: 'flex',
    flexDirection: 'column',
    gap: '18px',
  },
  listHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '12px',
  },
  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    maxHeight: '560px',
    overflowY: 'auto',
    paddingRight: '6px',
  },
  listItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    borderRadius: '16px',
    backgroundColor: 'var(--colorNeutralBackground3)',
    border: '1px solid rgba(255,255,255,0.04)',
    cursor: 'pointer',
    transition: 'border-color 0.2s ease, transform 0.2s ease',
    ...shorthands.padding('12px', '16px'),
  },
  listItemActive: {
    borderColor: 'var(--colorBrandStroke1)',
    transform: 'translateY(-2px)',
    boxShadow: '0 12px 30px rgba(28, 90, 163, 0.25)',
  },
  listItemHeader: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px',
  },
  detailCard: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  detailHeader: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  detailActions: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: '12px',
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
  tabContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
});

const FrameworkIcon = bundleIcon(ShieldGlobe24Filled, ShieldGlobe24Regular);
const OverviewIcon = bundleIcon(TextBulletListSquare24Filled, TextBulletListSquare24Regular);
const VisualizationIcon = bundleIcon(Branch24Filled, Branch24Regular);
const MenuIcon = bundleIcon(MoreHorizontal20Filled, MoreHorizontal20Regular);
const InsightsIcon = bundleIcon(ArrowTrendingLines20Filled, ArrowTrendingLines20Regular);

const RegulatoryOctopus = dynamic(() => import('../components/ui/RegulatoryOctopus'), {
  ssr: false,
  loading: () => (
    <div style={{ minHeight: 320, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Spinner appearance="primary" size="large" />
    </div>
  ),
});

const frameworks = [
  { id: 'far', name: 'Federal Acquisition Regulation (FAR)', category: 'Federal', lastUpdated: '2025-01-15' },
  { id: 'dfars', name: 'Defense Federal Acquisition Regulation Supplement', category: 'Defense', lastUpdated: '2024-11-30' },
  { id: 'cfe', name: 'Code of Federal Ethics', category: 'Ethics', lastUpdated: '2024-09-22' },
  { id: 'itar', name: 'International Traffic in Arms Regulations', category: 'International', lastUpdated: '2024-10-05' },
  { id: 'cmmc', name: 'Cybersecurity Maturity Model Certification', category: 'Security', lastUpdated: '2025-02-20' },
  { id: 'sow', name: 'Statement of Work Guidelines', category: 'Contracts', lastUpdated: '2024-12-10' },
  { id: 'ndaa', name: 'National Defense Authorization Act', category: 'Defense', lastUpdated: '2025-01-02' },
];

const crosswalkOptions = [
  { value: 'pillar', label: 'Pillar (Axis 1)' },
  { value: 'sector', label: 'Sector (Axis 2)' },
  { value: 'honeycomb', label: 'Honeycomb (Axis 3)' },
  { value: 'compliance', label: 'Compliance (Axis 8)' },
  { value: 'method', label: 'Method (Axis 9)' },
];

export default function RegulatoryPage() {
  const styles = useStyles();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFramework, setSelectedFramework] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [crosswalkAxis, setCrosswalkAxis] = useState('pillar');

  const filteredFrameworks = useMemo(() => {
    const query = searchQuery.toLowerCase();
    if (!query) {
      return frameworks;
    }

    return frameworks.filter(
      (framework) =>
        framework.name.toLowerCase().includes(query) || framework.category.toLowerCase().includes(query)
    );
  }, [searchQuery]);

  return (
    <Layout>
      <Head>
        <title>Regulatory Frameworks - UKG</title>
      </Head>

      <div className={styles.page}>
        <header className={styles.header}>
          <span className={styles.heroBadge}>Axis 6 &bull; Regulatory alignment</span>
          <Text as="h1" fontSize="3xl" fontWeight="semibold">
            Microsoft-compliant regulatory orchestration
          </Text>
          <Text color="muted">
            Centralise frameworks, crosswalk controls, and visualise cascading mandates to accelerate audit
            readiness across the Universal Knowledge Graph.
          </Text>
          <div className={styles.heroActions}>
            <Button variant="primary" icon={<OverviewIcon />}>Generate compliance briefing</Button>
            <Button variant="outline" icon={<VisualizationIcon />} disabled={!selectedFramework}>
              Launch octopus visualisation
            </Button>
          </div>
        </header>

        <section className={styles.layout}>
          <Card className={styles.listCard} appearance="subtle">
            <Card.Header
              header={
                <div className={styles.listHeader}>
                  <Text fontWeight="semibold">Framework library</Text>
                  <Badge appearance="tint" color="brand">
                    {filteredFrameworks.length} results
                  </Badge>
                </div>
              }
              description="Filter for jurisdiction, control scope, or enforcement style."
            />
            <Input
              placeholder="Search frameworks or categories"
              value={searchQuery}
              onChange={(_, data) => setSearchQuery(data.value)}
            />
            <div className={styles.list}>
              {filteredFrameworks.map((framework) => {
                const isActive = selectedFramework?.id === framework.id;
                return (
                  <div
                    key={framework.id}
                    role="button"
                    tabIndex={0}
                    className={`${styles.listItem} ${isActive ? styles.listItemActive : ''}`}
                    onClick={() => setSelectedFramework(framework)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        setSelectedFramework(framework);
                      }
                    }}
                  >
                    <div className={styles.listItemHeader}>
                      <FrameworkIcon />
                      <div>
                        <Text fontWeight="semibold">{framework.name}</Text>
                        <Text fontSize="sm" color="muted">
                          {framework.category} &bull; Updated {framework.lastUpdated}
                        </Text>
                      </div>
                    </div>
                  </div>
                );
              })}

              {filteredFrameworks.length === 0 && (
                <div className={styles.emptyState}>
                  <Text fontWeight="semibold">No frameworks match your filters</Text>
                  <Text color="muted">
                    Adjust the search criteria or synchronise additional registries from your Microsoft Purview
                    catalogue.
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
                        {selectedFramework ? selectedFramework.name : 'Select a regulatory framework'}
                      </Text>
                      <Text fontSize="sm" color="muted">
                        {selectedFramework
                          ? 'Review statutory context, explore dynamic node relationships, and orchestrate crosswalk mappings.'
                          : 'Choose a framework from the library to access structured intelligence and analytics.'}
                      </Text>
                    </div>
                    <Menu positioning="below-end">
                      <MenuTrigger>
                        <MenuButton appearance="transparent" icon={<MenuIcon />} disabled={!selectedFramework}>
                          Actions
                        </MenuButton>
                      </MenuTrigger>
                      <MenuPopover>
                        <MenuList>
                          <MenuItem disabled={!selectedFramework}>Export attestation brief</MenuItem>
                          <MenuItem disabled={!selectedFramework}>Share to Teams workspace</MenuItem>
                          <MenuItem disabled={!selectedFramework}>Schedule control refresh</MenuItem>
                        </MenuList>
                      </MenuPopover>
                    </Menu>
                  </div>

                  <TabList selectedValue={activeTab} onTabSelect={(_, data) => setActiveTab(data.value)} appearance="subtle">
                    <Tab value="overview" icon={<OverviewIcon />}>Overview</Tab>
                    <Tab value="sections" icon={<InsightsIcon />}>Sections</Tab>
                    <Tab value="visualization" icon={<VisualizationIcon />}>Visualisation</Tab>
                    <Tab value="crosswalk" icon={<FrameworkIcon />}>Crosswalk</Tab>
                  </TabList>
                </div>
              }
            />

            {selectedFramework ? (
              <div className={styles.tabContent}>
                {activeTab === 'overview' && <OverviewSection framework={selectedFramework} />}
                {activeTab === 'sections' && <SectionsSection />}
                {activeTab === 'visualization' && (
                  <div style={{ minHeight: 420 }}>
                    <RegulatoryOctopus frameworkUid={selectedFramework.id} />
                  </div>
                )}
                {activeTab === 'crosswalk' && (
                  <CrosswalkSection
                    crosswalkAxis={crosswalkAxis}
                    onAxisChange={setCrosswalkAxis}
                    framework={selectedFramework}
                  />
                )}
              </div>
            ) : (
              <div className={styles.emptyState}>
                <FrameworkIcon />
                <Text fontWeight="semibold">Select a regulatory framework</Text>
                <Text color="muted">
                  Visualise cascading requirements, compare frameworks, and map obligations across Microsoft
                  enterprise workloads.
                </Text>
              </div>
            )}
          </Card>
        </section>
      </div>
    </Layout>
  );
}

function OverviewSection({ framework }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <Card appearance="subtle">
        <Card.Body>
          <Text fontWeight="semibold">Description</Text>
          <Text color="muted" fontSize="sm">
            {framework.id === 'far'
              ? 'The Federal Acquisition Regulation (FAR) governs acquisition across all executive agencies, setting the baseline for compliant procurement.'
              : 'This regulatory framework codifies mandatory practices, oversight requirements, and reporting obligations for enterprise operations.'}
          </Text>
        </Card.Body>
      </Card>

      <Card appearance="subtle">
        <Card.Body>
          <Text fontWeight="semibold">Key information</Text>
          <Table aria-label="Framework details">
            <TableBody>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>{framework.id.toUpperCase()}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Category</TableCell>
                <TableCell>{framework.category}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Last updated</TableCell>
                <TableCell>{framework.lastUpdated}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Authority</TableCell>
                <TableCell>Federal Government</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Enforcement</TableCell>
                <TableCell>Mandatory</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </Card.Body>
      </Card>

      <Card appearance="subtle">
        <Card.Body>
          <Text fontWeight="semibold">Related frameworks</Text>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {frameworks
              .filter((item) => item.id !== framework.id)
              .slice(0, 3)
              .map((item) => (
                <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <Text fontWeight="semibold">{item.name}</Text>
                    <Text fontSize="sm" color="muted">
                      {item.category}
                    </Text>
                  </div>
                  <Badge appearance="ghost" color="brand">
                    {item.lastUpdated}
                  </Badge>
                </div>
              ))}
          </div>
        </Card.Body>
      </Card>
    </div>
  );
}

function SectionsSection() {
  return (
    <Accordion collapsible defaultOpenItems={["part1"]}>
      <AccordionItem value="part1">
        <AccordionHeader>Part 1: General information</AccordionHeader>
        <AccordionPanel>
          <Text color="muted" fontSize="sm">
            High-level context, definitions, applicability, and governance responsibilities for the framework.
          </Text>
          <ul style={{ marginTop: '12px', paddingLeft: '16px', lineHeight: 1.6 }}>
            <li>Purpose &amp; scope</li>
            <li>Definitions</li>
            <li>Applicability</li>
            <li>Roles and responsibilities</li>
          </ul>
        </AccordionPanel>
      </AccordionItem>
      <AccordionItem value="part2">
        <AccordionHeader>Part 2: Requirements</AccordionHeader>
        <AccordionPanel>
          <Text color="muted" fontSize="sm">
            Detailed control statements, technical requirements, and documentation expectations for compliance.
          </Text>
          <ul style={{ marginTop: '12px', paddingLeft: '16px', lineHeight: 1.6 }}>
            <li>General requirements</li>
            <li>Technical requirements</li>
            <li>Documentation obligations</li>
            <li>Compliance verification</li>
          </ul>
        </AccordionPanel>
      </AccordionItem>
      <AccordionItem value="part3">
        <AccordionHeader>Part 3: Procedures</AccordionHeader>
        <AccordionPanel>
          <Text color="muted" fontSize="sm">
            Implementation steps, monitoring cadence, reporting workflows, and audit preparation guidance.
          </Text>
          <ul style={{ marginTop: '12px', paddingLeft: '16px', lineHeight: 1.6 }}>
            <li>Implementation procedures</li>
            <li>Compliance monitoring</li>
            <li>Reporting workflows</li>
            <li>Audit preparation</li>
          </ul>
        </AccordionPanel>
      </AccordionItem>
    </Accordion>
  );
}

function CrosswalkSection({ framework, crosswalkAxis, onAxisChange }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <Text color="muted" fontSize="sm">
        Align {framework.name} sections with other Universal Knowledge Graph axes to orchestrate automated control
        crosswalks and Azure Policy deployments.
      </Text>

      <Table aria-label="Existing crosswalk examples">
        <TableHeader>
          <TableRow>
            <TableHeaderCell>Section</TableHeaderCell>
            <TableHeaderCell>Pillar (Axis 1)</TableHeaderCell>
            <TableHeaderCell>Method (Axis 9)</TableHeaderCell>
            <TableHeaderCell>Compliance (Axis 8)</TableHeaderCell>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>Part 1.1</TableCell>
            <TableCell>P1.1.2 Acquisition Fundamentals</TableCell>
            <TableCell>M3.2 Regulatory Analysis</TableCell>
            <TableCell>C2.1 Documentation</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Part 1.3</TableCell>
            <TableCell>P1.2.1 Terminology</TableCell>
            <TableCell>M1.1 Definition Mapping</TableCell>
            <TableCell>C1.3 Term Alignment</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Part 2.2</TableCell>
            <TableCell>P2.3.1 Technical Standards</TableCell>
            <TableCell>M5.4 Technical Validation</TableCell>
            <TableCell>C3.5 Technical Verification</TableCell>
          </TableRow>
        </TableBody>
      </Table>

      <Card appearance="subtle">
        <Card.Header header={<Text fontWeight="semibold">Create new crosswalk mapping</Text>} />
        <Card.Body>
          <div style={{ display: 'grid', gap: '16px' }}>
            <div>
              <Text fontWeight="semibold" fontSize="sm">
                Section
              </Text>
              <Input placeholder="Enter section number" />
            </div>
            <div>
              <Text fontWeight="semibold" fontSize="sm">
                Destination axis
              </Text>
              <Dropdown
                options={crosswalkOptions}
                value={crosswalkAxis}
                onChange={(value) => onAxisChange(value)}
                placeholder="Choose axis"
              />
            </div>
            <div>
              <Text fontWeight="semibold" fontSize="sm">
                Destination element
              </Text>
              <Input placeholder="Enter or search for element" />
            </div>
            <div>
              <Text fontWeight="semibold" fontSize="sm">
                Mapping notes
              </Text>
              <Textarea rows={3} placeholder="Capture rationale, controls, or mitigations" />
            </div>
            <div>
              <Button variant="primary">Create mapping</Button>
            </div>
          </div>
        </Card.Body>
      </Card>
    </div>
  );
}
