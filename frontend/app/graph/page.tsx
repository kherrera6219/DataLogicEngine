'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Maximize2, RotateCcw, ZoomIn, ZoomOut } from "lucide-react";

// Dynamic import to avoid SSR issues with Three.js
const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full text-gray-400">
      Loading 3D Engine...
    </div>
  )
});

interface GraphNode {
  id: string;
  name: string;
  pillar?: string;
  group?: number;
  val?: number;
}

interface GraphLink {
  source: string;
  target: string;
  type?: string;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

// Generate demo graph data for visualization
function generateDemoData(): GraphData {
  const pillars = ['Technology', 'Healthcare', 'Finance', 'Identity', 'Regulatory'];
  const nodes: GraphNode[] = [];
  const links: GraphLink[] = [];
  
  // Generate nodes for each pillar
  pillars.forEach((pillar, pillarIdx) => {
    const nodeCount = 15 + Math.floor(Math.random() * 10);
    for (let i = 0; i < nodeCount; i++) {
      const nodeId = `${pillar.toLowerCase()}-${i}`;
      nodes.push({
        id: nodeId,
        name: `${pillar} Node ${i + 1}`,
        pillar: pillar,
        group: pillarIdx,
        val: 1 + Math.random() * 3
      });
      
      // Create links within pillar
      if (i > 0) {
        const sourceIdx = Math.floor(Math.random() * i);
        links.push({
          source: `${pillar.toLowerCase()}-${sourceIdx}`,
          target: nodeId,
          type: 'Part-Of'
        });
      }
    }
  });
  
  // Create cross-pillar links
  for (let i = 0; i < 20; i++) {
    const sourcePillar = pillars[Math.floor(Math.random() * pillars.length)];
    const targetPillar = pillars[Math.floor(Math.random() * pillars.length)];
    if (sourcePillar !== targetPillar) {
      const sourceIdx = Math.floor(Math.random() * 15);
      const targetIdx = Math.floor(Math.random() * 15);
      links.push({
        source: `${sourcePillar.toLowerCase()}-${sourceIdx}`,
        target: `${targetPillar.toLowerCase()}-${targetIdx}`,
        type: 'Crosswalk'
      });
    }
  }
  
  return { nodes, links };
}

// Color palette for pillars
const PILLAR_COLORS: Record<string, string> = {
  'Technology': '#3b82f6',
  'Healthcare': '#10b981',
  'Finance': '#f59e0b',
  'Identity': '#8b5cf6',
  'Regulatory': '#ef4444'
};

export default function GraphPage() {
  const graphRef = useRef<unknown>(null);
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [showLabels, setShowLabels] = useState(true);
  const [enable3D, setEnable3D] = useState(true);
  const [enablePhysics, setEnablePhysics] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPillar, setSelectedPillar] = useState<string | null>(null);
  
  // Load demo data on mount
  useEffect(() => {
    setGraphData(generateDemoData());
  }, []);
  
