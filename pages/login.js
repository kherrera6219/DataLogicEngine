
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
            <div className="mb-4">
              <Label>Select Your Role</Label>
              <div className="row g-3 mt-2">
                {roles.map(role => (
                  <div key={role.id} className="col-6">
                    <div 
                      className={`role-card p-3 text-center border rounded cursor-pointer ${selectedRole === role.id ? 'border-primary bg-primary bg-opacity-10' : 'border-secondary'}`}
                      onClick={() => setSelectedRole(role.id)}
                    >
                      <i className={`bi ${role.icon} fs-1 mb-2`}></i>
                      <div>{role.name}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
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
              />
              <label className="form-check-label" htmlFor="simulationToggle">
                Live Agent Simulation Mode {isSimulationMode ? 'On' : 'Off'}
              </label>
            </div>
            
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
