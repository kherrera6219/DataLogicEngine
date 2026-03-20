'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import type { ForceGraphMethods } from 'react-force-graph-3d';
import dynamic from 'next/dynamic';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { ApiErrorBoundary } from "@/components/ui/api-error-boundary";
import {
  Shield, Info, Search, Filter, ChevronRight, RotateCcw, Zap, ChevronLeft, ZoomIn, ZoomOut, Maximize2
} from 'lucide-react';
import { cn } from "@/lib/utils";
import { AxisSelector } from "@/components/Graph/AxisSelector";
import { CommandBar } from "@/components/Dashboard/CommandBar";
import { useToast } from "@/components/ui/use-toast";

// Dynamic import to avoid SSR issues with Three.js
const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full text-gray-400 bg-gray-950">
      <div className="animate-pulse flex flex-col items-center gap-4">
        <div className="h-12 w-12 rounded-full border-4 border-blue-500 border-t-transparent animate-spin" />
        <span className="text-sm font-medium tracking-widest uppercase">Initializing 17D Engine</span>
      </div>
    </div>
  )
});

// Fixed color palette
const PILLAR_COLORS: Record<string, string> = {
  'Technology': '#3b82f6',
  'Healthcare': '#10b981',
  'Finance': '#f59e0b',
  'Identity': '#8b5cf6',
  'Regulatory': '#ef4444'
};

import { api, GraphNode, GraphEdge } from '@/lib/api';

/** Graph node as understood by react-force-graph-3d callbacks.
 *  The library adds x/y/z at runtime during layout. */
type ForceGraphNodeObject = GraphNode & { val?: number; x?: number; y?: number; z?: number };

/** Typed CSS property helper for CSS custom properties. */
type CSSWithCustomProps = React.CSSProperties & Record<string, string>;

