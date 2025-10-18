import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { makeStyles, shorthands, TabList, Tab, Spinner, Divider } from '@fluentui/react-components';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Text from '../components/ui/Text';

const useStyles = makeStyles({
  grid: {
    display: 'grid',
    gap: '24px',
  },
  metrics: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
    gap: '24px',
  },
  metricValue: {
    fontSize: '2.25rem',
    fontWeight: 700,
    margin: 0,
  },
  tabContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  list: {
    display: 'grid',
    gap: '12px',
  },
  listItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: 'var(--colorNeutralBackground3)',
    borderRadius: '14px',
    ...shorthands.padding('16px', '20px'),
    border: '1px solid rgba(255,255,255,0.04)',
  },
  listMeta: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  reportCard: {
    display: 'grid',
    gap: '16px',
  },
});

const statusColorMap = {
  compliant: 'success',
  healthy: 'success',
  warning: 'warning',
  vulnerable: 'warning',
  non_compliant: 'danger',
  critical: 'danger',
};

export default function ComplianceDashboard() {
  const styles = useStyles();
  const [complianceStatus, setComplianceStatus] = useState(null);
  const [securityStatus, setSecurityStatus] = useState(null);
  const [auditEvents, setAuditEvents] = useState([]);
  const [complianceEvents, setComplianceEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [reportData, setReportData] = useState(null);
  const [generateReportLoading, setGenerateReportLoading] = useState(false);

  useEffect(() => {
    fetchComplianceStatus();
    fetchSecurityStatus();
    fetchRecentEvents();
  }, []);

  const fetchComplianceStatus = async () => {
    try {
      const response = await fetch('/api/security/compliance/status');
      const data = await response.json();
      setComplianceStatus(data);
    } catch (error) {
      console.error('Error fetching compliance status:', error);
    }
  };

  const fetchSecurityStatus = async () => {
    try {
      const response = await fetch('/api/security/status');
      const data = await response.json();
      setSecurityStatus(data);
    } catch (error) {
      console.error('Error fetching security status:', error);
    }
  };

  const fetchRecentEvents = async () => {
    try {
      const auditResponse = await fetch('/api/security/audit/events?limit=10');
      const auditData = await auditResponse.json();
      setAuditEvents(auditData.events || []);

      const complianceResponse = await fetch('/api/security/compliance/events?limit=10');
      const complianceData = await complianceResponse.json();
      setComplianceEvents(complianceData.events || []);

      setLoading(false);
    } catch (error) {
      console.error('Error fetching events:', error);
      setLoading(false);
    }
  };

  const generateReport = async () => {
    setGenerateReportLoading(true);
    try {
      const today = new Date();
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(today.getDate() - 30);

      const response = await fetch('/api/security/compliance/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start_date: thirtyDaysAgo.toISOString(),
          end_date: today.toISOString(),
        }),
      });

      const data = await response.json();
      setReportData(data);
      setActiveTab('report');
    } catch (error) {
      console.error('Error generating report:', error);
    } finally {
      setGenerateReportLoading(false);
    }
  };

  const statusBadge = (status) => (
    <Badge appearance="ghost" color={statusColorMap[status?.toLowerCase()] || 'informative'}>
      {status?.replace('_', ' ') || 'Unknown'}
    </Badge>
  );

  const renderOverview = () => (
    <div className={styles.metrics}>
      <Card>
        <Card.Body>
          <Text fontSize="sm" color="muted">
            SOC 2 compliance status
          </Text>
          <p className={styles.metricValue}>
            {complianceStatus?.overall_status?.toUpperCase() || 'N/A'}
          </p>
          <Text fontSize="sm" color="muted">
            Last updated {complianceStatus?.timestamp && new Date(complianceStatus.timestamp).toLocaleString()}
          </Text>
          <Divider />
          <Text fontWeight="semibold" fontSize="sm">
            Trust service criteria
          </Text>
          <div className={styles.list}>
            {complianceStatus?.categories &&
              Object.entries(complianceStatus.categories).map(([category, state]) => (
                <div key={category} className={styles.listItem}>
                  <div className={styles.listMeta}>
                    <Text fontWeight="semibold">{category.replace('_', ' ')}</Text>
                    <Text fontSize="sm" color="muted">
                      Controls evaluated: {state.controls_evaluated || 'n/a'}
                    </Text>
                  </div>
                  {statusBadge(state.status)}
                </div>
              ))}
          </div>
        </Card.Body>
      </Card>

      <Card>
        <Card.Body>
          <Text fontSize="sm" color="muted">
            Security posture
          </Text>
          <p className={styles.metricValue}>{securityStatus?.status?.toUpperCase() || 'N/A'}</p>
          <Text fontSize="sm" color="muted">
            Attack surface monitoring and vulnerability management coverage
          </Text>
          <Divider />
          <Button variant="primary" onClick={runSecurityScan}>Run security scan</Button>
        </Card.Body>
      </Card>

      <Card>
        <Card.Body className={styles.reportCard}>
          <Text fontSize="sm" color="muted">
            Executive report
          </Text>
          <Text fontWeight="semibold">
            Generate a 30-day compliance and security summary
          </Text>
          <Button
            variant="primary"
            onClick={generateReport}
            disabled={generateReportLoading}
          >
            {generateReportLoading ? 'Preparing report…' : 'Generate report'}
          </Button>
          {reportData && (
            <Text fontSize="sm" color="muted">
              Last generated {new Date(reportData.generated_at).toLocaleString()}
            </Text>
          )}
        </Card.Body>
      </Card>
    </div>
  );

  const renderEventList = (events = []) => (
    <div className={styles.list}>
      {events.length === 0 && <Text color="muted">No recent events.</Text>}
      {events.map((event, idx) => (
        <div key={idx} className={styles.listItem}>
          <div className={styles.listMeta}>
            <Text fontWeight="semibold">{event.title || event.type}</Text>
            <Text fontSize="sm" color="muted">
              {event.description || event.summary}
            </Text>
          </div>
          <Text fontSize="sm" color="muted">
            {event.timestamp && new Date(event.timestamp).toLocaleString()}
          </Text>
        </div>
      ))}
    </div>
  );

  const renderReport = () => {
    if (!reportData) {
      return <Text color="muted">Generate a report to view consolidated insights.</Text>;
    }

    return (
      <Card>
        <Card.Body>
          <Text fontWeight="semibold">Summary</Text>
          <Text fontSize="sm" color="muted">
            Coverage: {reportData.coverage}% — Findings: {reportData.findings?.length || 0}
          </Text>
          <Divider />
          <div className={styles.list}>
            {(reportData.findings || []).map((finding, index) => (
              <div key={index} className={styles.listItem}>
                <div className={styles.listMeta}>
                  <Text fontWeight="semibold">{finding.title}</Text>
                  <Text fontSize="sm" color="muted">
                    {finding.description}
                  </Text>
                </div>
                {statusBadge(finding.severity)}
              </div>
            ))}
          </div>
        </Card.Body>
      </Card>
    );
  };

  const runSecurityScan = async () => {
    try {
      await fetch('/api/security/scan', { method: 'POST' });
      fetchSecurityStatus();
    } catch (error) {
      console.error('Error running security scan:', error);
    }
  };

  return (
    <Layout>
      <div className={styles.grid}>
        <Text fontSize="3xl" fontWeight="bold">
          Compliance operations dashboard
        </Text>
        <Text color="muted">
          Microsoft enterprise controls mapped across SOC 2, regulatory obligations, and UKG operational telemetry.
        </Text>

        {loading ? (
          <Spinner size="large" label="Loading compliance insights" />
        ) : (
          <>
            {renderOverview()}

            <div className={styles.tabContainer}>
              <TabList selectedValue={activeTab} onTabSelect={(event, data) => setActiveTab(data.value)}>
                <Tab value="overview">Overview</Tab>
                <Tab value="audit">Audit events</Tab>
                <Tab value="compliance">Compliance events</Tab>
                <Tab value="report">Reports</Tab>
              </TabList>

              {activeTab === 'overview' && renderOverview()}
              {activeTab === 'audit' && renderEventList(auditEvents)}
              {activeTab === 'compliance' && renderEventList(complianceEvents)}
              {activeTab === 'report' && renderReport()}
            </div>
          </>
        )}
      </div>
    </Layout>
  );
}
