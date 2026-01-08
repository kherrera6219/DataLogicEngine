'use client';

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const pillars = [
  { id: 1, name: "Technology", description: "Hardware, Software, AI, Networking", status: "active", count: 12450 },
  { id: 2, name: "Healthcare", description: "Medical, Pharma, Biotech, Wellness", status: "active", count: 8320 },
  { id: 3, name: "Finance", description: "Markets, Banking, Crypto, Insurance", status: "active", count: 15600 },
  { id: 4, name: "Education", description: "Pedagogy, Institutions, Curricula", status: "active", count: 6200 },
  { id: 5, name: "Government", description: "Policy, Regulation, Law, Utilities", status: "active", count: 9100 },
  { id: 6, name: "Identity", description: "Personas, Psychology, Sociology", status: "maintenance", count: 4500 },
];

export default function KnowledgePage() {
  return (
    <main className="min-h-screen bg-gray-50/50 dark:bg-gray-950 p-8">
      <div className="container mx-auto max-w-7xl">
        <header className="mb-10">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Knowledge Base</h1>
          <p className="text-gray-500 max-w-3xl">
            The Universal Knowledge Graph is organized into primary pillars. 
            Each pillar contains thousands of interconnected nodes, validated by the Truth Engine.
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {pillars.map((pillar) => (
            <Card key={pillar.id} className="hover:shadow-md transition-shadow cursor-pointer border-l-4 border-l-blue-500">
              <CardHeader>
                <div className="flex justify-between items-start">
                   <CardTitle className="text-xl">{pillar.name}</CardTitle>
                   <Badge variant={pillar.status === 'active' ? 'success' : 'secondary'}>
                      {pillar.status}
                   </Badge>
                </div>
                <CardDescription>{pillar.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex justify-between items-end mt-4">
                  <div>
                    <div className="text-3xl font-bold text-gray-900 dark:text-white">
                      {pillar.count.toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-500 uppercase font-medium mt-1">Nodes</div>
                  </div>
                  <div className="w-12 h-12 bg-blue-50 dark:bg-gray-800 rounded-full flex items-center justify-center text-blue-600">
                     <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </main>
  );
}
