'use client';

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

import { PageLayout } from "@/components/ui/page-layout";

export default function AdminPage() {
  return (
    <PageLayout
      title="System Administration"
      description="Platform-wide controls and user management."
      breadcrumbs={[{ label: "Admin Console" }]}
      actions={<Button variant="destructive">Emergency Shutdown</Button>}
    >

         <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
             <Card className="lg:col-span-3">
                 <CardHeader>
                    <CardTitle>User Management</CardTitle>
                 </CardHeader>
                 <CardContent>
                    <Table>
                       <TableHeader>
                          <TableRow>
                             <TableHead>User</TableHead>
                             <TableHead>Role</TableHead>
                             <TableHead>Status</TableHead>
                             <TableHead>Last Active</TableHead>
                             <TableHead className="text-right">Action</TableHead>
                          </TableRow>
                       </TableHeader>
                       <TableBody>
                          {[
                             { name: "John Doe", email: "john@ukg.io", role: "Admin", status: "Active", last: "Now" },
                             { name: "Alice Smith", email: "alice@ukg.io", role: "Editor", status: "Active", last: "2h ago" },
                             { name: "Bob Jones", email: "bob@ukg.io", role: "Viewer", status: "Inactive", last: "5d ago" },
                          ].map((user) => (
                             <TableRow key={user.email}>
                                <TableCell>
                                   <div className="font-medium">{user.name}</div>
                                   <div className="text-xs text-gray-500">{user.email}</div>
                                </TableCell>
                                <TableCell>{user.role}</TableCell>
                                <TableCell><Badge variant="outline">{user.status}</Badge></TableCell>
                                <TableCell>{user.last}</TableCell>
                                <TableCell className="text-right">
                                   <Button size="sm" variant="ghost">Edit</Button>
                                </TableCell>
                             </TableRow>
                          ))}
                       </TableBody>
                    </Table>
                 </CardContent>
             </Card>

             <Card className="lg:col-span-1">
                 <CardHeader>
                    <CardTitle>Quick Actions</CardTitle>
                 </CardHeader>
                 <CardContent className="space-y-4">
                    <Button variant="outline" className="w-full justify-start">
                       Flush Redis Cache
                    </Button>
                    <Button variant="outline" className="w-full justify-start">
                       Rotate API Keys
                    </Button>
                    <Button variant="outline" className="w-full justify-start">
                       Backup Database
                    </Button>
                    <Button variant="outline" className="w-full justify-start" onClick={() => window.location.href = '/admin/compliance'}>
                       Compliance & Audit Logs
                    </Button>
                    <Button variant="outline" className="w-full justify-start" onClick={() => window.location.href = '/admin/mcp'}>
                       MCP System & Tools
                    </Button>
                 </CardContent>
             </Card>
         </div>
    </PageLayout>
  );
}