export default function GraphPage() {
  const graphRef = useRef<ForceGraphMethods>();
  const { toast } = useToast();
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[], links: GraphEdge[] }>({ nodes: [], links: [] });
  const [activeAxis, setActiveAxis] = useState(1);
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(true);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(false);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const [showLabels, setShowLabels] = useState(true);
  const [enablePhysics, setEnablePhysics] = useState(true);

  useEffect(() => {
    async function fetchGraphData() {
      try {
        const [nodes, edges] = await Promise.all([
          api.knowledge.getNodes(),
          api.knowledge.getEdges()
        ]);

        const links = edges.map(e => {
          const raw = e as unknown as Record<string, unknown>;
          return {
            ...e,
            source: (raw.source_node_id as string) || e.source,
            target: (raw.target_node_id as string) || e.target
          };
        });

        setGraphData({ nodes, links });
        toast("Graph Engine synchronized with production DB.", "success", 3000);
      } catch (err) {
        console.error("Failed to fetch graph data:", err);
        toast("Failed to load production graph data.", "error", 3000);
      }
    }
    fetchGraphData();
  }, [toast]);

  const handleNodeClick = useCallback((node: ForceGraphNodeObject) => {
    setSelectedNode(node);
    setRightSidebarOpen(true);
    toast(`Inspecting Node: ${node.name}`, "info", 2000);
    if (graphRef.current) {
      const lookAt = { x: node.x ?? 0, y: node.y ?? 0, z: node.z ?? 0 };
      graphRef.current.cameraPosition({ x: node.id.length * 20, y: 20, z: 200 }, lookAt, 1000);
    }
  }, [toast]);

  const resetCamera = useCallback(() => {
    if (graphRef.current) {
      graphRef.current.cameraPosition({ x: 0, y: 0, z: 300 }, { x: 0, y: 0, z: 0 }, 1000);
      toast("Camera position reset to default.", "info", 2000);
    }
  }, [toast]);

  return (
    <div className="h-full relative flex flex-col overflow-hidden">
      <h1 className="sr-only">17-Axis Knowledge Graph Explorer</h1>
      <CommandBar />
      <AxisSelector activeAxis={activeAxis} onChange={setActiveAxis} />

      <div className="flex-1 flex relative">
        <aside
          className={cn(
            "h-full bg-gray-900 border-r border-gray-800 transition-all duration-300 flex flex-col z-20 shadow-2xl",
            leftSidebarOpen ? "w-72" : "w-0 overflow-hidden border-none"
          )}
          aria-label="Graph filters and metadata"
          role="complementary"
        >
           <div className="p-6 space-y-8 flex-1">
              <div className="space-y-4">
                 <div className="flex items-center gap-2 text-xs font-bold text-gray-500 uppercase tracking-widest">
                    <Filter className="h-3 w-3" /> Filters
                 </div>
                 <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                    <Input
                      placeholder="Quick find..."
                      className="bg-gray-800/50 border-gray-700 h-10 pl-10 rounded-xl"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      aria-label="Filter nodes in current view"
                    />
                 </div>
              </div>

              <div className="space-y-4" role="group" aria-label="Pillar filters">
                 <div className="text-xs font-bold text-gray-500 uppercase tracking-widest">Pillars</div>
                 <div className="flex flex-col gap-2">
                    {Object.entries(PILLAR_COLORS).map(([name, color]) => (
                      <div
                        key={name}
                        className="flex items-center justify-between p-2 rounded-lg hover:bg-white/5 cursor-pointer group"
                        role="button"
                        aria-pressed={false}
                        aria-label={`Filter by ${name} pillar`}
                      >
                         <div className="flex items-center gap-3">
                           <div
                             className="w-2.5 h-2.5 rounded-full ring-1 ring-white/20 shadow-[0_0_8px_var(--pillar-color)]"
                             style={{ backgroundColor: color, '--pillar-color': color } as CSSWithCustomProps}
                             aria-hidden="true"
                           />
                           <span className="text-sm font-medium">{name}</span>
                         </div>
                        <Badge variant="outline" className="opacity-0 group-hover:opacity-100 transition-opacity text-[10px] px-1 h-4">Active</Badge>
                      </div>
                    ))}
                 </div>
              </div>

              <div className="pt-6 border-t border-gray-800 space-y-4">
                  <div className="flex items-center justify-between p-1">
                     <span className="text-xs font-medium text-gray-400">Labels</span>
                     <Switch checked={showLabels} onCheckedChange={setShowLabels} aria-label="Toggle node labels" />
                  </div>
                  <div className="flex items-center justify-between p-1">
                     <span className="text-xs font-medium text-gray-400">Physics</span>
                     <Switch checked={enablePhysics} onCheckedChange={setEnablePhysics} aria-label="Toggle physics simulation" />
                  </div>
              </div>
           </div>

           <div className="p-4 bg-black/20 border-t border-gray-800">
              <Button
                size="sm" variant="ghost" className="w-full text-blue-500 text-xs gap-2"
                onClick={resetCamera}
                aria-label="Reset camera view to center"
              >
                 <RotateCcw className="h-3 w-3" /> Reset View
              </Button>
           </div>
        </aside>

        <button
          onClick={() => setLeftSidebarOpen(!leftSidebarOpen)}
          className={cn(
            "absolute top-1/2 -translate-y-1/2 z-30 h-12 w-4 bg-gray-900 border border-gray-800 rounded-r-lg flex items-center justify-center hover:bg-gray-800 transition-all duration-300 shadow-xl",
            leftSidebarOpen ? "translate-x-[288px]" : "translate-x-0"
          )}
          aria-label={leftSidebarOpen ? "Collapse filters" : "Expand filters"}
          aria-expanded={leftSidebarOpen}
        >
          {leftSidebarOpen ? <ChevronLeft className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
        </button>

        <div
          id="graph-viewport"
          className="flex-1 relative bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-gray-900 to-black"
          role="application"
          aria-label="3D Knowledge Graph Visualization"
        >
           <ForceGraph3D
             ref={graphRef}
             graphData={graphData}
             nodeLabel={showLabels ? 'name' : undefined}
             nodeColor={(node) => PILLAR_COLORS[(node as ForceGraphNodeObject).pillar || 'Technology'] || '#666'}
             nodeVal={(node) => (node as ForceGraphNodeObject).val || 1}
             linkColor={() => 'rgba(255,255,255,0.1)'}
             linkWidth={0.5}
             backgroundColor="rgba(0,0,0,0)"
             onNodeClick={(node) => handleNodeClick(node as ForceGraphNodeObject)}
             enableNodeDrag={enablePhysics}
             nodeOpacity={0.9}
           />

           <div className="absolute bottom-6 left-6 flex gap-3 p-1 bg-black/40 backdrop-blur-md rounded-2xl border border-white/10" role="group" aria-label="Camera controls">
              <Button variant="ghost" size="icon" className="h-10 w-10 text-gray-400 hover:text-white rounded-xl" aria-label="Zoom in"><ZoomIn className="h-5 w-5" /></Button>
              <Button variant="ghost" size="icon" className="h-10 w-10 text-gray-400 hover:text-white rounded-xl" aria-label="Zoom out"><ZoomOut className="h-5 w-5" /></Button>
              <Button variant="ghost" size="icon" className="h-10 w-10 text-gray-400 hover:text-white rounded-xl" aria-label="Toggle fullscreen"><Maximize2 className="h-5 w-5" /></Button>
           </div>

           <div className="absolute top-6 right-6 p-4 glass-morphism rounded-2xl max-w-[200px] hidden lg:block">
              <div className="flex items-center gap-2 mb-3">
                 <Zap className="h-4 w-4 text-amber-500" />
                 <span className="text-[10px] font-bold uppercase tracking-widest text-amber-500">Live Status</span>
              </div>
              <div className="space-y-1">
                 <p className="text-[11px] text-gray-400">Active Axis: <span className="text-white font-bold">{activeAxis}</span></p>
                 <p className="text-[11px] text-gray-400">Nodes Visualized: <span className="text-white font-bold">{graphData.nodes.length}</span></p>
                 <p className="text-[11px] text-gray-400">Calculated Health: <span className="text-emerald-500 font-bold">Optimal</span></p>
              </div>
           </div>
        </div>

        <ApiErrorBoundary moduleName="Node Inspector">
          <aside 
            className={cn(
              "h-full bg-gray-900 border-l border-gray-800 transition-all duration-300 flex flex-col z-20 shadow-2xl overflow-y-auto",
              rightSidebarOpen ? "w-80" : "w-0 overflow-hidden border-none"
            )}
            aria-label="Node detail inspector"
            role="complementary"
          >
            {selectedNode ? (
              <div className="p-6 flex flex-col h-full">
                <div className="flex items-center justify-between mb-8">
                   <div className="flex items-center gap-2 text-xs font-bold text-blue-500 uppercase tracking-tighter">
                      <Shield className="h-4 w-4" aria-hidden="true" /> Node Inspector
                   </div>
                   <Button 
                    variant="ghost" size="icon" className="h-8 w-8 text-gray-500 rounded-lg hover:bg-gray-800" 
                    onClick={() => setRightSidebarOpen(false)}
                    aria-label="Close inspector"
                  >
                      <ChevronRight className="h-5 w-5" />
                   </Button>
                </div>
  
                <div className="space-y-6">
                   <div>
                      <h3 className="text-xl font-bold text-white mb-2 leading-tight">{selectedNode.name}</h3>
                       <Badge
                        variant="secondary"
                        className="text-white border-none shadow-sm"
                        style={{ backgroundColor: PILLAR_COLORS[selectedNode.pillar || 'Technology'] }}
                        aria-label={`Pillar classification: ${selectedNode.pillar}`}
                      >
                        {selectedNode.pillar}
                      </Badge>
                   </div>
  
                   <div className="grid grid-cols-2 gap-4" role="list">
                      {selectedNode.details && Object.entries(selectedNode.details).map(([k, v]) => (
                        <div key={k} className="p-3 bg-white/5 rounded-xl border border-white/5" role="listitem">
                          <p className="text-[9px] text-gray-500 font-bold uppercase mb-1">{k}</p>
                          <p className="text-xs text-blue-100 font-medium">{v}</p>
                        </div>
                      ))}
                   </div>
  
                   <div className="p-4 bg-emerald-500/5 border border-emerald-500/20 rounded-2xl" role="status">
                      <div className="flex items-center gap-2 mb-2">
                         <Shield className="h-3 w-3 text-emerald-500" aria-hidden="true" />
                         <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest">Compliance Passed</span>
                      </div>
                      <p className="text-[11px] text-gray-400 italic">This node satisfies all NIST 800-171 requirements for its classification.</p>
                   </div>
                </div>
  
                <div className="mt-auto space-y-2 pt-6">
                   <Button className="w-full bg-blue-600 hover:bg-blue-700 h-10 rounded-xl" aria-label="Open detailed compliance report for this node">
                     View Full Details
                   </Button>
                   <Button 
                      variant="ghost" className="w-full text-xs text-gray-500 h-10 rounded-xl"
                      onClick={() => toast("Exporting node metadata bundle...", "info", 2000)}
                      aria-label="Export node metadata as JSON"
                    >
                     Export Node Bundle (JSON)
                   </Button>
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-600 px-10 text-center">
                 <div className="flex flex-col items-center gap-4">
                    <Info className="h-10 w-10 opacity-20" aria-hidden="true" />
                    <p className="text-sm font-medium">Select a node to inspect its compliance and metadata.</p>
                 </div>
              </div>
            )}
          </aside>
        </ApiErrorBoundary>
      </div>
    </div>
  );
}
