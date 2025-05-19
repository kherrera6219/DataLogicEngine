
import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { Card, Button } from '../components/ui';
import Badge from '../components/ui/Badge';

export default function ComplianceDashboard() {
  const [complianceStatus, setComplianceStatus] = useState(null);
  const [securityStatus, setSecurityStatus] = useState(null);
  const [auditEvents, setAuditEvents] = useState([]);
  const [complianceEvents, setComplianceEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [reportData, setReportData] = useState(null);
  const [generateReportLoading, setGenerateReportLoading] = useState(false);
  
  useEffect(() => {
    // Fetch initial data
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
      // Fetch recent audit events
      const auditResponse = await fetch('/api/security/audit/events?limit=10');
      const auditData = await auditResponse.json();
      setAuditEvents(auditData.events || []);

      // Fetch recent compliance events
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
          end_date: today.toISOString()
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

  const runSecurityScan = async () => {
    try {
      await fetch('/api/security/scan', { method: 'POST' });
      // Refresh security status after scan
      fetchSecurityStatus();
    } catch (error) {
      console.error('Error running security scan:', error);
    }
  };

  const getStatusColor = (status) => {
    if (!status) return 'bg-gray-500';
    
    switch(status.toLowerCase()) {
      case 'compliant':
      case 'healthy':
        return 'bg-green-500';
      case 'warning':
      case 'vulnerable':
        return 'bg-yellow-500';
      case 'non_compliant':
      case 'critical':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const renderOverviewTab = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Compliance Status Card */}
      <Card className="p-6">
        <h3 className="text-xl font-bold mb-4">SOC 2 Compliance Status</h3>
        {complianceStatus ? (
          <div>
            <div className="flex items-center mb-4">
              <div className={`w-4 h-4 rounded-full mr-2 ${getStatusColor(complianceStatus.overall_status)}`}></div>
              <span className="text-lg font-medium">
                Overall: {complianceStatus.overall_status?.toUpperCase() || 'Unknown'}
              </span>
            </div>
            
            <h4 className="font-semibold mb-2">Trust Service Criteria:</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {complianceStatus.categories && Object.entries(complianceStatus.categories).map(([category, state]) => (
                <div key={category} className="flex items-center">
                  <div className={`w-3 h-3 rounded-full mr-2 ${getStatusColor(state.status)}`}></div>
                  <span className="capitalize">{category.replace('_', ' ')}: {state.status}</span>
                </div>
              ))}
            </div>
            
            <div className="mt-4 text-sm text-gray-500">
              Last updated: {new Date(complianceStatus.timestamp).toLocaleString()}
            </div>
          </div>
        ) : (
          <div className="text-gray-500">Loading compliance data...</div>
        )}
      </Card>

      {/* Security Status Card */}
      <Card className="p-6">
        <h3 className="text-xl font-bold mb-4">Security Status</h3>
        {securityStatus ? (
          <div>
            <div className="flex items-center mb-4">
              <div className={`w-4 h-4 rounded-full mr-2 ${getStatusColor(securityStatus.status)}`}></div>
              <span className="text-lg font-medium">
                Status: {securityStatus.status?.toUpperCase() || 'Unknown'}
              </span>
            </div>
            
            <div className="grid grid-cols-2 gap-2 mb-4">
              <div className="border rounded p-3">
                <div className="text-lg font-bold text-red-500">{securityStatus.vulnerabilities_count}</div>
                <div className="text-sm">Vulnerabilities</div>
              </div>
              <div className="border rounded p-3">
                <div className="text-lg font-bold text-yellow-500">{securityStatus.warnings_count}</div>
                <div className="text-sm">Warnings</div>
              </div>
            </div>
            
            <div className="flex items-center mb-2">
              <svg className="w-5 h-5 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path>
              </svg>
              <span>Encryption: {securityStatus.encryption_enabled ? 'Enabled' : 'Disabled'}</span>
            </div>
            
            <div className="mt-4 text-sm text-gray-500">
              Last scan: {securityStatus.last_scan_time ? new Date(securityStatus.last_scan_time).toLocaleString() : 'Never'}
            </div>
            
            <Button className="mt-4 w-full" onClick={runSecurityScan}>
              Run Security Scan
            </Button>
          </div>
        ) : (
          <div className="text-gray-500">Loading security data...</div>
        )}
      </Card>

      {/* Recent Compliance Events */}
      <Card className="p-6">
        <h3 className="text-xl font-bold mb-4">Recent Compliance Events</h3>
        {loading ? (
          <div className="text-gray-500">Loading events...</div>
        ) : complianceEvents.length > 0 ? (
          <div className="overflow-auto max-h-72">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {complianceEvents.map((event) => (
                  <tr key={event.id} className="hover:bg-gray-50">
                    <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                      {new Date(event.timestamp).toLocaleString()}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-sm">
                      <Badge color={event.category === 'security' ? 'blue' : 
                              event.category === 'privacy' ? 'purple' : 
                              event.category === 'availability' ? 'green' : 
                              'gray'}>
                        {event.category}
                      </Badge>
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-sm">
                      <Badge color={event.type === 'violation' ? 'red' : 
                              event.type === 'remediation' ? 'green' : 'gray'}>
                        {event.type}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-gray-500 text-center py-4">No recent compliance events</div>
        )}
      </Card>

      {/* Recent Audit Logs */}
      <Card className="p-6">
        <h3 className="text-xl font-bold mb-4">Recent Audit Logs</h3>
        {loading ? (
          <div className="text-gray-500">Loading logs...</div>
        ) : auditEvents.length > 0 ? (
          <div className="overflow-auto max-h-72">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Event</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {auditEvents.map((event) => (
                  <tr key={event.id} className="hover:bg-gray-50">
                    <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                      {new Date(event.timestamp).toLocaleString()}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-sm">
                      {event.event_type}
                      {event.action && ` / ${event.action}`}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-sm">
                      <Badge color={event.status === 'success' ? 'green' : 'red'}>
                        {event.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-gray-500 text-center py-4">No recent audit logs</div>
        )}
      </Card>
    </div>
  );

  const renderReportTab = () => (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">SOC 2 Compliance Report</h2>
        <Button onClick={generateReport} disabled={generateReportLoading}>
          {generateReportLoading ? 'Generating...' : 'Generate New Report'}
        </Button>
      </div>

      {reportData ? (
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="mb-6 pb-4 border-b">
            <h3 className="text-xl font-semibold mb-2">Report Summary</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="bg-gray-50 p-3 rounded">
                <div className="text-sm text-gray-500">Report ID</div>
                <div className="font-mono text-sm truncate">{reportData.report_id}</div>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <div className="text-sm text-gray-500">Report Type</div>
                <div>{reportData.report_type}</div>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <div className="text-sm text-gray-500">Period Start</div>
                <div>{new Date(reportData.period_start).toLocaleDateString()}</div>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <div className="text-sm text-gray-500">Period End</div>
                <div>{new Date(reportData.period_end).toLocaleDateString()}</div>
              </div>
            </div>
            
            <div className="flex items-center">
              <div className="mr-4">
                <div className="text-sm text-gray-500">Overall Compliance Score</div>
                <div className="text-3xl font-bold">
                  {reportData.overall_compliance_score}%
                </div>
              </div>
              <div className="flex-grow h-4 bg-gray-200 rounded-full">
                <div 
                  className={`h-4 rounded-full ${
                    reportData.overall_compliance_score > 90 ? 'bg-green-500' : 
                    reportData.overall_compliance_score > 70 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${reportData.overall_compliance_score}%` }}
                ></div>
              </div>
            </div>
          </div>

          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-4">Trust Service Criteria Scores</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {Object.entries(reportData.compliance_scores).map(([category, score]) => (
                <div key={category} className="flex items-center">
                  <div className="w-32 capitalize font-medium">{category.replace('_', ' ')}</div>
                  <div className="flex-grow h-4 bg-gray-200 rounded-full mr-2">
                    <div 
                      className={`h-4 rounded-full ${
                        score > 90 ? 'bg-green-500' : 
                        score > 70 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${score}%` }}
                    ></div>
                  </div>
                  <div className="w-12 text-right font-medium">{score}%</div>
                </div>
              ))}
            </div>
          </div>

          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-4">Event Summary</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {Object.entries(reportData.event_counts).map(([category, counts]) => (
                <div key={category} className="bg-gray-50 p-4 rounded">
                  <h4 className="font-medium mb-2 capitalize">{category.replace('_', ' ')}</h4>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div>
                      <div className="text-lg font-bold">{counts.check}</div>
                      <div className="text-xs text-gray-500">Checks</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-red-500">{counts.violation}</div>
                      <div className="text-xs text-gray-500">Violations</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-green-500">{counts.remediation}</div>
                      <div className="text-xs text-gray-500">Remediations</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {reportData.event_sample && reportData.event_sample.length > 0 && (
            <div>
              <h3 className="text-xl font-semibold mb-4">Event Samples</h3>
              <div className="overflow-auto max-h-72">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Details</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {reportData.event_sample.map((event) => (
                      <tr key={event.id} className="hover:bg-gray-50">
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {new Date(event.timestamp).toLocaleString()}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm">
                          <Badge color={event.category === 'security' ? 'blue' : 
                                  event.category === 'privacy' ? 'purple' : 
                                  event.category === 'availability' ? 'green' : 
                                  'gray'}>
                            {event.category}
                          </Badge>
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm">
                          <Badge color={event.type === 'violation' ? 'red' : 
                                  event.type === 'remediation' ? 'green' : 'gray'}>
                            {event.type}
                          </Badge>
                        </td>
                        <td className="px-3 py-2 text-sm text-gray-900 max-w-md truncate">
                          {event.details}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div className="mt-6 pt-4 border-t text-sm text-gray-500">
            Report generated at: {new Date(reportData.generated_at).toLocaleString()}
          </div>
        </div>
      ) : (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <p className="text-gray-500 mb-4">No report data available. Generate a new report to view compliance statistics.</p>
          <Button onClick={generateReport} disabled={generateReportLoading}>
            {generateReportLoading ? 'Generating...' : 'Generate Report'}
          </Button>
        </div>
      )}
    </div>
  );

  const renderControlsTab = () => (
    <div>
      <h2 className="text-2xl font-bold mb-6">SOC 2 Controls</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Security Controls */}
        <Card className="p-6">
          <h3 className="text-xl font-bold mb-4">Security Controls</h3>
          <div className="space-y-4">
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex justify-between items-center">
                <span className="font-medium">Encryption at Rest</span>
                <Badge color="green">Implemented</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">Data is encrypted when stored using industry-standard algorithms.</p>
            </div>
            
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex justify-between items-center">
                <span className="font-medium">Access Controls</span>
                <Badge color="green">Implemented</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">Role-based access control with principle of least privilege.</p>
            </div>
            
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex justify-between items-center">
                <span className="font-medium">Vulnerability Scanning</span>
                <Badge color="green">Implemented</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">Regular automated scanning for security vulnerabilities.</p>
            </div>
            
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex justify-between items-center">
                <span className="font-medium">Security Monitoring</span>
                <Badge color="green">Implemented</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">24/7 monitoring of security events and alerts.</p>
            </div>
          </div>
        </Card>
        
        {/* Availability Controls */}
        <Card className="p-6">
          <h3 className="text-xl font-bold mb-4">Availability Controls</h3>
          <div className="space-y-4">
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex justify-between items-center">
                <span className="font-medium">High Availability</span>
                <Badge color="green">Implemented</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">Redundant infrastructure to ensure continuous operation.</p>
            </div>
            
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex justify-between items-center">
                <span className="font-medium">Backup Systems</span>
                <Badge color="green">Implemented</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">Regular backups with verified recovery procedures.</p>
            </div>
            
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex justify-between items-center">
                <span className="font-medium">Monitoring</span>
                <Badge color="green">Implemented</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">Continuous monitoring of system performance and availability.</p>
            </div>
            
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex justify-between items-center">
                <span className="font-medium">Incident Response</span>
                <Badge color="green">Implemented</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">Documented procedures for handling service disruptions.</p>
            </div>
          </div>
        </Card>
        
        {/* Processing Integrity Controls */}
        <Card className="p-6">
          <h3 className="text-xl font-bold mb-4">Processing Integrity Controls</h3>
          <div className="space-y-4">
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex justify-between items-center">
                <span className="font-medium">Input Validation</span>
                <Badge color="green">Implemented</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">Validation of input data for completeness and accuracy.</p>
            </div>
            
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex justify-between items-center">
                <span className="font-medium">Error Handling</span>
                <Badge color="green">Implemented</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">Procedures for identifying and handling processing errors.</p>
            </div>
            
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex justify-between items-center">
                <span className="font-medium">Transaction Logs</span>
                <Badge color="green">Implemented</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">Detailed logging of all system transactions.</p>
            </div>
            
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex justify-between items-center">
                <span className="font-medium">Quality Assurance</span>
                <Badge color="green">Implemented</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">Testing procedures to verify processing accuracy.</p>
            </div>
          </div>
        </Card>
        
        {/* Confidentiality Controls */}
        <Card className="p-6">
          <h3 className="text-xl font-bold mb-4">Confidentiality Controls</h3>
          <div className="space-y-4">
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex justify-between items-center">
                <span className="font-medium">Data Classification</span>
                <Badge color="green">Implemented</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">System for identifying and managing sensitive data.</p>
            </div>
            
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex justify-between items-center">
                <span className="font-medium">Transport Encryption</span>
                <Badge color="green">Implemented</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">Encryption of data during transmission using TLS.</p>
            </div>
            
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex justify-between items-center">
                <span className="font-medium">Access Restrictions</span>
                <Badge color="green">Implemented</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">Controls to prevent unauthorized access to confidential data.</p>
            </div>
            
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex justify-between items-center">
                <span className="font-medium">Data Disposal</span>
                <Badge color="green">Implemented</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">Secure procedures for disposal of confidential information.</p>
            </div>
          </div>
        </Card>
        
        {/* Privacy Controls */}
        <Card className="p-6">
          <h3 className="text-xl font-bold mb-4">Privacy Controls</h3>
          <div className="space-y-4">
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex justify-between items-center">
                <span className="font-medium">Notice</span>
                <Badge color="green">Implemented</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">Clear communication about data collection and use.</p>
            </div>
            
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex justify-between items-center">
                <span className="font-medium">Choice and Consent</span>
                <Badge color="green">Implemented</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">Options for individuals regarding their personal information.</p>
            </div>
            
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex justify-between items-center">
                <span className="font-medium">Access</span>
                <Badge color="green">Implemented</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">Procedures for individuals to access their personal information.</p>
            </div>
            
            <div className="p-3 bg-gray-50 rounded">
              <div className="flex justify-between items-center">
                <span className="font-medium">Data Retention</span>
                <Badge color="green">Implemented</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">Limits on retention of personal information.</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );

  return (
    <Layout>
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">SOC 2 Type 2 Compliance Dashboard</h1>
          <div className="flex space-x-2">
            <Button onClick={generateReport} disabled={generateReportLoading}>
              {generateReportLoading ? 'Generating...' : 'Generate Report'}
            </Button>
            <Button onClick={runSecurityScan} variant="outline">
              Run Security Scan
            </Button>
          </div>
        </div>

        <div className="mb-6">
          <div className="border-b flex">
            <button
              className={`py-2 px-4 font-medium text-sm focus:outline-none ${
                activeTab === 'overview' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'
              }`}
              onClick={() => setActiveTab('overview')}
            >
              Overview
            </button>
            <button
              className={`py-2 px-4 font-medium text-sm focus:outline-none ${
                activeTab === 'report' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'
              }`}
              onClick={() => setActiveTab('report')}
            >
              Compliance Report
            </button>
            <button
              className={`py-2 px-4 font-medium text-sm focus:outline-none ${
                activeTab === 'controls' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'
              }`}
              onClick={() => setActiveTab('controls')}
            >
              Controls
            </button>
          </div>
        </div>

        {/* Tab Content */}
        <div className="mt-6">
          {activeTab === 'overview' && renderOverviewTab()}
          {activeTab === 'report' && renderReportTab()}
          {activeTab === 'controls' && renderControlsTab()}
        </div>
      </div>
    </Layout>
  );
}
