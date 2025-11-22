
import React, { useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { Card, Button, Input, Label } from '../components/ui';

export default function LoginPage() {
  const [selectedRole, setSelectedRole] = useState('');
  const [isSimulationMode, setIsSimulationMode] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const roles = [
    { id: 'acquisition', name: 'Acquisition Expert', icon: 'bi-briefcase' },
    { id: 'industry', name: 'Industry Expert', icon: 'bi-building' },
    { id: 'regulatory', name: 'Regulatory Expert', icon: 'bi-shield-check' },
    { id: 'compliance', name: 'Compliance Expert', icon: 'bi-clipboard-check' }
  ];

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          password,
          role: selectedRole,
          simulationMode: isSimulationMode
        }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        setError(data.error || 'Login failed. Please check your credentials.');
        return;
      }

      // Store user preferences in localStorage (non-sensitive data only)
      if (typeof window !== 'undefined') {
        localStorage.setItem('userRole', selectedRole);
        localStorage.setItem('simulationMode', isSimulationMode);
        localStorage.setItem('username', data.user.username);
      }

      // Redirect to knowledge graph
      router.push('/knowledge-graph');
    } catch (err) {
      console.error('Login error:', err);
      setError('An error occurred during login. Please try again.');
    } finally {
      setIsLoading(false);
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

          {error && (
            <div className="alert alert-danger" role="alert">
              {error}
            </div>
          )}

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
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>

            <div className="mb-4">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
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
              <Button type="submit" disabled={!selectedRole || !username || !password || isLoading}>
                {isLoading ? 'Logging in...' : 'Login & Continue'}
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
