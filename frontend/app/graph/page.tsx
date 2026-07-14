'use client';

import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import type { ForceGraphMethods } from 'react-force-graph-3d';
import dynamic from 'next/dynamic';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { ApiErrorBoundary } from "@/components/ui/api-error-boundary";
import {
  Shield, Info, Search, Filter, ChevronRight, RotateCcw, Zap, ChevronLeft, ZoomIn, ZoomOut, Maximize2, Download
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

function displayMetadata(node: GraphNode): Array<[string, string]> {
  const metadata = { ...(node.attributes || {}), ...(node.details || {}) };
  return Object.entries(metadata)
    .filter(([, value]) => ['string', 'number', 'boolean'].includes(typeof value) || value === null)
    .map(([key, value]): [string, string] => [key, value === null ? 'Not recorded' : String(value)])
    .sort(([left], [right]) => left.localeCompare(right));
}

function GraphPageContent() {
  const searchParams = useSearchParams();
  const graphRef = useRef<ForceGraphMethods>();
  const viewportRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[], links: GraphEdge[], source_revision?: string, last_loaded_at?: string | null }>({ nodes: [], links: [] });
  const [activeAxis, setActiveAxis] = useState(1);
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(true);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(false);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [searchQuery, setSearchQuery] = useState(() => searchParams.get('search') || '');
  const [selectedPillar, setSelectedPillar] = useState<string | null>(null);
  const [graphStatus, setGraphStatus] = useState<'loading' | 'connected' | 'unavailable'>('loading');
  const [showAllMetadata, setShowAllMetadata] = useState(false);
  const [expanding, setExpanding] = useState(false);

  const [showLabels, setShowLabels] = useState(true);
  const [enablePhysics, setEnablePhysics] = useState(true);

  useEffect(() => {
    async function fetchGraphData() {
      try {
        setGraphStatus('loading');
        const graph = await api.knowledge.graph(activeAxis);
        setGraphData(graph);
        setGraphStatus('connected');
        toast("Knowledge Graph synchronized.", "success", 3000);
      } catch (err) {
        console.error("Failed to fetch graph data:", err);
        setGraphStatus('unavailable');
        toast("Failed to load production graph data.", "error", 3000);
      }
    }
    fetchGraphData();
  }, [activeAxis, toast]);

  const availablePillars = useMemo(
    () => Array.from(new Set(graphData.nodes.map((node) => node.pillar).filter((pillar): pillar is string => Boolean(pillar)))).sort(),
    [graphData.nodes]
  );

  const visibleGraphData = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();
    const nodes = graphData.nodes.filter((node) => {
      const matchesSearch = !normalizedQuery || [node.id, node.name, node.label, node.node_type, node.pillar]
        .some((value) => value?.toLowerCase().includes(normalizedQuery));
      return matchesSearch && (!selectedPillar || node.pillar === selectedPillar);
    });
    const nodeIds = new Set(nodes.map((node) => node.id));
    return {
      nodes,
      links: graphData.links.filter((link) => nodeIds.has(String(link.source)) && nodeIds.has(String(link.target))),
    };
  }, [graphData, searchQuery, selectedPillar]);

  const handleNodeClick = useCallback((node: ForceGraphNodeObject) => {
    setSelectedNode(node);
    setShowAllMetadata(false);
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

  const exportSelectedNode = useCallback(() => {
    if (!selectedNode) return;
    const body = JSON.stringify(selectedNode, null, 2);
    const url = URL.createObjectURL(new Blob([body], { type: 'application/json' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = `knowledge-node-${selectedNode.id.replace(/[^a-zA-Z0-9_-]/g, '_')}.json`;
    link.click();
    URL.revokeObjectURL(url);
    toast('Node metadata bundle exported.', 'success', 2000);
  }, [selectedNode, toast]);

  const expandSelectedNode = useCallback(async () => {
    if (!selectedNode) return;
    setExpanding(true);
    try {
      const expanded = await api.knowledge.graph(undefined, { root: selectedNode.id, depth: 1 });
      setGraphData((current) => {
        const nodes = new Map(current.nodes.map((node) => [node.id, node]));
        expanded.nodes.forEach((node) => nodes.set(node.id, node));
        const links = new Map(
          current.links.map((link) => [`${String(link.source)}:${String(link.target)}:${link.edge_type || ''}`, link]),
        );
        expanded.links.forEach((link) => links.set(`${String(link.source)}:${String(link.target)}:${link.edge_type || ''}`, link));
        return {
          nodes: Array.from(nodes.values()),
          links: Array.from(links.values()),
          source_revision: expanded.source_revision || current.source_revision,
          last_loaded_at: expanded.last_loaded_at || current.last_loaded_at,
        };
      });
      toast('One-hop graph neighborhood added to the view.', 'success', 2000);
    } catch {
      toast('The selected node neighborhood could not be loaded.', 'error', 2500);
    } finally {
      setExpanding(false);
    }
  }, [selectedNode, toast]);

  const selectedMetadata = useMemo(
    () => selectedNode ? displayMetadata(selectedNode) : [],
    [selectedNode],
  );
  const complianceState = selectedNode?.attributes?.compliance_status
    ?? selectedNode?.attributes?.compliance_result
    ?? selectedNode?.attributes?.validation_state;

  const zoomCamera = useCallback((factor: number) => {
    const camera = graphRef.current?.camera();
    if (!camera) return;
    graphRef.current?.cameraPosition({
      x: camera.position.x * factor,
      y: camera.position.y * factor,
      z: camera.position.z * factor,
    }, { x: 0, y: 0, z: 0 }, 250);
  }, []);

  const toggleFullscreen = useCallback(async () => {
    if (!viewportRef.current) return;
    if (document.fullscreenElement) {
      await document.exitFullscreen();
    } else {
      await viewportRef.current.requestFullscreen();
    }
  }, []);

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
           {graphStatus !== 'connected' && (
             <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/70" role="status">
               <p className={cn("text-sm font-medium", graphStatus === 'unavailable' ? "text-red-300" : "text-amber-300")}>
                 {graphStatus === 'unavailable' ? 'Graph service unavailable.' : 'Loading graph revision…'}
               </p>
             </div>
           )}
           {graphStatus === 'connected' && graphData.nodes.length === 0 && (
             <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/70" role="status">
               <p className="text-sm font-medium text-gray-300">This axis has no graph nodes in the current revision.</p>
             </div>
           )}
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
                    {availablePillars.map((name, index) => {
                      const color = PILLAR_COLORS[name] || Object.values(PILLAR_COLORS)[index % Object.keys(PILLAR_COLORS).length];
                      const active = selectedPillar === name;
                      return <button
                        key={name}
                        type="button"
                        className={cn("flex items-center justify-between p-2 rounded-lg hover:bg-white/5 cursor-pointer group", active && "bg-white/10")}
                        aria-pressed={active}
                        aria-label={`Filter by ${name} pillar`}
                        onClick={() => setSelectedPillar(active ? null : name)}
                      >
                         <div className="flex items-center gap-3">
                           <div
                             className="w-2.5 h-2.5 rounded-full ring-1 ring-white/20 shadow-[0_0_8px_var(--pillar-color)]"
                             style={{ backgroundColor: color, '--pillar-color': color } as CSSWithCustomProps}
                             aria-hidden="true"
                           />
                           <span className="text-sm font-medium">{name}</span>
                         </div>
                        <Badge variant="outline" className={cn("transition-opacity text-[10px] px-1 h-4", active ? "opacity-100" : "opacity-0 group-hover:opacity-100")}>{active ? 'Active' : 'Filter'}</Badge>
                      </button>;
                    })}
                    {availablePillars.length === 0 && (
                      <p className="text-xs text-gray-500">No pillar metadata is available for this axis.</p>
                    )}
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
          ref={viewportRef}
          className="flex-1 relative bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-gray-900 to-black"
          role="application"
          aria-label="3D Knowledge Graph Visualization"
        >
           <ForceGraph3D
             ref={graphRef}
             graphData={visibleGraphData}
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
              <Button variant="ghost" size="icon" className="h-10 w-10 text-gray-400 hover:text-white rounded-xl" aria-label="Zoom in" onClick={() => zoomCamera(0.8)}><ZoomIn className="h-5 w-5" /></Button>
              <Button variant="ghost" size="icon" className="h-10 w-10 text-gray-400 hover:text-white rounded-xl" aria-label="Zoom out" onClick={() => zoomCamera(1.25)}><ZoomOut className="h-5 w-5" /></Button>
              <Button variant="ghost" size="icon" className="h-10 w-10 text-gray-400 hover:text-white rounded-xl" aria-label="Toggle fullscreen" onClick={() => void toggleFullscreen()}><Maximize2 className="h-5 w-5" /></Button>
           </div>

           <div className="absolute top-6 right-6 p-4 glass-morphism rounded-2xl max-w-[200px] hidden lg:block">
              <div className="flex items-center gap-2 mb-3">
                 <Zap className="h-4 w-4 text-amber-500" />
                 <span className="text-[10px] font-bold uppercase tracking-widest text-amber-500">Live Status</span>
              </div>
              <div className="space-y-1">
                 <p className="text-[11px] text-gray-400">Active Axis: <span className="text-white font-bold">{activeAxis}</span></p>
                 <p className="text-[11px] text-gray-400">Nodes Visualized: <span className="text-white font-bold">{visibleGraphData.nodes.length}</span></p>
                 <p className="text-[11px] text-gray-400">Graph Status: <span className={cn("font-bold", graphStatus === 'connected' ? "text-emerald-500" : graphStatus === 'unavailable' ? "text-red-400" : "text-amber-400")}>{graphStatus === 'connected' ? 'Connected' : graphStatus === 'unavailable' ? 'Unavailable' : 'Loading'}</span></p>
                 <p className="truncate text-[11px] text-gray-400" title={graphData.source_revision}>Revision: <span className="font-mono text-white">{graphData.source_revision ? graphData.source_revision.slice(0, 18) + '…' : 'Not recorded'}</span></p>
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
                      {(showAllMetadata ? selectedMetadata : selectedMetadata.slice(0, 6)).map(([k, v]) => (
                        <div key={k} className="p-3 bg-white/5 rounded-xl border border-white/5" role="listitem">
                          <p className="text-[9px] text-gray-500 font-bold uppercase mb-1">{k}</p>
                          <p className="text-xs text-blue-100 font-medium">{v}</p>
                        </div>
                      ))}
                      {selectedMetadata.length === 0 && (
                        <p className="col-span-2 text-xs text-gray-500">No additional metadata was returned for this node.</p>
                      )}
                   </div>
  
                   <div className="p-4 bg-blue-500/5 border border-blue-500/20 rounded-2xl" role="status">
                      <div className="flex items-center gap-2 mb-2">
                         <Shield className="h-3 w-3 text-blue-400" aria-hidden="true" />
                         <span className="text-[10px] font-bold text-blue-400 uppercase tracking-widest">Recorded validation state</span>
                      </div>
                      <p className="text-[11px] text-gray-400">
                        {complianceState === undefined || complianceState === null || complianceState === ''
                          ? 'No compliance or validation result was returned for this node.'
                          : String(complianceState)}
                      </p>
                   </div>
                </div>
  
                <div className="mt-auto space-y-2 pt-6">
                   <Button
                     variant="outline"
                     className="w-full h-10 rounded-xl"
                     aria-label="Expand one-hop graph neighborhood for this node"
                     onClick={() => void expandSelectedNode()}
                     disabled={expanding}
                   >
                     {expanding ? 'Expanding…' : 'Expand Neighbors'}
                   </Button>
                   <Button
                     className="w-full bg-blue-600 hover:bg-blue-700 h-10 rounded-xl"
                     aria-label="Toggle all recorded metadata for this node"
                     onClick={() => setShowAllMetadata((current) => !current)}
                     disabled={selectedMetadata.length <= 6}
                   >
                     {showAllMetadata ? 'Show Summary' : 'View All Metadata'}
                   </Button>
                   <Button 
                      variant="ghost" className="w-full text-xs text-gray-500 h-10 rounded-xl"
                      onClick={exportSelectedNode}
                      aria-label="Export node metadata as JSON"
                    >
                     <Download className="mr-2 h-3 w-3" aria-hidden="true" /> Export Node Bundle (JSON)
                   </Button>
                   {typeof selectedNode.attributes?.last_retrieval_trace_id === 'string' && selectedNode.attributes.last_retrieval_trace_id && (
                     <Button asChild variant="ghost" className="w-full text-xs h-10 rounded-xl">
                       <Link href={`/runs/view?id=${encodeURIComponent(selectedNode.attributes.last_retrieval_trace_id)}`}>
                         View Last Answer Trace
                       </Link>
                     </Button>
                   )}
                   {typeof selectedNode.attributes?.ingestion_id === 'string' && selectedNode.attributes.ingestion_id && (
                     <Button asChild variant="ghost" className="w-full text-xs h-10 rounded-xl">
                       <Link href="/settings?tab=knowledge">View Source Ingestion</Link>
                     </Button>
                   )}
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-600 px-10 text-center">
                 <div className="flex flex-col items-center gap-4">
                    <Info className="h-10 w-10 opacity-20" aria-hidden="true" />
                    <p className="text-sm font-medium">Select a node to inspect its recorded metadata and validation state.</p>
                 </div>
              </div>
            )}
          </aside>
        </ApiErrorBoundary>
      </div>
    </div>
  );
}

export default function GraphPage() {
  return (
    <Suspense fallback={<div className="flex h-full items-center justify-center bg-black text-sm text-gray-300">Loading graph controls…</div>}>
      <GraphPageContent />
    </Suspense>
  );
}
