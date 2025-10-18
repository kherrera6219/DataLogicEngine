import React, { useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { Card, Button, Input, Label, Text } from '../components/ui';
import {
  Switch,
  makeStyles,
  shorthands,
} from '@fluentui/react-components';
import {
  bundleIcon,
  Briefcase24Filled,
  Briefcase24Regular,
  Building24Filled,
  Building24Regular,
  ShieldCheckmark24Filled,
  ShieldCheckmark24Regular,
  ClipboardTaskListLtr24Filled,
  ClipboardTaskListLtr24Regular,
} from '@fluentui/react-icons';

const useStyles = makeStyles({
  page: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'radial-gradient(circle at top, rgba(50,116,198,0.35), rgba(13,17,23,0.95) 60%)',
    padding: '32px',
  },
  card: {
    maxWidth: '520px',
    width: '100%',
  },
  roleGrid: {
    display: 'grid',
    gap: '12px',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
  },
  roleButton: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-start',
    gap: '8px',
    textAlign: 'left',
    borderRadius: '16px',
    border: '1px solid rgba(255,255,255,0.08)',
    ...shorthands.padding('12px', '14px'),
    cursor: 'pointer',
    transition: 'border-color 0.2s ease, transform 0.2s ease',
  },
  roleButtonActive: {
    borderColor: 'var(--colorBrandStroke1)',
    boxShadow: '0 12px 30px rgba(28, 90, 163, 0.25)',
    transform: 'translateY(-2px)',
  },
  toggleRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '12px',
  },
});

const AcquisitionIcon = bundleIcon(Briefcase24Filled, Briefcase24Regular);
const IndustryIcon = bundleIcon(Building24Filled, Building24Regular);
const RegulatoryIcon = bundleIcon(ShieldCheckmark24Filled, ShieldCheckmark24Regular);
const ComplianceIcon = bundleIcon(ClipboardTaskListLtr24Filled, ClipboardTaskListLtr24Regular);

const roles = [
  { id: 'acquisition', name: 'Acquisition Expert', description: 'Source, negotiate, and manage procurement workflows.', icon: AcquisitionIcon },
  { id: 'industry', name: 'Industry Expert', description: 'Align sector intelligence with knowledge graph operations.', icon: IndustryIcon },
  { id: 'regulatory', name: 'Regulatory Expert', description: 'Interpret mandates and maintain crosswalk alignment.', icon: RegulatoryIcon },
  { id: 'compliance', name: 'Compliance Expert', description: 'Monitor controls, attest to posture, and remediate gaps.', icon: ComplianceIcon },
];

export default function LoginPage() {
  const styles = useStyles();
  const router = useRouter();
  const [selectedRole, setSelectedRole] = useState('');
  const [isSimulationMode, setIsSimulationMode] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = (event) => {
    event.preventDefault();
    sessionStorage.setItem('userRole', selectedRole);
    sessionStorage.setItem('simulationMode', isSimulationMode);
    router.push('/knowledge-graph');
  };

  return (
    <div className={styles.page}>
      <Head>
        <title>Login - Universal Knowledge Graph</title>
      </Head>

      <Card className={styles.card} appearance="subtle">
        <Card.Header
          header={<Text fontWeight="semibold">Universal Knowledge Graph</Text>}
          description="Authenticate to access Microsoft enterprise-aligned knowledge experiences."
        />
          <Card.Body>
            <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div>
                <Label>Select your role</Label>
                <div className={styles.roleGrid} role="radiogroup" aria-label="Role selection">
                  {roles.map((role) => {
                    const Icon = role.icon;
                    const isActive = selectedRole === role.id;
                    return (
                      <div
                        key={role.id}
                        role="radio"
                        tabIndex={0}
                        aria-checked={isActive}
                        className={`${styles.roleButton} ${isActive ? styles.roleButtonActive : ''}`}
                        onClick={() => setSelectedRole(role.id)}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter' || event.key === ' ') {
                            event.preventDefault();
                            setSelectedRole(role.id);
                          }
                        }}
                      >
                        <Icon />
                        <div>
                          <Text fontWeight="semibold">{role.name}</Text>
                          <Text fontSize="sm" color="muted">
                            {role.description}
                          </Text>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div>
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  placeholder="Enter your username"
                  value={username}
                  onChange={(_, data) => setUsername(data.value)}
                  required
                />
              </div>

              <div>
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(_, data) => setPassword(data.value)}
                  required
                />
              </div>

              <div className={styles.toggleRow}>
                <div>
                  <Text fontWeight="semibold">Live agent simulation mode</Text>
                  <Text fontSize="sm" color="muted">
                    Toggle to control whether AI-driven simulation data augments your session.
                  </Text>
                </div>
                <Switch
                  checked={isSimulationMode}
                  onChange={(_, data) => setIsSimulationMode(data.checked)}
                />
              </div>

              <Button type="submit" variant="primary" disabled={!selectedRole || !username || !password}>
                Login and continue
              </Button>
            </form>
          </Card.Body>
          <Card.Footer>
            <Text fontSize="sm" color="muted">
              Enterprise-ready SSO integrations supported: Azure AD, Entra ID, Microsoft 365.
            </Text>
          </Card.Footer>
      </Card>
    </div>
  );
}
