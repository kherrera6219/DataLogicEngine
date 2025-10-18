
import React, { useEffect, useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { Card, Button, Input, Label } from '../components/ui';

export default function LoginPage() {
  const [selectedRole, setSelectedRole] = useState('');
  const [isSimulationMode, setIsSimulationMode] = useState(true);
  const [isClient, setIsClient] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const router = useRouter();

  useEffect(() => {
    setIsClient(true);
  }, []);

  const roles = [
    { id: 'acquisition', name: 'Acquisition Expert', icon: 'bi-briefcase' },
    { id: 'industry', name: 'Industry Expert', icon: 'bi-building' },
    { id: 'regulatory', name: 'Regulatory Expert', icon: 'bi-shield-check' },
    { id: 'compliance', name: 'Compliance Expert', icon: 'bi-clipboard-check' }
  ];

  const handleLogin = (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (!selectedRole) {
      setErrorMessage('Please select a role before continuing.');
      return;
    }

    if (!isClient) {
      setErrorMessage('Login is not available until the page finishes loading.');
      return;
    }

    try {
      if (typeof window === 'undefined' || !window.sessionStorage) {
        throw new Error('Session storage is not available.');
      }

      window.sessionStorage.setItem('userRole', selectedRole);
      window.sessionStorage.setItem('simulationMode', JSON.stringify(isSimulationMode));
      router.push('/knowledge-graph');
    } catch (err) {
      console.error('Unable to persist login preferences:', err);
      setErrorMessage('We could not save your login preferences. Please check your browser settings and try again.');
    }
  };

  return (
    <div className="min-vh-100 d-flex align-items-center justify-content-center bg-dark">
      <Head>
        <title>Login - Universal Knowledge Graph</title>
      </Head>
      
      <Card className="login-card" style={{ maxWidth: '500px', width: '100%' }}>
        <Card.Header>
          <Card.Title className="text-center">Universal Knowledge Graph</Card.Title>
        </Card.Header>
        <Card.Body>
          <h4 className="mb-4 text-center">Role Selection & Login</h4>
          
          <form onSubmit={handleLogin}>
            <fieldset className="mb-4">
              <legend className="form-label">Select Your Role</legend>
              <div className="row g-3 mt-2" role="radiogroup" aria-label="Available user roles">
                {roles.map(role => {
                  const isSelected = selectedRole === role.id;
                  return (
                    <div key={role.id} className="col-6">
                      <button
                        type="button"
                        className={`role-card w-100 p-3 text-center border rounded ${isSelected ? 'border-primary bg-primary bg-opacity-10' : 'border-secondary bg-dark bg-opacity-25'}`}
                        onClick={() => {
                          setSelectedRole(role.id);
                          setErrorMessage('');
                        }}
                        aria-pressed={isSelected}
                        aria-label={role.name}
                      >
                        <i className={`bi ${role.icon} fs-1 mb-2`} aria-hidden="true"></i>
                        <div id={`role-${role.id}-label`} className="fw-semibold">{role.name}</div>
                      </button>
                    </div>
                  );
                })}
              </div>
            </fieldset>

            <div className="mb-4">
              <Label htmlFor="username">Username</Label>
              <Input 
                id="username" 
                placeholder="Enter your username"
                required
              />
            </div>
            
            <div className="mb-4">
              <Label htmlFor="password">Password</Label>
              <Input 
                id="password" 
                type="password" 
                placeholder="Enter your password"
                required
              />
            </div>
            
            <div className="mb-4 form-check form-switch">
              <input
                className="form-check-input"
                type="checkbox"
                id="simulationToggle"
                checked={isSimulationMode}
                onChange={() => setIsSimulationMode(!isSimulationMode)}
                aria-describedby="simulation-toggle-description"
              />
              <label className="form-check-label" htmlFor="simulationToggle" id="simulation-toggle-description">
                Live Agent Simulation Mode {isSimulationMode ? 'On' : 'Off'}
              </label>
            </div>

            {errorMessage && (
              <div className="alert alert-warning" role="alert" aria-live="assertive">
                {errorMessage}
              </div>
            )}

            <div className="d-grid">
              <Button type="submit" disabled={!selectedRole}>
                Login & Continue
              </Button>
            </div>
          </form>
        </Card.Body>
        <Card.Footer className="text-center text-muted">
          <small>Secure access with SSO or Azure AD integration</small>
        </Card.Footer>
      </Card>
    </div>
  );
}
