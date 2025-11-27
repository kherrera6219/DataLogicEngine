
import React, { useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { Card, Button, Input, Label } from '../components/ui';

export default function LoginPage() {
  const [selectedRole, setSelectedRole] = useState('');
  const [isSimulationMode, setIsSimulationMode] = useState(true);
  const router = useRouter();

  const roles = [
    { id: 'acquisition', name: 'Acquisition Expert', icon: 'bi-briefcase' },
    { id: 'industry', name: 'Industry Expert', icon: 'bi-building' },
    { id: 'regulatory', name: 'Regulatory Expert', icon: 'bi-shield-check' },
    { id: 'compliance', name: 'Compliance Expert', icon: 'bi-clipboard-check' }
  ];

  const handleLogin = (e) => {
    e.preventDefault();
    // Store selected role in sessionStorage
    sessionStorage.setItem('userRole', selectedRole);
    sessionStorage.setItem('simulationMode', isSimulationMode);
    router.push('/knowledge-graph');
  };

  return (
    <div className="min-vh-100 mesh-hero text-white d-flex align-items-center">
      <Head>
        <title>Login - Universal Knowledge Graph</title>
      </Head>

      <div className="container py-5">
        <div className="row g-4 align-items-stretch">
          <div className="col-lg-5">
            <div className="glass-panel p-4 h-100">
              <span className="section-title">Secure Access</span>
              <h2 className="mb-3">Authentication</h2>
              <p className="text-white-50">SSO, MFA, biometrics, and role selection mapped to the 13-axis experience.</p>
              <div className="d-grid gap-2 mb-3">
                <Button variant="primary">
                  <i className="bi bi-microsoft me-2"></i> Continue with Azure AD
                </Button>
                <Button variant="secondary">
                  <i className="bi bi-lock me-2"></i> Continue with SAML / Okta
                </Button>
              </div>
              <div className="glass-border p-3">
                <div className="d-flex justify-content-between mb-2">
                  <span>MFA status</span>
                  <span className="badge bg-success">Enabled</span>
                </div>
                <p className="text-white-50 small mb-1">Touch ID / Face ID supported for mobile experiences.</p>
                <p className="text-white-50 small mb-0">Security key + passkey ready. Audit trail is active.</p>
              </div>
            </div>
          </div>

          <div className="col-lg-7">
            <Card className="h-100">
              <Card.Header>
                <Card.Title>Role selection & direct login</Card.Title>
              </Card.Header>
              <Card.Body>
                <form onSubmit={handleLogin} className="d-grid gap-3">
                  <div>
                    <Label>Select your role</Label>
                    <div className="row g-3 mt-2">
                      {roles.map(role => (
                        <div key={role.id} className="col-sm-6">
                          <div
                            className={`role-card p-3 h-100 text-center border rounded cursor-pointer ${selectedRole === role.id ? 'border-primary bg-primary bg-opacity-10' : 'border-secondary'}`}
                            onClick={() => setSelectedRole(role.id)}
                          >
                            <i className={`bi ${role.icon} fs-1 mb-2`}></i>
                            <div>{role.name}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="row g-3">
                    <div className="col-md-6">
                      <Label htmlFor="username">Email or Username</Label>
                      <Input id="username" placeholder="user@company.com" required />
                    </div>
                    <div className="col-md-6">
                      <Label htmlFor="password">Password</Label>
                      <Input id="password" type="password" placeholder="Enter password" required />
                    </div>
                  </div>

                  <div className="row g-3">
                    <div className="col-md-6">
                      <Label htmlFor="mfa">2FA / MFA code</Label>
                      <Input id="mfa" placeholder="000000" />
                    </div>
                    <div className="col-md-6 d-flex align-items-center justify-content-between">
                      <div className="form-check form-switch">
                        <input
                          className="form-check-input"
                          type="checkbox"
                          id="simulationToggle"
                          checked={isSimulationMode}
                          onChange={() => setIsSimulationMode(!isSimulationMode)}
                        />
                        <label className="form-check-label" htmlFor="simulationToggle">
                          Live agent simulation {isSimulationMode ? 'On' : 'Off'}
                        </label>
                      </div>
                      <div className="d-flex gap-2">
                        <Button variant="secondary">
                          <i className="bi bi-fingerprint me-2"></i> Biometric
                        </Button>
                        <Button variant="outline">
                          <i className="bi bi-shield-lock me-2"></i> Hardware key
                        </Button>
                      </div>
                    </div>
                  </div>

                  <div className="d-flex justify-content-between align-items-center">
                    <div className="d-flex flex-column text-white-50 small">
                      <span><i className="bi bi-shield-check me-2"></i>Audit logging active</span>
                      <span><i className="bi bi-geo-alt me-2"></i>Device + location tracking enabled</span>
                    </div>
                    <Button type="submit" variant="primary" disabled={!selectedRole}>
                      Continue to workspace
                    </Button>
                  </div>
                </form>
              </Card.Body>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
