'use client';

import { useState, useEffect } from 'react';
import { mcpApi, MCPStats } from '@/lib/api/mcp';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Server, Activity, Database, Terminal, Settings } from 'lucide-react';
import Link from 'next/link';
// import { useAuth } from '@/contexts/AuthContext'; // Not actually used in this component

export default function MCPDashboard() {
  // const { user } = useAuth(); // Unused
  const [stats, setStats] = useState<MCPStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const data = await mcpApi.getStats();
      setStats(data);
    } catch (err) {
      setError('Failed to load MCP stats');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-muted-foreground">Loading MCP System...</div>;
  }

  if (error) {
    return (
      <div className="p-8 text-center text-red-500">
        <p>{error}</p>
        <Button onClick={fetchStats} variant="outline" className="mt-4">Retry</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">MCP System</h1>
          <p className="text-muted-foreground">Model Context Protocol Management</p>
        </div>
        <div className="flex gap-2">
            <Link href="/admin/mcp/servers">
                <Button>
                    <Server className="w-4 h-4 mr-2" />
                    Manage Servers
                </Button>
            </Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Servers</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.active_servers || 0} / {stats?.total_servers || 0}</div>
            <p className="text-xs text-muted-foreground">
              Running instances
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resources</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_resources || 0}</div>
            <p className="text-xs text-muted-foreground">
              Exposed data points
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tools</CardTitle>
            <Settings className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_tools || 0}</div>
            <p className="text-xs text-muted-foreground">
              Callable functions
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Connections</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.active_connections || 0}</div>
            <p className="text-xs text-muted-foreground">
              Active client sessions
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-2">
        <Card>
            <CardHeader>
                <CardTitle>System Health</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-2">
                    <div className="flex justify-between items-center text-sm">
                        <span>Status</span>
                        <span className="text-green-500 font-medium">Operational</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                        <span>Protocol Version</span>
                        <span>1.0.0</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                        <span>Environment</span>
                        <span>{process.env.NODE_ENV}</span>
                    </div>
                </div>
            </CardContent>
        </Card>

        <Card>
            <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
                 <Link href="/admin/mcp/servers">
                    <Button variant="outline" className="w-full justify-start">
                        <Server className="mr-2 h-4 w-4" />
                        View Server Registry
                    </Button>
                </Link>
                <Button variant="outline" className="w-full justify-start" disabled>
                    <Terminal className="mr-2 h-4 w-4" />
                    Open MCP Console (Coming Soon)
                </Button>
            </CardContent>
        </Card>
      </div>
    </div>
  );
}