  // Filter nodes based on search and selected pillar
  const filteredData = useCallback(() => {
    let nodes = graphData.nodes;
    let links = graphData.links;
    
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      nodes = nodes.filter(n => 
        n.name.toLowerCase().includes(query) || 
        n.id.toLowerCase().includes(query)
      );
      const nodeIds = new Set(nodes.map(n => n.id));
      links = links.filter(l => 
        nodeIds.has(l.source as string) && nodeIds.has(l.target as string)
      );
    }
    
    if (selectedPillar) {
      nodes = nodes.filter(n => n.pillar === selectedPillar);
      const nodeIds = new Set(nodes.map(n => n.id));
      links = links.filter(l => 
        nodeIds.has(l.source as string) && nodeIds.has(l.target as string)
      );
    }
    
    return { nodes, links };
  }, [graphData, searchQuery, selectedPillar]);
  
  const handleNodeClick = useCallback((node: GraphNode) => {
    // Focus on clicked node
    const graph = graphRef.current as { cameraPosition?: (coords: object, lookAt: object, ms: number) => void };
    if (graph?.cameraPosition) {
      const distance = 100;
      const distRatio = 1 + distance / Math.hypot(0, 0, 0);
      graph.cameraPosition(
        { x: 0 * distRatio, y: 0 * distRatio, z: distance },
        node as unknown as object,
        1000
      );
    }
  }, []);
  
  const resetCamera = useCallback(() => {
    const graph = graphRef.current as { cameraPosition?: (coords: object, lookAt: object, ms: number) => void };
    if (graph?.cameraPosition) {
      graph.cameraPosition({ x: 0, y: 0, z: 300 }, { x: 0, y: 0, z: 0 }, 1000);
    }
  }, []);
  
  const displayData = filteredData();
  
  return (
    <main className="h-screen bg-gray-950 flex flex-col md:flex-row overflow-hidden">
       {/* Sidebar Controls */}
       <aside className="w-full md:w-80 bg-gray-900 border-r border-gray-800 p-4 flex flex-col gap-6 overflow-y-auto">
          <div>
             <h1 className="text-lg font-bold text-white mb-1">Graph Explorer</h1>
             <p className="text-xs text-gray-400">Interactive 3D Knowledge Graph Visualization</p>
          </div>

          <div className="space-y-4">
             <div className="space-y-2">
                <label className="text-xs font-semibold text-gray-500 uppercase">Search</label>
                <Input 
                  placeholder="Find node by ID or Label..." 
                  className="bg-gray-800 border-gray-700 text-white placeholder-gray-500"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
             </div>

             <div className="space-y-2">
                <label className="text-xs font-semibold text-gray-500 uppercase">Pillar Filter</label>
                <div className="flex flex-wrap gap-2">
                   {Object.entries(PILLAR_COLORS).map(([pillar, color]) => (
                     <Badge 
                       key={pillar}
                       variant="outline" 
                       className={`cursor-pointer transition-all ${selectedPillar === pillar ? 'ring-2 ring-white' : ''}`}
                       style={{ 
                         borderColor: color, 
                         color: selectedPillar === pillar ? 'white' : color,
                         backgroundColor: selectedPillar === pillar ? color : 'transparent'
                       }}
                       onClick={() => setSelectedPillar(selectedPillar === pillar ? null : pillar)}
                     >
                       {pillar}
                     </Badge>
                   ))}
                </div>
             </div>

             <div className="space-y-4 border-t border-gray-800 pt-4">
                 <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-300">Physics Simulation</span>
                    <Switch checked={enablePhysics} onCheckedChange={setEnablePhysics} />
                 </div>
                 <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-300">Show Labels</span>
                    <Switch checked={showLabels} onCheckedChange={setShowLabels} />
                 </div>
                 <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-300">3D Mode</span>
                    <Switch checked={enable3D} onCheckedChange={setEnable3D} />
                 </div>
             </div>
             
             <div className="space-y-2">
               <label className="text-xs font-semibold text-gray-500 uppercase">Camera Controls</label>
               <div className="flex gap-2">
                 <Button variant="outline" size="sm" onClick={resetCamera} className="flex-1">
                   <RotateCcw className="h-4 w-4 mr-1" /> Reset
                 </Button>
                 <Button variant="outline" size="sm" className="flex-1">
                   <Maximize2 className="h-4 w-4 mr-1" /> Fit
                 </Button>
               </div>
             </div>
          </div>

          <div className="mt-auto space-y-2">
             <div className="text-xs text-gray-500 p-2 bg-gray-800/50 rounded">
               <p>Nodes: <span className="text-white">{displayData.nodes.length}</span></p>
               <p>Edges: <span className="text-white">{displayData.links.length}</span></p>
             </div>
             <Button className="w-full">Export View</Button>
          </div>
       </aside>

       {/* Main Visualization Area */}
       <div className="flex-1 relative bg-black">
          {enable3D && (
            <ForceGraph3D
              ref={graphRef}
              graphData={displayData}
              nodeLabel={showLabels ? 'name' : undefined}
              nodeColor={(node: GraphNode) => PILLAR_COLORS[node.pillar || 'Technology'] || '#666'}
              nodeVal={(node: GraphNode) => node.val || 1}
              linkColor={() => 'rgba(255,255,255,0.2)'}
              linkWidth={0.5}
              backgroundColor="#000011"
              onNodeClick={handleNodeClick}
              enableNodeDrag={enablePhysics}
              cooldownTicks={enablePhysics ? Infinity : 0}
              warmupTicks={100}
            />
          )}
          
          <div className="absolute top-4 left-4 p-2 bg-gray-900/80 rounded-lg text-xs text-mono text-green-400 border border-gray-800">
             FPS: 60 | Nodes: {displayData.nodes.length} | Edges: {displayData.links.length}
          </div>
          
          <div className="absolute bottom-4 right-4 flex gap-2">
            <Button variant="outline" size="sm" className="bg-gray-900/80">
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm" className="bg-gray-900/80">
              <ZoomOut className="h-4 w-4" />
            </Button>
          </div>
       </div>
    </main>
  );
}
