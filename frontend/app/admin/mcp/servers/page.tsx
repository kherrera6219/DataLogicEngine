'use client';

import { useState, useEffect } from 'react';
import { mcp, MCPServer } from '@/lib/api/mcp';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from '@/components/ui/dialog';
import { Trash2, Plus, RefreshCw, Box } from 'lucide-react';
import Link from 'next/link';
import { useToast } from '@/components/ui/use-toast';

export default function MCPServersPage() {
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { toast } = useToast();
  // Add Server dialog state
  const [addOpen, setAddOpen] = useState(false);
  const [addName, setAddName] = useState('');
  const [addVersion, setAddVersion] = useState('1.0.0');
  const [addDescription, setAddDescription] = useState('');
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    fetchServers();
  }, []);

  const fetchServers = async () => {
    try {
      setLoading(true);
      const data = await mcp.getServers();
      setServers(data.servers);
    } catch (err) {
      setError('Failed to load servers');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this server?')) return;
    try {
      await mcp.deleteServer(id);
      toast('Server deleted successfully.', 'success');
      fetchServers();
    } catch (err) {
      console.error(err);
      toast('Failed to delete server. Please try again.', 'error');
    }
  };

  const handleAddServer = async () => {
    if (!addName.trim()) {
      toast('Server name is required.', 'error');
      return;
    }
    setAdding(true);
    try {
      await mcp.createServer({ name: addName.trim(), version: addVersion.trim() || '1.0.0', description: addDescription.trim() });
      toast('Server registered successfully.', 'success');
      setAddOpen(false);
      setAddName('');
      setAddVersion('1.0.0');
      setAddDescription('');
      fetchServers();
    } catch (err) {
      console.error(err);
      toast('Failed to register server. Please try again.', 'error');
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
           <div className="flex items-center gap-2 mb-2">
                <Link href="/admin/mcp" className="text-muted-foreground hover:text-primary">
                    MCP
                </Link>
                <span className="text-muted-foreground">/</span>
                <span className="font-semibold">Servers</span>
           </div>
          <h1 className="text-3xl font-bold tracking-tight">Server Registry</h1>
          <p className="text-muted-foreground">Manage registered Model Context Protocol servers.</p>
        </div>
        <div className="flex gap-2">
            <Button variant="outline" onClick={fetchServers}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
            </Button>
            <Button onClick={() => setAddOpen(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Add Server
            </Button>
        </div>
      </div>

      {error && <div className="text-red-500 p-4 border border-red-200 rounded-md bg-red-50">{error}</div>}

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Version</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Capabilities</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                        Loading servers...
                    </TableCell>
                </TableRow>
              ) : servers.length === 0 ? (
                <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                        No servers found.
                    </TableCell>
                </TableRow>
              ) : (
                servers.map((server) => (
                  <TableRow key={server.server_id}>
                    <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                            <Box className="w-4 h-4 text-blue-500" />
                            <div>
                                <div>{server.name}</div>
                                <div className="text-xs text-muted-foreground">{server.description}</div>
                            </div>
                        </div>
                    </TableCell>
                    <TableCell>{server.version}</TableCell>
                    <TableCell>
                        <Badge variant={server.status === 'active' ? 'default' : 'destructive'} className="uppercase text-[10px]">
                            {server.status}
                        </Badge>
                    </TableCell>
                    <TableCell>
                        <div className="flex gap-1">
                            {server.capabilities?.resources && <Badge variant="outline" className="text-[10px]">Resources</Badge>}
                            {server.capabilities?.tools && <Badge variant="outline" className="text-[10px]">Tools</Badge>}
                            {server.capabilities?.prompts && <Badge variant="outline" className="text-[10px]">Prompts</Badge>}
                        </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button size="icon" variant="ghost" className="text-red-500 hover:text-red-700 hover:bg-red-50" onClick={() => handleDelete(server.server_id!)}>
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Add Server Dialog */}
      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Register MCP Server</DialogTitle>
            <DialogDescription>Add a new Model Context Protocol server to the registry.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="add-name">Server Name <span className="text-red-500">*</span></Label>
              <Input
                id="add-name"
                value={addName}
                onChange={(e) => setAddName(e.target.value)}
                placeholder="my-knowledge-server"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="add-version">Version</Label>
              <Input
                id="add-version"
                value={addVersion}
                onChange={(e) => setAddVersion(e.target.value)}
                placeholder="1.0.0"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="add-desc">Description</Label>
              <Input
                id="add-desc"
                value={addDescription}
                onChange={(e) => setAddDescription(e.target.value)}
                placeholder="Optional description"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddOpen(false)} disabled={adding}>Cancel</Button>
            <Button onClick={handleAddServer} disabled={adding}>
              {adding ? <><RefreshCw className="w-4 h-4 mr-2 animate-spin" />Registering...</> : 'Register Server'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
