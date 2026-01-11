'use client';

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";

export default function GraphPage() {
  return (
    <main className="h-screen bg-gray-950 flex flex-col md:flex-row overflow-hidden">
       {/* Sidebar Controls */}
       <aside className="w-full md:w-80 bg-gray-900 border-r border-gray-800 p-4 flex flex-col gap-6 overflow-y-auto">
          <div>
             <h1 className="text-lg font-bold text-white mb-1">Graph Explorer</h1>
             <p className="text-xs text-gray-400">Visualization Constraints & Filters</p>
          </div>

          <div className="space-y-4">
             <div className="space-y-2">
                <label className="text-xs font-semibold text-gray-500 uppercase">Search</label>
                <Input placeholder="Find node by ID or Label..." className="bg-gray-800 border-gray-700 text-white placeholder-gray-500" />
             </div>

             <div className="space-y-2">
                <label className="text-xs font-semibold text-gray-500 uppercase">Pillar Filter</label>
                <Select className="bg-gray-800 border-gray-700 text-white">
                   <option>All Pillars</option>
                   <option>Technology</option>
                   <option>Healthcare</option>
                   <option>Finance</option>
                   <option>Identity</option>
                </Select>
             </div>

             <div className="space-y-2">
                <label className="text-xs font-semibold text-gray-500 uppercase">Relationship Type</label>
                <div className="flex flex-wrap gap-2">
                   <Badge variant="outline" className="cursor-pointer hover:bg-blue-900 hover:text-white">Is-A</Badge>
                   <Badge variant="outline" className="cursor-pointer hover:bg-blue-900 hover:text-white">Part-Of</Badge>
                   <Badge variant="outline" className="cursor-pointer hover:bg-blue-900 hover:text-white">Causal</Badge>
                   <Badge variant="outline" className="cursor-pointer hover:bg-blue-900 hover:text-white">Temporal</Badge>
                </div>
             </div>

             <div className="space-y-4 border-t border-gray-800 pt-4">
                 <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-300">Physics Simulation</span>
                    <Switch checked={true} />
                 </div>
                 <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-300">Show Labels</span>
                    <Switch checked={true} />
                 </div>
                 <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-300">3D Mode</span>
                    <Switch checked={true} />
                 </div>
             </div>
          </div>

          <div className="mt-auto">
             <Button className="w-full">Export View</Button>
          </div>
       </aside>

       {/* Main Visualization Area */}
       <div className="flex-1 relative bg-black">
          {/* Simulated Graph Canvas */}
          <div className="absolute inset-0 flex items-center justify-center opacity-30 pointer-events-none">
             {/* Abstract Grid visual placeholder */}
             <div className="w-[600px] h-[600px] border border-blue-900 rounded-full flex items-center justify-center">
                 <div className="w-[400px] h-[400px] border border-blue-800 rounded-full flex items-center justify-center">
                    <div className="w-[200px] h-[200px] border border-blue-700 rounded-full"></div>
                 </div>
             </div>
          </div>
          
          <div className="absolute top-4 left-4 p-2 bg-gray-900/80 rounded-lg text-xs text-mono text-green-400 border border-gray-800">
             FPS: 60 | Nodes: 12,405 | Edges: 48,920
          </div>

          {/* Prompt to connect real WebGL */}
          <div className="absolute bottom-8 left-1/2 -translate-x-1/2 bg-gray-900/90 p-4 rounded-xl border border-gray-800 text-center max-w-md">
             <h3 className="text-white font-medium mb-1">Visualization Engine Ready</h3>
             <p className="text-sm text-gray-400">
                The control surface is implemented. 
                <br/>Connect <span className="text-blue-400 font-mono">three.js</span> or <span className="text-blue-400 font-mono">react-force-graph</span> here to render the live dataset.
             </p>
          </div>
       </div>
    </main>
  );
}
