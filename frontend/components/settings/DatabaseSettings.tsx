'use client';

import React, { useState, useEffect } from 'react';
import { 
  Database, Server, HardDrive, Network, Zap, 
  CheckCircle, XCircle, RefreshCw, Play, Square,
  Cloud, Laptop, Settings2, AlertCircle
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface ServiceStatus {
  healthy: boolean;
  url?: string;
  is_cloud: boolean;
  provider?: string;
  endpoint?: string;
}

interface StorageHealth {
  mode: string;
  services: {
    postgres: ServiceStatus;
    redis: ServiceStatus;
    neo4j: ServiceStatus;
    vector: ServiceStatus;
    object: ServiceStatus;
  };
}

const SERVICE_ICONS: Record<string, React.ElementType> = {
  postgres: Database,
  redis: Zap,
  neo4j: Network,
  vector: HardDrive,
  object: Server,
};

const SERVICE_LABELS: Record<string, string> = {
  postgres: 'PostgreSQL',
  redis: 'Redis',
  neo4j: 'Neo4j',
  vector: 'Vector DB',
  object: 'Object Storage',
};

export function DatabaseSettings() {
  const [health, setHealth] = useState<StorageHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [mode, setMode] = useState<'local' | 'cloud' | 'hybrid'>('local');
  const [activeTab, setActiveTab] = useState('status');

  const fetchHealth = async () => {
    try {
      const response = await fetch('/api/v1/storage/health');
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setHealth(data.data);
          setMode(data.data.mode as 'local' | 'cloud' | 'hybrid');
        }
      }
    } catch (error) {
      console.error('Failed to fetch storage health:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchHealth();
  };

  const handleTestConnection = async (service: string) => {
    setTesting(service);
    try {
      const response = await fetch(`/api/v1/storage/health/${service}`);
      if (response.ok) {
        await fetchHealth();
      }
    } catch (error) {
      console.error(`Failed to test ${service}:`, error);
    } finally {
      setTesting(null);
    }
  };

  const handleStartDatabases = async () => {
    try {
      await fetch('/api/v1/storage/databases/start', { method: 'POST' });
      setTimeout(fetchHealth, 2000);
    } catch (error) {
      console.error('Failed to start databases:', error);
    }
  };

  const handleStopDatabases = async () => {
    try {
      await fetch('/api/v1/storage/databases/stop', { method: 'POST' });
      setTimeout(fetchHealth, 1000);
    } catch (error) {
      console.error('Failed to stop databases:', error);
    }
  };

  const renderServiceCard = (serviceKey: string, status: ServiceStatus) => {
    const Icon = SERVICE_ICONS[serviceKey] || Database;
    const label = SERVICE_LABELS[serviceKey] || serviceKey;
    
    return (
      <Card key={serviceKey} className="relative overflow-hidden">
        <div className={`absolute top-0 left-0 w-1 h-full ${status.healthy ? 'bg-green-500' : 'bg-red-500'}`} />
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Icon className="h-5 w-5 text-muted-foreground" />
              <CardTitle className="text-base">{label}</CardTitle>
            </div>
            <Badge variant={status.healthy ? 'default' : 'destructive'}>
              {status.healthy ? (
                <><CheckCircle className="h-3 w-3 mr-1" /> Online</>
              ) : (
                <><XCircle className="h-3 w-3 mr-1" /> Offline</>
              )}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2 text-muted-foreground">
              {status.is_cloud ? (
                <><Cloud className="h-4 w-4" /> Cloud</>
              ) : (
                <><Laptop className="h-4 w-4" /> Local</>
              )}
            </div>
            {status.url && (
              <p className="text-xs text-muted-foreground truncate" title={status.url}>
                {status.url}
              </p>
            )}
            {status.provider && (
              <p className="text-xs text-muted-foreground">
                Provider: {status.provider}
              </p>
            )}
            <Button 
              size="sm" 
              variant="outline" 
              className="w-full mt-2"
              onClick={() => handleTestConnection(serviceKey)}
              disabled={testing === serviceKey}
            >
              {testing === serviceKey ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Settings2 className="h-4 w-4 mr-2" />
              )}
              Test Connection
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const healthyCount = health ? Object.values(health.services).filter(s => s.healthy).length : 0;
  const totalCount = health ? Object.keys(health.services).length : 5;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Database Connections</h2>
          <p className="text-muted-foreground">
            Manage local and cloud storage backends
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Status Overview */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-full ${healthyCount === totalCount ? 'bg-green-100 dark:bg-green-900' : 'bg-yellow-100 dark:bg-yellow-900'}`}>
                {healthyCount === totalCount ? (
                  <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-400" />
                ) : (
                  <AlertCircle className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
                )}
              </div>
              <div>
                <p className="font-medium">
                  {healthyCount}/{totalCount} Services Online
                </p>
                <p className="text-sm text-muted-foreground">
                  Mode: <Badge variant="secondary">{mode.toUpperCase()}</Badge>
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={handleStartDatabases}>
                <Play className="h-4 w-4 mr-2" />
                Start All
              </Button>
              <Button variant="outline" onClick={handleStopDatabases}>
                <Square className="h-4 w-4 mr-2" />
                Stop All
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Service Cards */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="status">Status</TabsTrigger>
          <TabsTrigger value="local">Local Config</TabsTrigger>
          <TabsTrigger value="cloud">Cloud Config</TabsTrigger>
        </TabsList>

        <TabsContent value="status" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {health && Object.entries(health.services).map(([key, status]) => 
              renderServiceCard(key, status)
            )}
          </div>
        </TabsContent>

        <TabsContent value="local" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Laptop className="h-5 w-5" />
                Local Database Configuration
              </CardTitle>
              <CardDescription>
                Configure portable databases for desktop mode
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>PostgreSQL Port</Label>
                  <Input type="number" defaultValue="54320" />
                </div>
                <div className="space-y-2">
                  <Label>Redis Port</Label>
                  <Input type="number" defaultValue="63790" />
                </div>
                <div className="space-y-2">
                  <Label>Neo4j Bolt Port</Label>
                  <Input type="number" defaultValue="7687" />
                </div>
                <div className="space-y-2">
                  <Label>ChromaDB Path</Label>
                  <Input defaultValue="./databases/chroma" />
                </div>
              </div>
              <div className="flex items-center space-x-2 pt-4">
                <Switch id="auto-start" />
                <Label htmlFor="auto-start">Auto-start databases on application launch</Label>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="cloud" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Cloud className="h-5 w-5" />
                Cloud Database Configuration
              </CardTitle>
              <CardDescription>
                Configure cloud-hosted database connections
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* PostgreSQL Cloud */}
              <div className="space-y-2">
                <Label>PostgreSQL Cloud URL</Label>
                <Input 
                  type="password" 
                  placeholder="postgresql://user:pass@host:5432/db" 
                />
              </div>

              {/* Redis Cloud */}
              <div className="space-y-2">
                <Label>Redis Cloud URL</Label>
                <Input 
                  type="password" 
                  placeholder="redis://user:pass@host:6379" 
                />
              </div>

              {/* Neo4j Aura */}
              <div className="space-y-2">
                <Label>Neo4j Aura Connection URI</Label>
                <Input 
                  type="password" 
                  placeholder="neo4j+s://xxxx.databases.neo4j.io" 
                />
              </div>

              {/* Pinecone */}
              <div className="space-y-2">
                <Label>Pinecone API Key</Label>
                <Input 
                  type="password" 
                  placeholder="Enter Pinecone API key" 
                />
              </div>

              {/* S3 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>S3 Endpoint URL</Label>
                  <Input placeholder="https://s3.amazonaws.com" />
                </div>
                <div className="space-y-2">
                  <Label>S3 Bucket</Label>
                  <Input placeholder="datalogic" />
                </div>
                <div className="space-y-2">
                  <Label>S3 Access Key</Label>
                  <Input type="password" placeholder="Access Key ID" />
                </div>
                <div className="space-y-2">
                  <Label>S3 Secret Key</Label>
                  <Input type="password" placeholder="Secret Access Key" />
                </div>
              </div>

              <Button className="w-full">Save Cloud Configuration</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default DatabaseSettings;
